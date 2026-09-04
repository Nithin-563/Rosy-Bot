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


class WebSearchTool(BaseTool):
    """Web search via DuckDuckGo's HTML endpoint (no API key required)."""

    spec = ToolSpec(
        name="web_search",
        description="Search the web and return a list of result titles, URLs and snippets.",
        parameters={
            "query": {"type": "string", "description": "The search query."},
            "max_results": {"type": "integer", "description": "Max results to return (1-10)."},
        },
        timeout_seconds=20.0,
    )

    def __init__(self, http: httpx.AsyncClient) -> None:
        self.http = http

    async def execute(self, query: str = "", max_results: int = 5, **kwargs) -> str:
        if not query or len(query) > 200:
            raise ValueError("Please provide a search query.")
        max_results = max(1, min(int(max_results), 10))
        params = {"q": query}
        try:
            resp = await self.http.get(
                "https://lite.duckduckgo.com/lite/",
                params=params,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
                    )
                },
                follow_redirects=True,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ValueError(f"Web search failed: {exc}") from exc
        return _parse_ddg_results(resp.text, max_results)


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


def _parse_ddg_results(html: str, max_results: int) -> str:
    import html as _html

    results: list[str] = []
    # lite.duckduckgo.com renders each result as an <a ...> containing class='result-link'.
    # Match whole anchor tags, then check the class and extract the href + title.
    for m in re.finditer(r"<a\s[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", html, re.I | re.S):
        href, inner = m.group(1), m.group(2)
        if "result-link" not in m.group(0):
            continue
        if href.startswith("//"):
            href = "https:" + href
        title = re.sub(r"<[^>]+>", "", inner).strip()
        results.append(f"- {_html.unescape(title)}: {_html.unescape(href)}")
        if len(results) >= max_results:
            break
    return "\n".join(results) if results else "No results found for that query."


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
        if http is None:
            return
        registry.register_class(WebFetchTool(http=http))
        registry.register_class(WebSearchTool(http=http))
        registry.register_class(ExtractTextTool(file_provider=files))