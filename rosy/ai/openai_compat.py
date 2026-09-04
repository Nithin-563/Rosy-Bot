"""Provider implementation for OpenAI-compatible chat-completions APIs.

Used by OpenRouter (default), OpenAI, Groq, Mistral, and Gemini's OpenAI-compat
endpoint — they share the same wire format.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from rosy.ai.base import BaseProvider, ChatResponse, Message, ProviderError, ToolDef, Usage


class OpenAICompatProvider(BaseProvider):
    name = "openai-compat"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        *,
        provider_name: str = "openai-compat",
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, model=model)
        self.name = provider_name
        self._client: httpx.AsyncClient | None = None

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list[ToolDef] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> ChatResponse:
        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": [_to_wire(m) for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]
            payload["tool_choice"] = "auto"

        try:
            resp = await self._http().post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            raise ProviderError(f"{self.name} HTTP {exc.response.status_code}: {body}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.name} request failed: {exc}") from exc

        try:
            choice = data["choices"][0]
            msg = choice.get("message", {})
            usage_raw = data.get("usage") or {}
            return ChatResponse(
                content=msg.get("content") or "",
                tool_calls=self._split_tool_calls(msg.get("tool_calls", [])),
                finish_reason=choice.get("finish_reason"),
                usage=Usage(
                    prompt_tokens=usage_raw.get("prompt_tokens", 0),
                    completion_tokens=usage_raw.get("completion_tokens", 0),
                    total_tokens=usage_raw.get("total_tokens", 0),
                ),
                model=data.get("model") or self._resolve_model(model),
                provider=self.name,
            )
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"{self.name} returned malformed response.") from exc

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def _to_wire(m: Message) -> dict[str, Any]:
    d: dict[str, Any] = {"role": m.role, "content": m.content}
    if m.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.get("id"),
                "type": "function",
                "function": {
                    "name": tc.get("name", ""),
                    "arguments": tc.get("arguments") or "{}",
                },
            }
            for tc in m.tool_calls
        ]
    return d


def parse_arguments(raw: str) -> dict[str, Any]:
    """Safely parse a tool-call arguments string."""
    try:
        parsed = json.loads(raw or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
