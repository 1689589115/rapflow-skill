"""Musicazi.com 适配器 — ⚠️ 已废弃。

Musicazi 网站在当前网络环境下无法访问（DNS 解析失败）。
如需重新接入，请确保网络环境正常后实现此适配器。
当前实现仅为空壳，所有查询返回 None。
"""

from __future__ import annotations

import logging
from typing import Optional

from crawler.client import CrawlerClient
from crawler.sources.base import LyricsSource

logger = logging.getLogger(__name__)


class MusicaziSource(LyricsSource):
    """Musicazi.com 歌词源适配器 — ⚠️ 已废弃，所有请求返回 None。"""

    NAME = "musicazi"
    _DEPRECATED = True

    def __init__(self, client: CrawlerClient) -> None:
        logger.warning(
            "MusicaziSource is deprecated and will always return None. "
            "The website is unreachable in the current network environment."
        )

    async def search_lyrics(self, artist: str, song: str) -> Optional[dict]:
        """废弃：始终返回 None。"""
        logger.info("MusicaziSource: skipped (deprecated) for '%s %s'", artist, song)
        return None

    async def get_album_tracks(self, artist: str, album: str) -> list[dict]:
        """废弃：始终返回空列表。"""
        return []
