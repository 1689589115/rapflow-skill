"""ManualLyricSource 模块测试。"""

from __future__ import annotations

import asyncio
import pytest

from crawler.sources.manual_source import ManualLyricSource


class TestManualLyricSource:
    """ManualLyricSource 单元测试。"""

    @pytest.mark.asyncio
    async def test_search_lyrics_with_text(self) -> None:
        """测试从预设文本搜索歌词。"""
        source = ManualLyricSource()
        source.set_text("Test Artist", "Test Song", "这是一句歌词\n第二句歌词")

        result = await source.search_lyrics("Test Artist", "Test Song")

        assert result is not None
        assert result["artist"] == "Test Artist"
        assert result["song"] == "Test Song"
        assert result["source"] == "manual"
        assert result["confidence"] == 1.0
        assert "这是一句歌词" in result["lyrics"]
        assert "第二句歌词" in result["lyrics"]

    @pytest.mark.asyncio
    async def test_search_lyrics_without_text(self) -> None:
        """测试未预设文本时返回 None。"""
        source = ManualLyricSource()

        result = await source.search_lyrics("Unknown", "Unknown")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_lyrics_mismatched_artist(self) -> None:
        """测试歌手名不匹配时返回 None。"""
        source = ManualLyricSource()
        source.set_text("Artist A", "Song A", "歌词内容")

        result = await source.search_lyrics("Artist B", "Song A")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_lyrics_empty_text(self) -> None:
        """测试空文本时返回 None。"""
        source = ManualLyricSource()
        source.set_text("Artist", "Song", "   ")

        result = await source.search_lyrics("Artist", "Song")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_album_tracks_returns_empty(self) -> None:
        """测试专辑曲目查询返回空列表。"""
        source = ManualLyricSource()

        result = await source.get_album_tracks("Artist", "Album")

        assert result == []

    def test_confidence_is_one(self) -> None:
        """测试置信度为 1.0。"""
        source = ManualLyricSource()
        source.set_text("Artist", "Song", "歌词")

        result = asyncio.run(source.search_lyrics("Artist", "Song"))
        assert result["confidence"] == 1.0
