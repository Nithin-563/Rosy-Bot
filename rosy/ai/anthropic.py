"""Anthropic Claude provider (native Messages API)."""
from __future__ import annotations

from typing import Any

import httpx

from rosy.ai.base import BaseProvider, ChatResponse, Message, ProviderError, ToolDef, Usage


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    DEFAULT_BASE = "https://api.anthropic.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url or self.DEFAULT_BASE, model=model)
        self._client: httpx.AsyncClient | None = None

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "x-api-key": self.api_key or "",
                    "anthropic-version": "2023-06-01",
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
        system = "\n".join(m.content for m in messages if m.role == "system")
        convo = [m for m in messages if m.role != "system"]

        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": [_to_wire(m) for m in convo],
            "temperature": temperature,
            "max_tokens": max_tokens or 1500,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.parameters,
                }
                for t in tools
            ]

        try:
            resp = await self._http().post("/messages", json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"anthropic HTTP {exc.response.status_code}: {exc.response.text[:500]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"anthropic request failed: {exc}") from exc

        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        tool_calls: list[dict[str, Any]] = []
        for b in content_blocks:
            if b.get("type") == "tool_use":
                tool_calls.append(
                    {
                        "id": b.get("id"),
                        "name": b.get("name", ""),
                        "arguments": b.get("input", {}),
                    }
                )
        usage_raw = data.get("usage") or {}
        return ChatResponse(
            content=text,
            tool_calls=tool_calls,
            finish_reason=data.get("stop_reason"),
            usage=Usage(
                prompt_tokens=usage_raw.get("input_tokens", 0),
                completion_tokens=usage_raw.get("output_tokens", 0),
                total_tokens=usage_raw.get("input_tokens", 0)
                + usage_raw.get("output_tokens", 0),
            ),
            model=data.get("model") or self._resolve_model(model),
            provider=self.name,
        )

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def _to_wire(m: Message) -> dict[str, Any]:
    if m.tool_calls:
        return {"role": "assistant", "content": [{"type": "tool_use", **tc} for tc in m.tool_calls]}
    if m.role == "tool":
        return {"role": "user", "content": [{"type": "tool_result", "tool_use_id": m.name, "content": m.content}]}
    return {"role": m.role, "content": m.content}
