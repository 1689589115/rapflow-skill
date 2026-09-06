"""歌词源模块初始化。

导出所有可用的歌词数据源，方便其他模块统一导入。
"""

from __future__ import annotations

from crawler.sources.base import LyricsSource
from crawler.sources.genius import GeniusSource
from crawler.sources.netease import NeteaseSource
from crawler.sources.musicazi import MusicaziSource
from crawler.sources.lrc_cx import LrcCXSource
from crawler.sources.manual_source import ManualLyricSource
from crawler.sources.search_fallback import GoogleSearchFallbackSource
from crawler.sources.local_db import LocalDbSource

__all__ = [
    "LyricsSource",
    "GeniusSource",
    "NeteaseSource",
    "MusicaziSource",
    "LrcCXSource",
    "ManualLyricSource",
    "GoogleSearchFallbackSource",
    "LocalDbSource",
]
