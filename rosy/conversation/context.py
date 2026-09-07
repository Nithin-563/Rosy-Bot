"""Context building — assemble a bounded, token-aware prompt for the model."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from rosy.ai.base import Message
from rosy.config import get_settings
from rosy.personality.manager import PersonalityManager

log = logging.getLogger(__name__)

# Rough char->token heuristic; sufficient for budgeting, not accounting.
_CHARS_PER_TOKEN = 4


@dataclass
class ConversationContext:
    messages: list[Message] = field(default_factory=list)
    # Extra metadata surfaced to the response layer / tools.
    summary: str = ""
    memories: list[str] = field(default_factory=list)
    guild_name: str = ""
    user_name: str = ""

    def estimated_tokens(self) -> int:
        return sum(len(m.content) // _CHARS_PER_TOKEN for m in self.messages)


class ContextBuilder:
    def __init__(self, personality: PersonalityManager | None = None, settings: object | None = None) -> None:
        self.personality = personality or PersonalityManager()
        self.settings = settings or get_settings()

    def build(
        self,
        *,
        mode: str | None = None,
        recent_messages: list[Message],
        summary: str = "",
        memories: list[str] | None = None,
        guild_name: str = "",
        user_name: str = "",
        extra_instructions: str = "",
    ) -> ConversationContext:
        s = self.settings
        system = self.personality.system_prompt(mode)
        if extra_instructions:
            system += "\n" + extra_instructions

        ctx = ConversationContext(
            summary=summary,
            memories=memories or [],
            guild_name=guild_name,
            user_name=user_name,
        )

        # Budget: reserve space for system + memory + summary, then fit history.
        budget = int(s.max_context_tokens)
        used = len(system) // _CHARS_PER_TOKEN
        used += len(extra_instructions) // _CHARS_PER_TOKEN

        memory_text = ""
        if memories:
            memory_text = "Relevant memories:\n" + "\n".join(f"- {m}" for m in memories)
            used += len(memory_text) // _CHARS_PER_TOKEN
        summary_text = ""
        if summary:
            summary_text = f"Conversation summary (so far): {summary}"
            used += len(summary_text) // _CHARS_PER_TOKEN

        # Keep as many recent messages as fit, from most recent backwards.
        fitted: list[Message] = []
        for msg in reversed(recent_messages):
            cost = len(msg.content) // _CHARS_PER_TOKEN + 1
            if used + cost > budget:
                break
            fitted.append(msg)
            used += cost
        fitted.reverse()

        ctx.messages.append(Message(role="system", content=system))
        if memory_text:
            ctx.messages.append(Message(role="system", content=memory_text))
        if summary_text:
            ctx.messages.append(Message(role="system", content=summary_text))
        ctx.messages.extend(fitted)
        return ctx
