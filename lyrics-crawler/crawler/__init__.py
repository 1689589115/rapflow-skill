"""中文说唱歌词爬虫引擎 — 主入口模块。

提供从多个网络源搜索歌词、清洗歌词、存入本地 SQLite 语料库的能力，
并对外暴露 async 和 CLI 两种调用方式。

可用歌词源：
- LrcCXSource: lrc.cx API（主力源，置信度 0.9）
- GeniusSource: Genius.com（已废弃，需要 access_token）
- NeteaseSource: 网易云音乐（已废弃，AES 加密未跑通）
- MusicaziSource: Musicazi.com（已废弃，网络不可达）
- ManualLyricSource: 手动导入本地歌词文件
- GoogleSearchFallbackSource: Google 搜索 Musixmatch/Musicazi 兜底
"""

from __future__ import annotations

from crawler.client import CrawlerClient
from crawler.sources.base import LyricsSource
from crawler.sources.genius import GeniusSource
from crawler.sources.netease import NeteaseSource
from crawler.sources.musicazi import MusicaziSource
from crawler.sources.lrc_cx import LrcCXSource
from crawler.sources.manual_source import ManualLyricSource
from crawler.sources.search_fallback import GoogleSearchFallbackSource
from crawler.extractor import LyricsExtractor
from crawler.cleaner import clean_lyrics, split_sections
from crawler.database import LyricsDB

__all__ = [
    "CrawlerClient",
    "LyricsSource",
    "GeniusSource",
    "NeteaseSource",
    "MusicaziSource",
    "LrcCXSource",
    "ManualLyricSource",
    "GoogleSearchFallbackSource",
    "LyricsExtractor",
    "clean_lyrics",
    "split_sections",
    "LyricsDB",
]

__version__ = "0.3.0"
