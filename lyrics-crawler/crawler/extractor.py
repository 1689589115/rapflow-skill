"""歌词提取器 —— 并发从多个源抓取歌词，选择最佳结果。
协调所有 LyricsSource 的实现，并发请求各源，返回置信度最高的歌词。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from crawler.client import CrawlerClient
from crawler.cleaner import clean_lyrics
from crawler.sources.base import LyricsSource

logger = logging.getLogger(__name__)


class LyricsExtractor:
    """歌词提取编排器，负责并发请求多个源并选择最佳结果。"""

    def __init__(self, *sources: LyricsSource) -> None:
        """初始化，传入所有已注册的歌词源实例。"""
        self._sources = sources

    async def crawl(
        self,
        artist: str,
        song: str,
        *,
        prefer_clean: bool = True,
    ) -> Optional[dict]:
        """并发从所有源搜索歌词，返回置信度最高的结果。
        参数：
            artist: 歌手名
            song: 歌名
            prefer_clean: 是否对原始歌词运行清洗管道
        返回：
            格式同 LyricsSource.search_lyrics 的返回值，
            若所有源均失败则返回 None。
        """
        tasks = [src.search_lyrics(artist, song) for src in self._sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 分离正常结果和异常
        candidates: list[tuple[float, dict]] = []
        for src, result in zip(self._sources, results):
            if isinstance(result, Exception):
                logger.warning("%s raised %r", src.NAME, result)
                continue
            if result is None:
                logger.info("%s: no results for '%s %s'", src.NAME, artist, song)
                continue
            candidates.append((result.get("confidence", 0.0), result))

        if not candidates:
            logger.warning("All sources failed for '%s %s'", artist, song)
            return None

        # 按置信度降序，取最高
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]

        # 可选：对返回的歌词运行清洗管道（部分源已返回清洗后歌词）
        if prefer_clean and best.get("lyrics"):
            best = {**best, "lyrics": clean_lyrics(best["lyrics"])}

        logger.info(
            "Selected %s (conf=%.2f) for '%s %s'",
            best.get("source"),
            best.get("confidence", 0),
            artist,
            song,
        )
        return best

    async def crawl_album(
        self, artist: str, album: str
    ) -> list[dict]:
        """并发从所有源获取专辑曲目列表。"""
        tasks = [src.get_album_tracks(artist, album) for src in self._sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        tracks: list[dict] = []
        for src, result in zip(self._sources, results):
            if isinstance(result, Exception):
                logger.warning("%s album tracks raised %r", src.NAME, result)
                continue
            if result:
                tracks.extend(result)
        return tracks
