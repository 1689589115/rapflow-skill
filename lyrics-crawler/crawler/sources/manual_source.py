"""手动歌词导入源。

供用户提供"我已有歌词文件，直接入库"的路径，不走网络请求。
适用于：
- 本地已有清洗好的歌词文本文件（.txt / .lrc）
- 从其他来源（如 PDF、网页截图 OCR）获取的歌词文本
- 手动整理的歌词数据

使用方式：
    source = ManualLyricSource()
    source.set_text("歌手名", "歌名", text_content)
    result = await source.search_lyrics("歌手名", "歌名")
"""

from __future__ import annotations

import logging
from typing import Optional

from crawler.client import CrawlerClient
from crawler.cleaner import clean_lyrics
from crawler.sources.base import LyricsSource

logger = logging.getLogger(__name__)


class ManualLyricSource(LyricsSource):
    """手动歌词导入源 — 从实例变量读取文本，不发起网络请求。"""

    NAME = "manual"

    def __init__(self, client: Optional[CrawlerClient] = None) -> None:
        """初始化。

        参数：
            client: 无需使用，保留参数以符合基类签名，可传 None
        """
        self._client = client
        # 待导入的歌词文本，由 set_text() 填充
        self._pending_text: str = ""
        self._pending_artist: str = ""
        self._pending_song: str = ""

    def set_text(self, artist: str, song: str, text: str) -> None:
        """设置待导入的歌词文本。

        参数：
            artist: 歌手名
            song: 歌名
            text: 歌词文本（可以是原始格式，会自动走清洗管道）
        """
        self._pending_artist = artist
        self._pending_song = song
        self._pending_text = text
        logger.info("ManualLyricSource: loaded %d chars for '%s - %s'", len(text), artist, song)

    async def search_lyrics(self, artist: str, song: str) -> Optional[dict]:
        """从 _pending_text 读取文本，清洗后返回结果。"""
        # 支持两种调用方式：
        # 1. 通过 set_text() 预设，再调用 search_lyrics(artist, song)
        # 2. 直接传入 artist/song 匹配预设值
        if self._pending_artist != artist or self._pending_song != song:
            # 未预设或参数不匹配，返回 None
            logger.info("ManualLyricSource: no text set for '%s - %s'", artist, song)
            return None

        if not self._pending_text.strip():
            logger.warning("ManualLyricSource: empty text for '%s - %s'", artist, song)
            return None

        raw_lyrics = self._pending_text
        clean_lyrics_text = clean_lyrics(raw_lyrics)

        logger.info(
            "ManualLyricSource: imported '%s - %s' (%d lines)",
            artist,
            song,
            len([l for l in clean_lyrics_text.splitlines() if l.strip()]),
        )

        return {
            "artist": artist,
            "song": song,
            "lyrics": clean_lyrics_text,
            "raw_lyrics": raw_lyrics,
            "url": "",
            "album": "",
            "release_date": "",
            "source": self.NAME,
            "confidence": 1.0,
        }

    async def get_album_tracks(self, artist: str, album: str) -> list[dict]:
        """手动源不支持专辑曲目查询。"""
        return []
