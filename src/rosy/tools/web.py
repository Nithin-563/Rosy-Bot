"""Web and file/document tools with bounded, SSRF-resistant fetching."""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx

from rosy.tools.base import BaseTool, ToolSpec


class WebFetchTool(BaseTool):
    spec = ToolSpec(
        name="web_fetch",
        description="Fetch and extract the main text of a public web page (markdown-like).",
        parameters={
            "url": {"type": "string", "description": "Absolute http(s) URL."},
            "max_chars": {"type": "integer", "description": "Max characters to return."},
        },
        timeout_seconds=20.0,
    )

    def __init__(self, http: httpx.AsyncClient) -> None:
        self.http = http

    async def execute(self, url: str = "", max_chars: int = 6000, **kwargs) -> str:
        if self.http is None:
            raise ValueError("Web access is not configured.")
        max_chars = max(1, min(int(max_chars), 50_000))
        current = _validate_public_url(url)
        for _ in range(5):
            try:
                resp = await self.http.get(current, follow_redirects=False)
            except httpx.TimeoutException as exc:
                raise ValueError("The web request timed out.") from exc
            except httpx.HTTPError as exc:
                raise ValueError("Could not fetch that page.") from exc
            if resp.status_code in {301, 302, 303, 307, 308}:
                location = resp.headers.get("location")
                if not location:
                    raise ValueError("The page returned an invalid redirect.")
                current = _validate_public_url(urljoin(current, location))
                continue
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ValueError(f"The page returned HTTP {resp.status_code}.") from exc
            text = _html_to_text(resp.text)
            return text[:max_chars]
        raise ValueError("Too many redirects.")


class ExtractTextTool(BaseTool):
    """Extract readable text from an uploaded file (text/plain-like data)."""

    spec = ToolSpec(
        name="extract_text",
        description="Extract readable text from a document (txt/md/csv/pdf).",
        parameters={
            "filename": {"type": "string", "description": "Name of the uploaded file."},
            "max_chars": {"type": "integer", "description": "Max characters to return."},
        },
        timeout_seconds=20.0,
    )

    def __init__(self, file_provider=None) -> None:
        self.files = file_provider

    async def execute(self, filename: str = "", max_chars: int = 8000, **kwargs) -> str:
        if self.files is None:
            raise ValueError("File access not configured.")
        if not filename or len(filename) > 255:
            raise ValueError("Invalid filename.")
        max_chars = max(1, min(int(max_chars), 50_000))
        data = await self.files.read(filename)
        if data is None:
            raise ValueError("File not found.")
        if isinstance(data, bytes):
            try:
                return data.decode("utf-8", errors="replace")[:max_chars]
            except Exception as exc:
                raise ValueError("Binary file; text extraction is not supported for this type yet.") from exc
        return str(data)[:max_chars]


def _validate_public_url(url: str) -> str:
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("Invalid URL.")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public http(s) URLs are allowed.")
    if parsed.port and not 1 <= parsed.port <= 65535:
        raise ValueError("Invalid port.")
    host = parsed.hostname.rstrip(".")
    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            addresses = {ipaddress.ip_address(info[4][0]) for info in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)}
        except OSError as exc:
            raise ValueError("Could not resolve that host.") from exc
    for address in addresses:
        if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast or address.is_unspecified:
            raise ValueError("Requests to private or local network addresses are blocked.")
    return url


def _html_to_text(html: str) -> str:
    """Very lightweight HTML->text; strips tags and scripts."""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class WebTools:
    """Factory that registers the web/file tools into a registry."""

    @staticmethod
    def register(registry, *, settings=None, http=None, files=None) -> None:
        registry.register_class(WebFetchTool(http=http))
        registry.register_class(ExtractTextTool(file_provider=files))
