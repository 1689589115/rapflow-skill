"""Google 搜索兜底源。

当 Genius 和 Musicazi 都找不到歌词时，通过 Google 搜索
site:musixmatch.com OR site:musicazi.com 查找歌词页面，
提取第一个符合条件的结果。

注意：
- Google 搜索结果页可能触发验证码（captcha），检测到后直接跳过
- 置信度较低（0.5），仅供兜底使用
- 依赖 httpx + beautifulsoup4 + lxml，不引入额外第三方库
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from typing import Optional

from bs4 import BeautifulSoup

from crawler.client import CrawlerClient
from crawler.sources.base import LyricsSource

logger = logging.getLogger(__name__)

# Google 搜索 URL
_GOOGLE_SEARCH_URL = "https://www.google.com/search"

# 目标站点正则（Musixmatch / Musicazi）
_TARGET_SITE_RE = re.compile(r"(?:musixmatch|musicazi)\.com", re.IGNORECASE)

# Google 验证码页面特征词
_CAPTCHA_KEYWORDS = [
    "unusual traffic",
    "automated queries",
    "captcha",
    "verify you are not a robot",
    "无法显示验证码",
    "请完成验证码",
]

# Google 搜索结果中链接匹配正则
_RESULT_LINK_RE = re.compile(r"https?://(?:www\.)?(?:musixmatch|musicazi)\.com/[^\s\"'>]+", re.IGNORECASE)


class GoogleSearchFallbackSource(LyricsSource):
    """Google 搜索兜底歌词源。

    通过 Google 搜索目标站点歌词页面，提取第一个匹配结果。
    """

    NAME = "google_fallback"

    def __init__(self, client: CrawlerClient) -> None:
        self._client = client

    async def search_lyrics(self, artist: str, song: str) -> Optional[dict]:
        """通过 Google 搜索 Musixmatch / Musicazi 歌词页面。"""
        query = urllib.parse.quote(f"{artist} {song} lyrics")
        # 限定搜索范围为目标站点
        site_query = urllib.parse.quote(f'site:musixmatch.com OR site:musicazi.com')
        url = f"{_GOOGLE_SEARCH_URL}?q={query}+{site_query}&hl=zh-CN"

        logger.info("GoogleSearchFallback: searching for '%s %s'", artist, song)

        html = await self._client.fetch(url)
        if html is None:
            logger.warning("GoogleSearchFallback: search request failed for '%s %s'", artist, song)
            return None

        # 检测验证码页面
        if self._is_captcha_page(html):
            logger.warning("GoogleSearchFallback: captcha detected, skipping")
            return None

        # 从搜索结果中提取第一个目标站点链接
        target_url = self._extract_target_url(html)
        if target_url is None:
            logger.info("GoogleSearchFallback: no target site links found for '%s %s'", artist, song)
            return None

        logger.info("GoogleSearchFallback: found target URL %s", target_url)

        # 获取目标页面
        target_html = await self._client.fetch(target_url)
        if target_html is None:
            logger.warning("GoogleSearchFallback: failed to fetch %s", target_url)
            return None

        # 检测目标页面是否是验证码
        if self._is_captcha_page(target_html):
            logger.warning("GoogleSearchFallback: captcha on target page %s", target_url)
            return None

        # 从目标页面提取歌词
        info = self._extract_lyrics(target_html, target_url, artist, song)
        if info is None:
            logger.warning("GoogleSearchFallback: could not extract lyrics from %s", target_url)
            return None

        return info

    async def get_album_tracks(self, artist: str, album: str) -> list[dict]:
        """Google 搜索源不支持专辑曲目查询。"""
        return []

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    def _is_captcha_page(self, html: str) -> bool:
        """检测 HTML 是否是验证码页面。"""
        lower_html = html.lower()
        return any(keyword in lower_html for keyword in _CAPTCHA_KEYWORDS)

    def _extract_target_url(self, html: str) -> Optional[str]:
        """从 Google 搜索结果页提取第一个目标站点链接。"""
        soup = BeautifulSoup(html, "lxml")

        # 方法 1: 通过正则匹配 href 中的目标站点链接
        matches = _RESULT_LINK_RE.findall(html)
        if matches:
            # 去重并保持顺序
            seen = set()
            for url in matches:
                clean_url = url.rstrip(")/]")
                if clean_url not in seen:
                    seen.add(clean_url)
                    return clean_url

        # 方法 2: 通过 BeautifulSoup 查找包含目标站点的 <a> 标签
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if _TARGET_SITE_RE.search(href):
                # Google 返回的链接可能是重定向 URL，需要解析
                clean_url = self._resolve_google_redirect(href)
                if clean_url:
                    return clean_url

        return None

    def _resolve_google_redirect(self, google_url: str) -> Optional[str]:
        """解析 Google 重定向 URL，提取最终目标地址。

        Google 返回的链接格式类似：
        https://www.google.com/url?sa=t&url=TARGET_URL&...
        """
        try:
            parsed = urllib.parse.urlparse(google_url)
            if parsed.hostname != "www.google.com":
                return google_url
            query_params = urllib.parse.parse_qs(parsed.query)
            urls = query_params.get("url", [])
            if urls:
                return urls[0]
        except Exception as exc:
            logger.debug("Failed to resolve Google redirect: %r", exc)
        return None

    def _extract_lyrics(
        self, html: str, page_url: str, artist: str, song: str
    ) -> Optional[dict]:
        """从目标站点页面提取歌词和元信息。"""
        soup = BeautifulSoup(html, "lxml")

        # 尝试多种选择器提取歌词
        raw_lyrics = ""

        # Musixmatch 常用选择器
        selectors = [
            'div[data-lyrics-container="true"]',
            '.lyrics-container',
            '.lyrics-content',
            'lyrics-snippet',
            '.Lyrics__Container',
            '[class*="lyrics"]',
            'pre',
        ]

        for selector in selectors:
            el = soup.select_one(selector)
            if el is not None:
                text = el.get_text(separator="\n", strip=True)
                if len(text) > 50:  # 过滤过短的内容
                    raw_lyrics = text
                    break

        if not raw_lyrics:
            # 兜底：提取所有段落文本
            paragraphs = soup.find_all("p")
            if paragraphs:
                raw_lyrics = "\n".join(p.get_text(strip=True) for p in paragraphs[:50])

        if not raw_lyrics or len(raw_lyrics) < 20:
            return None

        # 尝试从页面提取元信息
        album = ""
        release_date = ""

        # 从 meta 标签提取
        meta_album = soup.select_one('meta[property="music:song:album"]')
        if meta_album is not None:
            album = meta_album.get("content", "")

        meta_date = soup.select_one('meta[property="music:song:release_date"]')
        if meta_date is not None:
            release_date = meta_date.get("content", "")

        return {
            "artist": artist,
            "song": song,
            "lyrics": raw_lyrics,
            "raw_lyrics": raw_lyrics,
            "url": page_url,
            "album": album,
            "release_date": release_date,
            "source": self.NAME,
            "confidence": 0.5,
        }
