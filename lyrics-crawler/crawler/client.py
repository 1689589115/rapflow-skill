"""HTTP 客户端封装 — 基于 httpx.AsyncClient。

提供带 UA 轮换、Accept-Language 和超时控制的异步请求能力，
所有网络调用失败时返回 None 而非抛出异常。
"""

from __future__ import annotations

import logging
import random
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# 常见浏览器 User-Agent 池，每次请求随机选取一项
UA_POOL: list[str] = [
    # Chrome / Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome / macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Firefox / Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) "
    "Gecko/20100101 Firefox/133.0",
    # Safari / macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6; rv:131.0) "
    "Gecko/20100101 Firefox/131.0",
    # Edge / Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

# 统一超时：15 秒
_TIMEOUT = httpx.Timeout(connect=15.0, read=15.0, write=15.0, pool=15.0)


class CrawlerClient:
    """异步 HTTP 客户端，封装 UA 轮换和错误处理。"""

    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = httpx.Timeout(connect=timeout, read=timeout, write=timeout, pool=timeout)
        # 进程内共享一个 client 实例，避免每次请求重建连接池
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """懒加载 client 实例。"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                http2=False,  # 目标站点对 HTTP/2 支持不稳定，回退到 HTTP/1.1
            )
        return self._client

    async def close(self) -> None:
        """关闭底层连接池。"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "CrawlerClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def fetch(
        self,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        proxy: Optional[str] = None,
    ) -> Optional[str]:
        """发起 GET 请求，返回响应文本；失败时返回 None。

        参数：
            url: 请求 URL
            headers: 可选的请求头
            proxy: 可选的代理 URL，如 "http://127.0.0.1:7897"

        每次请求随机选取一个 User-Agent，并附加 Accept-Language。
        """
        # 如果指定了代理，创建带代理的 client
        if proxy:
            client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                proxy=proxy,
                http2=False,
            )
            try:
                return await self._do_fetch(client, url, headers)
            finally:
                await client.aclose()
        else:
            client = await self._get_client()
            return await self._do_fetch(client, url, headers)

    async def _do_fetch(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: Optional[dict[str, str]],
    ) -> Optional[str]:
        """执行实际的 HTTP 请求。"""
        # 构造请求头：随机 UA + 中文语言偏好
        req_headers = {
            "User-Agent": random.choice(UA_POOL),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        if headers:
            req_headers.update(headers)

        try:
            resp = await client.get(url, headers=req_headers)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPStatusError as exc:
            # 429 等状态码记录下来，调用方可决定是否重试
            logger.warning("HTTP %d for %s", exc.response.status_code, url)
            return None
        except (httpx.HTTPError, OSError, TimeoutError) as exc:
            logger.warning("Request failed for %s: %r", url, exc)
            return None

    async def fetch_json(
        self,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        proxy: Optional[str] = None,
    ) -> Optional[dict]:
        """发起 GET 请求，返回解析后的 JSON 对象；失败时返回 None。

        参数：
            url: 请求 URL
            headers: 可选的请求头
            proxy: 可选的代理 URL，如 "http://127.0.0.1:7897"
        """
        # 如果指定了代理，创建带代理的 client
        if proxy:
            client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                proxy=proxy,
                http2=False,
            )
            try:
                return await self._do_fetch_json(client, url, headers)
            finally:
                await client.aclose()
        else:
            client = await self._get_client()
            return await self._do_fetch_json(client, url, headers)

    async def _do_fetch_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: Optional[dict[str, str]],
    ) -> Optional[dict]:
        """执行实际的 JSON 请求。"""
        req_headers = {
            "User-Agent": random.choice(UA_POOL),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        if headers:
            req_headers.update(headers)

        try:
            resp = await client.get(url, headers=req_headers)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPStatusError, httpx.HTTPError, OSError, TimeoutError, ValueError) as exc:
            logger.warning("JSON fetch failed for %s: %r", url, exc)
            return None
