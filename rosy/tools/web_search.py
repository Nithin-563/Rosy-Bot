"""Web-search tool.

Uses a configured search provider (Tavily preferred) and falls back to
DuckDuckGo's HTML endpoint when no API key is set. Results are trimmed to
titles + snippets + URLs; the bot distinguishes these from model knowledge by
labeling the result source.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote_plus

import httpx

from rosy.config import get_settings
from rosy.tools.base import BaseTool, ToolResult

UA = "Mozilla/5.0 (RosyBot/1.0; +https://example.invalid/rosy)"


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Search the web for current information. Returns titles, snippets and source URLs. "
        "Use this for up-to-date facts, news, or anything after the model's training cutoff."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query."},
            "max_results": {"type": "integer", "description": "Max results (default 5, max 8)."},
        },
        "required": ["query"],
    }
    timeout_seconds = 20.0

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=8.0), follow_redirects=True)
        return self._client

    async def _tavily(self, query: str, k: int) -> list[dict[str, Any]] | None:
        key = self.settings.tavily_api_key
        if not key:
            return None
        resp = await self._http().post(
            "https://api.tavily.com/search",
            json={"api_key": key, "query": query, "max_results": k, "search_depth": "basic"},
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            {
                "title": r.get("title", ""),
                "snippet": (r.get("content") or "")[:300],
                "url": r.get("url", ""),
            }
            for r in data.get("results", [])
        ]

    async def _duckduckgo(self, query: str, k: int) -> list[dict[str, Any]]:
        url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
        resp = await self._http().get(url, headers={"User-Agent": UA})
        resp.raise_for_status()
        html = resp.text
        results: list[dict[str, Any]] = []
        # Minimal extraction of result blocks — robust enough for a tool fallback.
        from html import unescape
        import re
        blocks = re.findall(r'<div class="result__body.*?</div>\s*</div>\s*</div>', html, re.S)
        for block in blocks[:k]:
            m_title = re.search(r'class="result__a"[^>]*>(.*?)</a>', block, re.S)
            m_url = re.search(r'class="result__a" href="([^"]+)"', block, re.S)
            m_snip = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', block, re.S)
            title = unescape(re.sub(r"<[^>]+>", "", m_title.group(1))) if m_title else ""
            snip = unescape(re.sub(r"<[^>]+>", "", m_snip.group(1))) if m_snip else ""
            url = m_url.group(1) if m_url else ""
            results.append({"title": title, "snippet": snip, "url": url})
        return results

    async def run(self, arguments: dict[str, Any], context: dict[str, Any] | None = None) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(False, "", error="query is required.")
        try:
            k = min(int(arguments.get("max_results", 5) or 5), 8)
        except (TypeError, ValueError):
            k = 5
        try:
            results = await self._tavily(query, k)
            source = "tavily"
            if results is None:
                results = await self._duckduckgo(query, k)
                source = "duckduckgo"
        except Exception as exc:  # noqa: BLE001
            return ToolResult(False, "", error=f"web_search failed: {exc}")

        if not results:
            return ToolResult(True, "[web_search] No results found.")
        lines = [f"[source: {source}]"]
        for r in results:
            lines.append(f"- {r.get('title') or 'untitled'}\n  {r.get('snippet') or ''}\n  {r.get('url') or ''}")
        return ToolResult(True, "\n".join(lines))

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
