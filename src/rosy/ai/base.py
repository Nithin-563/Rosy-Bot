"""Abstract AI provider interface.

Providers expose an OpenAI-compatible chat completions shape so the manager
can stay provider-agnostic. Each provider class handles its own HTTP transport
and returns a :class:`ChatResult`.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResult:
    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)
    raw: Optional[Any] = None


class ChatProvider(ABC):
    """Base class for all AI chat providers."""

    name: str = "base"

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.8,
        max_tokens: int | None = None,
        tools: Optional[list[dict]] = None,
    ) -> ChatResult:
        """Send a chat completion request and return the assistant reply."""
        raise NotImplementedError
