"""Safe public-web tools with SSRF protection and bounded responses."""
from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

from rosy.tools.base import BaseTool, ToolSpec


def _validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only absolute public http(s) URLs are allowed.")
    host = parsed.hostname.strip().lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise ValueError("Local/private hosts are not allowed.")
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
                raise ValueError("Private/internal addresses are not allowed.")
    except socket.gaierror as exc:
        raise ValueError("Host could not be resolved.") from exc
    return url


class WebSearchTool(BaseTool):
    spec = ToolSpec(
        name="web_search",
        description="Search the public web and return concise result titles, URLs and snippets.",
        parameters={
            "query": {"type": "string", "description": "Search query."},
            "max_results": {"type": "integer", "description": "1-8 results."},
        },
        timeout_seconds=15.0,
    )

    def __init__(self, http: httpx.AsyncClient) -> None:
        self.http = http

    async def execute(self, query: str = "", max_results: int = 5, **kwargs) -> str:
        query = query.strip()
        if not query or len(query) > 300:
            raise ValueError("Invalid search query.")
        max_results = max(1, min(int(max_results), 8))
        url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
        response = await self.http.get(url, follow_redirects=False, headers={"User-Agent": "Rosy/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results: list[str] = []
        for block in soup.select("div.result")[:max_results]:
            anchor = block.select_one("a.result__a")
            if anchor is None:
                continue
            title = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "").strip()
            snippet_node = block.select_one(".result__snippet")
            snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""
            if not title or not href:
                continue
            results.append(f"{len(results)+1}. {title}\n{href}\n{snippet[:500]}")
        if not results:
            return "No web results found."
        return "\n\n".join(results)


class WebFetchTool(BaseTool):
    spec = ToolSpec(
        name="web_fetch",
        description="Fetch readable text from a public web page. Never use for private/internal URLs.",
        parameters={
            "url": {"type": "string", "description": "Absolute public http(s) URL."},
            "max_chars": {"type": "integer", "description": "Maximum text length."},
        },
        timeout_seconds=20.0,
    )

    def __init__(self, http: httpx.AsyncClient) -> None:
        self.http = http

    async def execute(self, url: str = "", max_chars: int = 6000, **kwargs) -> str:
        _validate_public_url(url)
        max_chars = max(500, min(int(max_chars), 12000))
        response = await self.http.get(url, follow_redirects=False, headers={"User-Agent": "Rosy/1.0"})
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if content_type and not any(x in content_type.lower() for x in ("text/html", "text/plain", "application/xhtml+xml")):
            raise ValueError("That URL does not return a readable web page.")
        if len(response.content) > 4 * 1024 * 1024:
            raise ValueError("The web page is too large to read safely.")
        text = _html_to_text(response.text)
        return text[:max_chars]


class ExtractTextTool(BaseTool):
    """Extract readable text from an explicitly supplied file provider."""
    spec = ToolSpec(
        name="extract_text",
        description="Extract readable text from a permitted document provided by the application.",
        parameters={
            "filename": {"type": "string", "description": "Filename."},
            "max_chars": {"type": "integer", "description": "Maximum text length."},
        },
        required_permission="user_files",
        timeout_seconds=20.0,
    )

    def __init__(self, file_provider=None) -> None:
        self.files = file_provider

    async def execute(self, filename: str = "", max_chars: int = 8000, **kwargs) -> str:
        if self.files is None:
            raise ValueError("File access is not configured.")
        if not filename or len(filename) > 255 or ".." in filename or filename.startswith(("/", "\\")):
            raise ValueError("Invalid filename.")
        data = await self.files.read(filename)
        if data is None:
            raise ValueError("File not found.")
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")[: max(500, min(int(max_chars), 12000))]
        return str(data)[: max(500, min(int(max_chars), 12000))]


def _strip_html(value: str) -> str:
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    return _strip_html(text)


class WebTools:
    @staticmethod
    def register(registry, *, settings=None, http=None, files=None) -> None:
        if http is not None:
            registry.register_class(WebSearchTool(http=http))
            registry.register_class(WebFetchTool(http=http))
        if files is not None:
            registry.register_class(ExtractTextTool(file_provider=files))
