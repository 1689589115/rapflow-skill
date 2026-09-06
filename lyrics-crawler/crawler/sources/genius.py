"""Genius.com 适配器 — ⚠️ 已废弃。

Genius 需要 access_token 才能使用 API，本项目未实现认证逻辑。
如需重新接入，请提供有效的 access_token 并更新此文件。
当前实现仅为空壳，所有查询返回 None。
"""

from __future__ import annotations

import logging
from typing import Optional

from crawler.client import CrawlerClient
from crawler.sources.base import LyricsSource

logger = logging.getLogger(__name__)


class GeniusSource(LyricsSource):
    """Genius.com 歌词源适配器 — ⚠️ 已废弃，所有请求返回 None。"""

    NAME = "genius"
    _DEPRECATED = True

    def __init__(self, client: CrawlerClient) -> None:
        logger.warning(
            "GeniusSource is deprecated and will always return None. "
            "Access token authentication is not implemented."
        )

    async def search_lyrics(self, artist: str, song: str) -> Optional[dict]:
        """废弃：始终返回 None。"""
        logger.info("GeniusSource: skipped (deprecated) for '%s %s'", artist, song)
        return None

    async def get_album_tracks(self, artist: str, album: str) -> list[dict]:
        """废弃：始终返回空列表。"""
        return []
