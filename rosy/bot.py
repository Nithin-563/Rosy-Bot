"""RosyBot — wires all subsystems together and owns the Discord client lifecycle.

This is the composition root. Cogs are registered here; services are injected
so tests can construct the bot without a live Discord connection.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from rosy.ai.factory import ProviderRegistry
from rosy.ai.router import ProviderRouter
from rosy.config import get_settings
from rosy.conversation.engine import ConversationEngine
from rosy.conversation.manager import ConversationManager
from rosy.custom_commands.service import CustomCommandService
from rosy.db.session import build_engine, build_sessionmaker
from rosy.games.service import GamesService
from rosy.knowledge.service import KnowledgeService
from rosy.memory.service import MemoryService
from rosy.moderation.service import ModerationService
from rosy.music.player import MusicPlayer
from rosy.personality.manager import PersonalityManager
from rosy.reminders.service import ReminderService
from rosy.security.rate_limit import RateLimiter
from rosy.tools.registry import build_default_registry
from rosy.voice.manager import VoiceManager

log = logging.getLogger(__name__)

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True


class RosyBot(commands.Bot):
    """Composition root exposing all Rosy services as attributes."""

    def __init__(self, *, engine=None, sessions=None, settings: object | None = None) -> None:
        self.settings = settings or get_settings()
        self.engine = engine or build_engine()
        self.sessions = sessions or build_sessionmaker(self.engine)

        # Services
        self.personality = PersonalityManager()
        self.registry = build_default_registry()
        self.router = ProviderRouter(ProviderRegistry())
        self.engine_ai = ConversationEngine(self.router, self.registry)
        self.conversations = ConversationManager(self.sessions)
        self.memory = MemoryService()
        self.moderation = ModerationService()
        self.reminders = ReminderService(self.sessions)
        self.knowledge = KnowledgeService()
        self.custom_commands = CustomCommandService()
        self.games = GamesService()
        self.music = MusicPlayer()
        self.voice = VoiceManager()
        self.rate_limiter = RateLimiter(
            max_calls=int(self.settings.rate_limit_max),
            window_seconds=int(self.settings.rate_limit_window_seconds),
        )

        super().__init__(
            command_prefix=commands.when_mentioned_or(self.settings.discord_command_prefix),
            intents=INTENTS,
            help_command=None,
        )

        # Reminder delivery by user id.
        self.reminders.set_sender("default", self._deliver_reminder)

    async def setup_hook(self) -> None:
        # Ensure schema exists on first boot (production uses alembic migrations;
        # create_all is a safe fallback that makes the bot always bootable).
        from rosy.db.models import Base  # noqa: F401 - registers models

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await self._register_cogs()
        asyncio.get_running_loop().create_task(self.reminders.loop())
        log.info("Rosy setup complete (provider=%s)", self.settings.default_provider_name)

    async def _register_cogs(self) -> None:
        from rosy.cogs import CORE_COGS

        for cog in CORE_COGS:
            try:
                await self.add_cog(cog(self))
                log.debug("Loaded cog %s", cog.__name__)
            except Exception:  # noqa: BLE001
                log.exception("Failed to load cog %s", cog.__name__)

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id=%s)", self.user, self.user.id)

    async def _deliver_reminder(self, reminder) -> None:
        """Deliver a reminder to the target user (DM), or post in channel."""
        user = self.get_user(reminder.user_id) or await self.fetch_user(reminder.user_id)
        text = f"⏰ **Reminder:** {reminder.message}"
        if reminder.channel_id and self.get_channel(reminder.channel_id) is not None:
            channel = self.get_channel(reminder.channel_id)
            await channel.send(f"<@{reminder.user_id}> {text}")
        elif user is not None:
            await user.send(text)

    async def close(self) -> None:
        await super().close()
        if self.engine is not None:
            await self.engine.dispose()


def build_bot(**kwargs) -> RosyBot:
    return RosyBot(**kwargs)
