"""Web and file/document tools (safe, network-bounded)."""

from __future__ import annotations

import re

import httpx

from rosy.config import Settings
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
        if not re.match(r"^https?://", url):
            raise ValueError("Only http(s) URLs are allowed.")
        try:
            resp = await self.http.get(url, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ValueError(f"Could not fetch page: {exc}") from exc
        text = _html_to_text(resp.text)
        return text[:max_chars]


class ExtractTextTool(BaseTool):
    """Extract readable text from an uploaded file (text/pdf/plain)."""

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
        data = await self.files.read(filename)
        if data is None:
            raise ValueError("File not found.")
        if isinstance(data, bytes):
            # only plain-text-like content is decoded here.
            try:
                return data.decode("utf-8", errors="replace")[:max_chars]
            except Exception:
                raise ValueError("Binary file; text extraction not supported for this type yet.") from None
        return str(data)[:max_chars]


def _html_to_text(html: str) -> str:
    """Very lightweight HTML->text; strips tags and scripts."""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class WebTools:
    """Factory that registers the web/file tools into a registry."""

    @staticmethod
    def register(registry, *, settings: Settings | None = None, http=None, files=None) -> None:
        registry.register_class(WebFetchTool(http=http))
        registry.register_class(ExtractTextTool(file_provider=files))