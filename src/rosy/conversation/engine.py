"""Conversation engine: response-decision + orchestration.

Decides whether Rosy should reply and, if so, assembles context and calls the
AI provider. Keeps track of per-channel cooldowns to prevent spam.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from ..ai.base import ChatMessage, ChatProvider
from ..ai.manager import AIProviderManager
from ..config import get_settings
from .context import ContextBuilder
from .personality import Personality

logger = logging.getLogger("rosy.engine")

BOT_NAME = "Rosy"


@dataclass
class Decision:
    should_reply: bool
    reason: str = ""


@dataclass
class ConversationEngine:
    provider_manager: AIProviderManager
    channel_cooldowns: dict[int, float] = field(default_factory=dict)

    def decide(
        self,
        *,
        content: str,
        is_mention: bool,
        is_reply_to_bot: bool,
        has_bot_name: bool,
        allow_autonomous: bool,
        channel_id: int,
        now: float | None = None,
    ) -> Decision:
        """Decide whether to reply based on signals and cooldown."""
        now = now or time.time()
        low = content.lower()

        if is_mention or is_reply_to_bot or has_bot_name:
            self.channel_cooldowns[channel_id] = now
            return Decision(True, "directed")

        if not allow_autonomous:
            return Decision(False, "autonomous disabled")

        cooldown = get_settings().ros_autonomous_cooldown
        last = self.channel_cooldowns.get(channel_id, 0.0)
        if now - last < cooldown:
            return Decision(False, "cooldown")

        # Only autonomously join if the message looks conversational and Rosy
        # has participated recently or the message is a question worth answering.
        if not (low.endswith("?") or len(content.strip()) < 40):
            return Decision(False, "not conversational enough")

        self.channel_cooldowns[channel_id] = now
        return Decision(True, "autonomous")

    def record_participation(self, channel_id: int) -> None:
        self.channel_cooldowns[channel_id] = time.time()

    async def respond(
        self,
        *,
        message_text: str,
        author_name: str,
        guild_id: Optional[int],
        guild_name: Optional[str],
        provider: Optional[ChatProvider],
        personality: Personality,
        memories: list,
        recent_history: list[ChatMessage] | None = None,
    ) -> str:
        builder = ContextBuilder(personality)
        bundle = builder.build(
            message_text=message_text,
            author_name=author_name,
            memories=memories,
            recent_history=recent_history,
            guild_name=guild_name,
        )
        messages = [ChatMessage(role="system", content=bundle.system)] + bundle.user_messages
        result = await self.provider_manager.chat(
            messages, provider=provider, temperature=0.85
        )
        return result.content.strip()
