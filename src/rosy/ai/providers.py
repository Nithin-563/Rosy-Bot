"""Alternative provider implementations for native (non-OpenAI) APIs."""

from __future__ import annotations

from typing import Any

from rosy.ai.base import ChatMessage, ChatResult, Provider
from rosy.core.errors import ProviderUnavailable


class GeminiProvider(Provider):
    """Google Gemini via the HTTP generative language API."""

    name = "gemini"

    async def chat(self, messages: list[ChatMessage], **kwargs: Any) -> ChatResult:
        base = self.config.base_url.rstrip("/")
        url = f"{base}/models/{self.config.model}:generateContent?key={self.config.api_key}"
        contents = []
        for m in messages:
            if m.role == "system":
                continue  # Gemini has no system role; inject in payload preamble
            contents.append({"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]})
        payload: dict[str, Any] = {"contents": contents}
        if kwargs.get("temperature") is not None:
            payload["generationConfig"] = {"temperature": kwargs["temperature"]}
        data = await self._post_json(url, payload, {"Content-Type": "application/json"})
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise ProviderUnavailable(f"{self.name}: malformed response", provider=self.name) from exc
        usage = {
            "prompt_tokens": data.get("usageMetadata", {}).get("promptTokenCount", 0),
            "completion_tokens": data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
        }
        return ChatResult(text=text, provider=self.name, model=self.config.model, usage=usage, raw=data)


class AnthropicProvider(Provider):
    """Anthropic Claude Messages API."""

    name = "anthropic"

    async def chat(self, messages: list[ChatMessage], **kwargs: Any) -> ChatResult:
        url = self.config.base_url.rstrip("/") + "/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        system = "\n".join(m.content for m in messages if m.role == "system")
        body_messages = [
            {"role": m.role if m.role in ("user", "assistant") else "user", "content": m.content}
            for m in messages
            if m.role in ("user", "assistant", "tool")
        ]
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": body_messages,
            "max_tokens": kwargs.get("max_tokens") or 1024,
        }
        if system:
            payload["system"] = system
        if kwargs.get("temperature") is not None:
            payload["temperature"] = kwargs["temperature"]
        data = await self._post_json(url, payload, headers)
        try:
            text = "".join(block.get("text", "") for block in data["content"])
        except (KeyError, TypeError) as exc:
            raise ProviderUnavailable(f"{self.name}: malformed response", provider=self.name) from exc
        usage = {
            "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
            "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
        }
        return ChatResult(text=text, provider=self.name, model=self.config.model, usage=usage, raw=data)


def register_native_providers(registry) -> None:
    from rosy.ai.base import ProviderRegistry

    if not isinstance(registry, ProviderRegistry):
        return
    registry.register("gemini", GeminiProvider)
    registry.register("anthropic", AnthropicProvider)