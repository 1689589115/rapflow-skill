"""LrcCX.com 歌词源适配器。

通过 lrc.cx API 搜索和获取歌词，返回 LRC 格式歌词文本。
- API 端点: https://api.lrc.cx/lyrics
- 搜索参数: ?artist={歌手名}&song={歌名}
- 返回格式: text/plain (LRC 歌词文本，带时间戳)
- 置信度: 0.9

注意：
- 所有 HTTP 请求必须走代理（127.0.0.1:7897）
- lrc.cx 返回的是带时间戳的 LRC 格式，cleaner.remove_timestamp() 会处理
- 中文歌词编码已经是 UTF-8，不需要额外转换
- 遇到错误或超时，返回 None 不要抛异常
"""

from __future__ import annotations

import logging
import urllib.parse
from typing import Optional

from crawler.client import CrawlerClient
from crawler.sources.base import LyricsSource

logger = logging.getLogger(__name__)

# LrcCX API 端点
_LRC_CX_API_URL = "https://api.lrc.cx/lyrics"

# 代理设置
_PROXY_URL = "http://127.0.0.1:7897"


class LrcCXSource(LyricsSource):
    """LrcCX.com 歌词源适配器。"""

    NAME = "lrc_cx"

    def __init__(self, client: CrawlerClient) -> None:
        self._client = client

    async def search_lyrics(self, artist: str, song: str) -> Optional[dict]:
        """在 LrcCX 上搜索歌词。

        参数：
            artist: 歌手名
            song: 歌名

        返回：
            歌词信息字典，包含 artist, song, lyrics, raw_lyrics, url, source, confidence
            如果没搜到或出错返回 None。
        """
        # 构造 API 请求参数
        params = {
            "artist": artist.strip(),
            "song": song.strip(),
        }

        # 编码参数
        query_string = urllib.parse.urlencode(params)
        url = f"{_LRC_CX_API_URL}?{query_string}"

        logger.info("LrcCXSource: searching for '%s - %s'", artist, song)

        # 尝试1：直连（大多数情况可行）
        lyrics_text = await self._client.fetch(url, proxy=None)
        if lyrics_text is not None and lyrics_text.strip():
            raw_lyrics = lyrics_text.strip()
            logger.info("LrcCXSource: found %d chars via direct connection", len(raw_lyrics))
            return self._build_result(artist, song, raw_lyrics)

        # 尝试2：代理（直连被墙时回退）
        lyrics_text = await self._client.fetch(url, proxy=_PROXY_URL)
        if lyrics_text is None:
            logger.warning("LrcCXSource: both direct and proxy requests failed for '%s %s'", artist, song)
            return None
        if not lyrics_text or not lyrics_text.strip():
            logger.info("LrcCXSource: no lyrics found for '%s %s'", artist, song)
            return None

        raw_lyrics = lyrics_text.strip()
        logger.info("LrcCXSource: found %d chars via proxy", len(raw_lyrics))
        return self._build_result(artist, song, raw_lyrics)

    @staticmethod
    def _build_result(artist: str, song: str, raw_lyrics: str) -> dict:
        """统一构建搜索结果字典。"""
        return {
            "artist": artist,
            "song": song,
            "lyrics": raw_lyrics,
            "raw_lyrics": raw_lyrics,
            "url": _LRC_CX_API_URL,
            "album": "",
            "release_date": "",
            "source": "lrc_cx",
            "confidence": 0.9,
        }

    async def get_album_tracks(self, artist: str, album: str) -> list[dict]:
        """LrcCX 不提供专辑曲目查询 API，返回空列表。"""
        return []
