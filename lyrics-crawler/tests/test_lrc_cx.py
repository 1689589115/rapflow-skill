"""LrcCXSource 模块测试。"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from crawler.sources.lrc_cx import LrcCXSource


class TestLrcCXSource:
    """LrcCXSource 单元测试。"""

    @pytest.mark.asyncio
    async def test_search_lyrics_success(self) -> None:
        """测试成功获取歌词。"""
        source = LrcCXSource(MagicMock())
        lrc_text = "[00:00.00]这是一段歌词\n[00:05.00]第二段歌词\n[00:10.00]第三段歌词"

        with patch.object(source._client, 'fetch', new=AsyncMock(return_value=lrc_text)):
            result = await source.search_lyrics("Test Artist", "Test Song")

        assert result is not None
        assert result["artist"] == "Test Artist"
        assert result["song"] == "Test Song"
        assert result["source"] == "lrc_cx"
        assert result["confidence"] == 0.9
        assert "[00:00.00]这是一段歌词" in result["lyrics"]
        assert "[00:05.00]第二段歌词" in result["lyrics"]

    @pytest.mark.asyncio
    async def test_search_lyrics_fetch_fails(self) -> None:
        """测试请求失败时返回 None。"""
        source = LrcCXSource(MagicMock())

        with patch.object(source._client, 'fetch', new=AsyncMock(return_value=None)):
            result = await source.search_lyrics("Test Artist", "Test Song")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_lyrics_empty_response(self) -> None:
        """测试空响应时返回 None。"""
        source = LrcCXSource(MagicMock())

        with patch.object(source._client, 'fetch', new=AsyncMock(return_value="")):
            result = await source.search_lyrics("Test Artist", "Test Song")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_lyrics_whitespace_only(self) -> None:
        """测试空白响应时返回 None。"""
        source = LrcCXSource(MagicMock())

        with patch.object(source._client, 'fetch', new=AsyncMock(return_value="   \n\n  ")):
            result = await source.search_lyrics("Test Artist", "Test Song")

        assert result is None

    def test_get_album_tracks_returns_empty(self) -> None:
        """测试专辑曲目查询返回空列表。"""
        source = LrcCXSource(MagicMock())

        result = asyncio.run(source.get_album_tracks("Artist", "Album"))

        assert result == []

    def test_name_property(self) -> None:
        """测试 NAME 属性。"""
        assert LrcCXSource.NAME == "lrc_cx"

    def test_confidence_is_point_nine(self) -> None:
        """测试置信度为 0.9。"""
        source = LrcCXSource(MagicMock())
        lrc_text = "[00:00.00]Test lyric"

        with patch.object(source._client, 'fetch', new=AsyncMock(return_value=lrc_text)):
            result = asyncio.run(source.search_lyrics("Artist", "Song"))

        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_search_lyrics_trims_whitespace(self) -> None:
        """测试歌词文本会被 strip。"""
        source = LrcCXSource(MagicMock())
        lrc_text = "  \n  [00:00.00]Test lyric  \n  "

        with patch.object(source._client, 'fetch', new=AsyncMock(return_value=lrc_text)):
            result = await source.search_lyrics("Test Artist", "Test Song")

        assert result is not None
        assert result["lyrics"] == "[00:00.00]Test lyric"

    @pytest.mark.asyncio
    async def test_search_lyrics_uses_direct_connection(self) -> None:
        """测试优先使用直连（代理不可用时）。"""
        source = LrcCXSource(MagicMock())
        lrc_text = "[00:00.00]Test"

        fetch_mock = AsyncMock(return_value=lrc_text)
        with patch.object(source._client, 'fetch', fetch_mock):
            result = await source.search_lyrics("Artist", "Song")

        # 首次调用应该是直连（proxy=None）
        fetch_mock.assert_called_once()
        call_kwargs = fetch_mock.call_args
        assert call_kwargs[1].get('proxy') is None
        assert result is not None
        assert result['source'] == 'lrc_cx'
        assert result['confidence'] == 0.9

    @pytest.mark.asyncio
    async def test_search_lyrics_fallback_to_proxy(self) -> None:
        """测试直连失败时回退到代理。"""
        source = LrcCXSource(MagicMock())
        lrc_text = "[00:00.00]Test via proxy"

        # 直连返回 None，代理返回歌词
        fetch_mock = AsyncMock(side_effect=[None, lrc_text])
        with patch.object(source._client, 'fetch', fetch_mock):
            result = await source.search_lyrics("Artist", "Song")

        # 验证调用了两次：直连失败后回退代理
        assert fetch_mock.call_count == 2
        first_call = fetch_mock.call_args_list[0]
        second_call = fetch_mock.call_args_list[1]
        assert first_call[1].get('proxy') is None  # 第一次直连
        assert second_call[1].get('proxy') == "http://127.0.0.1:7897"  # 第二次走代理
        assert result is not None
        assert result['source'] == 'lrc_cx'
