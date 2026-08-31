"""Conversation engine.

Orchestrates context building, memory recall, AI calling, and personality
adaptation for a single chat interaction.
"""

from __future__ import annotations

import logging
import time

from rosy.ai import AIManager, ChatMessage, ChatResult
from rosy.config import Settings
from rosy.conversation.context import Context, ContextBuilder
from rosy.conversation.decision import DecisionEngine, DecisionInput
from rosy.conversation.personality import Personality
from rosy.memory.service import MemoryService
from rosy.models import MemoryScope

logger = logging.getLogger("rosy.conversation")


class ConversationEngine:
    def __init__(
        self,
        settings: Settings,
        ai: AIManager,
        memory: MemoryService,
        decision: DecisionEngine | None = None,
    ) -> None:
        self.settings = settings
        self.ai = ai
        self.memory = memory
        self.decision = decision or DecisionEngine()
        self.context_builder = ContextBuilder(settings)
        self._last_response: dict[str, float] = {}

    async def should_respond(self, *, bot_id, author_id, content, mentions_me=False, is_reply_to_me=False, is_dm=False, is_bot=False, channel_key="", autonomous_enabled=True, probability=0.15) -> bool:
        inp = DecisionInput(
            bot_id=bot_id,
            author_id=author_id,
            content=content,
            mentions_me=mentions_me,
            is_reply_to_me=is_reply_to_me,
            is_dm=is_dm,
            is_bot=is_bot,
            autonomous_enabled=autonomous_enabled,
            autonomous_probability=probability,
            cooldown_seconds=self.settings.response_cooldown_seconds,
            last_response_at=self._last_response.get(channel_key, 0.0),
        )
        return self.decision.should_respond(inp).should

    async def generate(
        self,
        *,
        user_text: str,
        user_id: int | None = None,
        guild_id: int | None = None,
        channel_id: int | None = None,
        is_dm: bool = False,
        history: list[ChatMessage] | None = None,
        personality_mode: str = "friendly",
        guild_name: str = "",
        user_name: str = "",
        provider: str | None = None,
        model: str = "",
    ) -> ChatResult:
        memories = []
        try:
            if getattr(self.settings, "memory_enabled", True) and self.memory:
                if is_dm and user_id:
                    memories += await self.memory.recall(scope=MemoryScope.dm, guild_id=None, user_id=user_id)
                if guild_id:
                    memories += await self.memory.recall(scope=MemoryScope.guild, guild_id=guild_id, user_id=None)
                    if user_id:
                        memories += await self.memory.recall(scope=MemoryScope.user_in_guild, guild_id=guild_id, user_id=user_id)
        except Exception:  # pragma: no cover - memory must never block a reply
            logger.exception("Memory recall failed; continuing without memories.")

        mode = Personality.detect_mode(user_text, personality_mode)
        ctx = Context(
            user_id=user_id,
            guild_id=guild_id,
            channel_id=channel_id,
            is_dm=is_dm,
            history=history or [],
            memories=memories,
            personality_mode=mode,
            guild_name=guild_name,
            user_name=user_name,
        )
        # Append the current user turn.
        ctx.history = (ctx.history or []) + [ChatMessage(role="user", content=user_text)]
        messages = self.context_builder.build_messages(ctx)

        result = await self.ai.chat(
            messages,
            provider=provider,
            model=model,
            guild_id=guild_id,
            temperature=self.settings.temperature,
        )
        return result

    def mark_response(self, channel_key: str) -> None:
        self._last_response[channel_key] = time.monotonic()