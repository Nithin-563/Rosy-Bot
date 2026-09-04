"""AI provider protocol and shared data structures."""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class Message:
    """A single chat message sent to or returned by a provider."""

    role: str  # system|user|assistant|tool
    content: str = ""
    name: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ToolDef:
    """Schema of a callable tool exposed to the model."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema object


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0


@dataclass
class ChatResponse:
    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str | None = None
    usage: Usage = field(default_factory=Usage)
    model: str = ""
    provider: str = ""


class ProviderError(RuntimeError):
    """Raised when an AI provider call fails."""


class BaseProvider(abc.ABC):
    """Interface every AI provider implements.

    Providers may be stateless or hold an optional API key. Per-guild
    overrides are applied by the factory / router, not by the provider itself.
    """

    name: str = "base"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abc.abstractmethod
    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list[ToolDef] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        model: str | None = None,
    ) -> ChatResponse:
        """Complete a conversation. Return text and/or tool calls."""
        raise NotImplementedError

    async def aclose(self) -> None:  # pragma: no cover - default no-op
        return None

    def _resolve_model(self, model: str | None) -> str:
        return model or self.model or ""

    @staticmethod
    def _split_tool_calls(raw: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """Normalize provider-specific tool-call payloads into Rosy's shape."""
        out: list[dict[str, Any]] = []
        for call in raw or []:
            fn = call.get("function", {})
            out.append(
                {
                    "id": call.get("id"),
                    "name": fn.get("name", ""),
                    "arguments": fn.get("arguments", "{}"),
                }
            )
        return out
