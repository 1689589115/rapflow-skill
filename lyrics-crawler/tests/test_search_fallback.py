"""GoogleSearchFallbackSource 模块测试。"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from crawler.sources.search_fallback import GoogleSearchFallbackSource


class TestGoogleSearchFallbackSource:
    """GoogleSearchFallbackSource 单元测试。"""

    @pytest.mark.asyncio
    async def test_search_lyrics_fetch_fails(self) -> None:
        """测试搜索请求失败时返回 None。"""
        source = GoogleSearchFallbackSource(MagicMock())

        with patch.object(source._client, 'fetch', new=AsyncMock(return_value=None)):
            result = await source.search_lyrics("Artist", "Song")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_lyrics_captcha_detected(self) -> None:
        """测试检测到验证码页面时返回 None。"""
        source = GoogleSearchFallbackSource(MagicMock())

        captcha_html = """
        <html>
        <body>
            <h1>unusual traffic</h1>
            <p>Please complete the captcha</p>
        </body>
        </html>
        """
        with patch.object(source._client, 'fetch', new=AsyncMock(return_value=captcha_html)):
            result = await source.search_lyrics("Artist", "Song")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_lyrics_no_target_links(self) -> None:
        """测试未找到目标站点链接时返回 None。"""
        source = GoogleSearchFallbackSource(MagicMock())

        # 不包含任何 musixmatch 或 musicazi 链接的 HTML
        normal_html = """
        <html>
        <body>
            <a href="https://example.com/other">Example</a>
            <a href="https://genius.com/song">Genius</a>
        </body>
        </html>
        """
        with patch.object(source._client, 'fetch', new=AsyncMock(return_value=normal_html)):
            result = await source.search_lyrics("Artist", "Song")

        assert result is None

    def test_get_album_tracks_returns_empty(self) -> None:
        """测试专辑曲目查询返回空列表。"""
        source = GoogleSearchFallbackSource(MagicMock())

        result = asyncio.run(source.get_album_tracks("Artist", "Album"))

        assert result == []

    def test_name_property(self) -> None:
        """测试 NAME 属性。"""
        assert GoogleSearchFallbackSource.NAME == "google_fallback"

    def test_is_captcha_page(self) -> None:
        """测试验证码检测逻辑。"""
        source = GoogleSearchFallbackSource(MagicMock())

        # 测试各种验证码关键词
        captcha_cases = [
            "unusual traffic from this IP",
            "automated queries detected",
            "please complete the captcha",
            "verify you are not a robot",
            "请完成验证码",
            "无法显示验证码",
        ]
        for case in captcha_cases:
            assert source._is_captcha_page(case) is True

        # 测试正常页面
        normal_html = """
        <html>
        <body>
            <h1>歌词页面</h1>
            <p>这是一首好歌</p>
        </body>
        </html>
        """
        assert source._is_captcha_page(normal_html) is False

    def test_resolve_google_redirect(self) -> None:
        """测试 Google 重定向 URL 解析。"""
        source = GoogleSearchFallbackSource(MagicMock())

        # 测试 Google 重定向 URL
        google_url = "https://www.google.com/url?sa=t&url=https://musixmatch.com/lyrics/test&usg=ABC123"
        result = source._resolve_google_redirect(google_url)
        assert result == "https://musixmatch.com/lyrics/test"

        # 测试非 Google URL
        normal_url = "https://musixmatch.com/lyrics/test"
        result = source._resolve_google_redirect(normal_url)
        assert result == normal_url

    def test_extract_target_url_with_regex(self) -> None:
        """测试通过正则提取目标 URL。"""
        source = GoogleSearchFallbackSource(MagicMock())

        html = """
        <html>
        <body>
            <a href="https://www.musixmatch.com/lyrics/test-artist/test-song">
                Test Song Lyrics
            </a>
        </body>
        </html>
        """
        result = source._extract_target_url(html)
        assert result is not None
        assert "musixmatch.com" in result

    def test_extract_lyrics_basic(self) -> None:
        """测试歌词提取逻辑。"""
        source = GoogleSearchFallbackSource(MagicMock())

        html = """
        <html>
        <body>
            <div data-lyrics-container="true">
                <p>Lyric line one</p>
                <p>Lyric line two</p>
                <p>Lyric line three</p>
            </div>
        </body>
        </html>
        """
        result = source._extract_lyrics(html, "https://musixmatch.com/lyrics/test", "Artist", "Song")

        assert result is not None
        assert result["artist"] == "Artist"
        assert result["song"] == "Song"
        assert result["source"] == "google_fallback"
        assert result["confidence"] == 0.5
        assert "Lyric line one" in result["lyrics"]
        assert "Lyric line two" in result["lyrics"]
