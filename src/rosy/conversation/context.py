"""Context builder: assembles a bounded, token-aware system/user prompt."""

import logging
from dataclasses import dataclass
from typing import Optional

from ..ai.base import ChatMessage
from ..memory.service import MemoryService
from ..conversation.personality import Personality

logger = logging.getLogger("rosy.context")

# Rough token estimate for display/limiting purposes.
_CHARS_PER_TOKEN = 4


@dataclass
class ContextBundle:
    system: str
    user_messages: list[ChatMessage]


class ContextBuilder:
    """Builds a context bundle for a single response."""

    def __init__(self, personality: Personality, max_tokens: int = 4000):
        self.personality = personality
        self.max_tokens = max_tokens

    @staticmethod
    def _est_tokens(text: str) -> int:
        return max(1, len(text) // _CHARS_PER_TOKEN)

    def build(
        self,
        *,
        message_text: str,
        author_name: str,
        memories: list,
        recent_history: list[ChatMessage] | None = None,
        guild_name: Optional[str] = None,
        extra_system: str = "",
    ) -> ContextBundle:
        parts = [self.personality.system_prompt]

        if guild_name:
            parts.append(f"Context: you are chatting in the server \"{guild_name}\".")

        memory_lines = [
            f"- [{m.memory_type}] {m.key}: {m.value}" for m in memories[:8]
        ]
        if memory_lines:
            parts.append("What you remember (use it naturally, do not quote it verbatim):\n" + "\n".join(memory_lines))

        if extra_system:
            parts.append(extra_system)

        system = "\n\n".join(parts)

        user_messages: list[ChatMessage] = []
        budget = self.max_tokens - self._est_tokens(system) - self._est_tokens(message_text)

        # Build recent history, newest-last, trimming from the front to stay in budget.
        if recent_history:
            history: list[ChatMessage] = list(recent_history)
            while history and self._est_tokens(sum(m.content for m in history)) > budget:
                history.pop(0)
            user_messages.extend(history)

        user_messages.append(
            ChatMessage(role="user", content=f"{author_name}: {message_text}")
        )
        return ContextBundle(system=system, user_messages=user_messages)
