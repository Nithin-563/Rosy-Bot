"""Web search and page-fetch tools.

Uses a configurable search URL (default DuckDuckGo HTML) to avoid requiring a
paid search API key. Returns plain text snippets. Never executes OS commands.
"""

import html
import re

import httpx

from ..config import get_settings
from .base import Tool

SEARCH_URL = "https://duckduckgo.com/html/?q={query}"


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web and return a short list of results with snippets."
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "The search query."}},
        "required": ["query"],
    }

    async def execute(self, query: str = "") -> str:
        if not query:
            return "Provide a query."
        settings = get_settings()
        timeout = httpx.Timeout(settings.web_search_timeout)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(SEARCH_URL.format(query=query))
            if resp.status_code != 200:
                return f"Search failed (HTTP {resp.status_code})."
            text = resp.text
        return self._extract(text)

    @staticmethod
    def _extract(html_text: str) -> str:
        results = re.findall(
            r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>.*?'
            r'<a class="result__snippet"[^>]*>(.*?)</a>',
            html_text,
            re.DOTALL,
        )
        lines = []
        for idx, (url, title, snippet) in enumerate(results[:5], 1):
            title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
            snippet = html.unescape(re.sub(r"<[^>]+>", "", snippet)).strip()
            lines.append(f"{idx}. {title}\n   {url}\n   {snippet}")
        if not lines:
            return "No results found."
        return "\n\n".join(lines)
