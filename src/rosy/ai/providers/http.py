"""Generic OpenAI-compatible HTTP provider.

Covers OpenRouter, OpenAI, Groq, Mistral, and OpenAI-compatible endpoints for
Gemini and Anthropic. Uses a shared async httpx client with timeout handling.
"""

import logging
from dataclasses import dataclass

import httpx

from ..base import ChatMessage, ChatProvider, ChatResult

logger = logging.getLogger("rosy.ai.providers.http")


@dataclass
class ProviderConfig:
    base_url: str
    default_model: str


class OpenAICompatProvider(ChatProvider):
    """Talk to any OpenAI-compatible ``/chat/completions`` endpoint."""

    name = "openai-compat"

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        super().__init__(api_key, model, base_url)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.8,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
    ) -> ChatResult:
        client = await self._get_client()
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload: dict = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools

        headers = {"Authorization": f"Bearer {self.api_key}"}
        # Anthropic's OpenAI-compatible layer uses x-api-key instead.
        if "anthropic.com" in (self.base_url or ""):
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}

        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Provider %s returned HTTP %s", self.name, exc.response.status_code)
            raise
        except httpx.HTTPError as exc:
            logger.warning("Provider %s network error: %s", self.name, exc)
            raise

        content = data["choices"][0]["message"]["content"] or ""
        return ChatResult(
            content=content,
            model=data.get("model", self.model),
            provider=self.name,
            usage=data.get("usage", {}),
            raw=data,
        )
