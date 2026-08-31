"""AI provider abstraction.

A provider is responsible for turning a list of chat messages into a model
response. Different backends (OpenRouter, OpenAI, Gemini, Anthropic, Groq,
Mistral, custom OpenAI-compatible endpoints) implement `Provider`.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

import httpx

from rosy.core.errors import (
    ProviderAuthError,
    ProviderRateLimited,
    ProviderUnavailable,
)


@dataclass
class ChatMessage:
    role: str  # system | user | assistant | tool
    content: str
    name: str | None = None
    # Optional structured tool-call arguments passed by the conversation engine.
    tool_calls: list[dict] | None = None


@dataclass
class ChatResult:
    text: str
    provider: str
    model: str
    usage: dict = field(default_factory=dict)
    raw: dict | None = None
    tool_calls: list[dict] | None = None

    @property
    def prompt_tokens(self) -> int:
        return int(self.usage.get("prompt_tokens", 0) or 0)

    @property
    def completion_tokens(self) -> int:
        return int(self.usage.get("completion_tokens", 0) or 0)


@dataclass
class ProviderConfig:
    """Resolved credentials/model for a single chat call."""

    provider: str
    api_key: str
    base_url: str
    model: str
    extra: dict[str, Any] = field(default_factory=dict)


class Provider(abc.ABC):
    """Base class for AI chat providers."""

    name: str = "base"

    def __init__(self, config: ProviderConfig, http: httpx.AsyncClient) -> None:
        self.config = config
        self.http = http

    @abc.abstractmethod
    async def chat(self, messages: list[ChatMessage], **kwargs: Any) -> ChatResult:
        """Send messages and return a ChatResult."""
        raise NotImplementedError

    def _handle_status(self, resp: httpx.Response) -> None:
        if resp.status_code == 429:
            raise ProviderRateLimited(f"{self.name} rate limited", provider=self.name)
        if resp.status_code in (401, 403):
            raise ProviderAuthError(f"{self.name} auth error", provider=self.name)
        if resp.status_code >= 500:
            raise ProviderUnavailable(f"{self.name} HTTP {resp.status_code}", provider=self.name)
        resp.raise_for_status()

    async def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict:
        try:
            resp = await self.http.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise ProviderUnavailable(f"{self.name} timed out", provider=self.name) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(f"{self.name} network error", provider=self.name) from exc
        self._post_status(resp)
        try:
            return resp.json()
        except ValueError as exc:
            raise ProviderUnavailable(f"{self.name}: non-JSON response", provider=self.name) from exc


class OpenAICompatProvider(Provider):
    """Generic implementation for OpenAI-compatible chat endpoints.

    Works for OpenRouter, OpenAI, Groq, Mistral and custom endpoints.
    """

    name = "openai-compat"

    def build_headers(self) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        extra = self.config.extra
        if extra.get("referer"):
            headers["HTTP-Referer"] = extra["referer"]
        if extra.get("title"):
            headers["X-Title"] = extra["title"]
        return headers

    def _payload(self, messages: list[ChatMessage], **kwargs: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": m.role, "content": m.content, **({"name": m.name} if m.name else {})}
                for m in messages
            ],
        }
        if kwargs.get("temperature") is not None:
            payload["temperature"] = kwargs["temperature"]
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]
        if kwargs.get("max_tokens"):
            payload["max_tokens"] = kwargs["max_tokens"]
        return payload

    async def chat(self, messages: list[ChatMessage], **kwargs: Any) -> ChatResult:
        payload = self._payload(messages, **kwargs)
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        data = await self._post_json(url, payload, self.build_headers())
        try:
            choice = data["choices"][0]
        except (KeyError, IndexError) as exc:
            raise ProviderUnavailable(f"{self.name}: malformed response", provider=self.name) from exc
        message = choice.get("message", {})
        text = message.get("content") or ""
        tool_calls = message.get("tool_calls")
        return ChatResult(
            text=text,
            provider=self.name,
            model=self.config.model,
            usage=data.get("usage", {}),
            raw=data,
            tool_calls=tool_calls,
        )


class ProviderRegistry:
    """Registry mapping provider keys to provider classes."""

    def __init__(self) -> None:
        self._classes: dict[str, type[Provider]] = {
            "openai": OpenAICompatProvider,
            "openrouter": OpenAICompatProvider,
            "groq": OpenAICompatProvider,
            "mistral": OpenAICompatProvider,
        }

    def register(self, name: str, cls: type[Provider]) -> None:
        self._classes[name] = cls

    def known(self) -> list[str]:
        return sorted(self._classes.keys())

    def create(self, name: str, config: ProviderConfig, http: httpx.AsyncClient) -> Provider:
        cls = self._classes.get(name)
        if cls is None:
            raise ValueError(f"Unknown provider: {name}")
        return cls(config, http)