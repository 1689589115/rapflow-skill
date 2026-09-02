"""歌词源抽象基类。

所有具体源适配器（Genius、网易云等）均需继承此类并实现：
- search_lyrics：根据歌手+歌名搜索歌词
- get_album_tracks：获取专辑曲目列表（可选，默认返回空列表）
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class LyricsSource(ABC):
    """歌词数据源的抽象基类。"""

    # 源的显示名称，用于日志和输出
    NAME: str = "base"

    @abstractmethod
    async def search_lyrics(
        self, artist: str, song: str
    ) -> Optional[dict]:
        """根据歌手名和歌名搜索歌词。

        返回字典，结构如下：
        {
            "artist": str,          # 歌手名
            "song": str,            # 歌名
            "lyrics": str,          # 清洗后的歌词全文
            "raw_lyrics": str,      # 原始歌词（清洗前）
            "url": str,             # 来源页面 URL
            "album": str,           # 专辑名（可选）
            "release_date": str,    # 发行日期（可选）
            "source": str,          # 来源名称
            "confidence": float,    # 0~1 的置信度
        }
        如果没搜到或出错返回 None。
        """
        ...

    @abstractmethod
    async def get_album_tracks(
        self, artist: str, album: str
    ) -> list[dict]:
        """获取某张专辑的所有曲目列表。

        每项复用 search_lyrics 返回的 dict 格式，但只包含 meta 信息，
        不含全文歌词（lyrics 和 raw_lyrics 可为空字符串）。
        """
        ...
