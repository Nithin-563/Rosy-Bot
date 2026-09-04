"""Context builder.

Assembles a bounded, token-budgeted context: recent messages, conversation
summary, relevant memories, guild context, and personality. Does not dump
unlimited history.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rosy.ai.base import ChatMessage
from rosy.config import Settings
from rosy.conversation.personality import Personality
from rosy.models import Memory


@dataclass
class Context:
    """Everything needed to build the model prompt for one interaction."""

    user_id: int | None = None
    guild_id: int | None = None
    channel_id: int | None = None
    is_dm: bool = False
    history: list[ChatMessage] = field(default_factory=list)
    summary: str = ""
    memories: list[Memory] = field(default_factory=list)
    personality_mode: str = "friendly"
    emotion: str = ""
    guild_name: str = ""
    user_name: str = ""
    extra_notes: str = ""


class ContextBuilder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _budget(self, text: str, budget: int) -> str:
        """Cheap char-based token budget heuristic (~4 chars/token)."""
        if not text:
            return ""
        max_chars = budget * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "…"

    def build_messages(self, ctx: Context) -> list[ChatMessage]:
        personality = Personality(ctx.personality_mode)
        system_parts = [personality.system_block(ctx.emotion)]
        if ctx.is_dm:
            system_parts.append("This is a private DM conversation. Keep this user's data private.")
        if ctx.guild_name:
            system_parts.append(f"You are in the server '{ctx.guild_name}'.")
        if ctx.user_name:
            system_parts.append(f"The person you are talking to is '{ctx.user_name}'.")
        if ctx.summary:
            system_parts.append(f"Conversation summary so far: {ctx.summary}")

        mem_lines = [f"- {m.content} (importance {m.importance:.1f})" for m in ctx.memories]
        if mem_lines:
            budget = self.settings.max_context_tokens // 4
            joined = "\n".join(mem_lines)
            system_parts.append("Relevant memories:\n" + self._budget(joined, budget))

        if ctx.extra_notes:
            system_parts.append(ctx.extra_notes)

        messages: list[ChatMessage] = [ChatMessage(role="system", content="\n\n".join(system_parts))]

        trimmed = ctx.history[-self.settings.max_context_messages:]
        for m in reversed(trimmed):
            messages.append(m)
        return messages