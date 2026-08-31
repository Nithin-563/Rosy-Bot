"""RosyBot — the application container.

Wires configuration, database, AI manager, memory, conversation engine,
reminders, moderation, settings, tools and cogs together, and exposes them to
cogs via `bot.services`.
"""

from __future__ import annotations

import logging
import time

import discord
from discord.ext import commands

from rosy.ai import AIManager
from rosy.ai.providers import register_native_providers
from rosy.config import Settings, get_settings
from rosy.conversation import ConversationEngine, DecisionEngine
from rosy.core import init_encryption
from rosy.core.db import Database
from rosy.core.errors import safe_user_message
from rosy.memory import MemoryService
from rosy.moderation import ModerationService
from rosy.reminders import ReminderService
from rosy.settings import GuildSettingsService
from rosy.tools import build_default_registry

logger = logging.getLogger("rosy.bot")


def _redact_db_url(url) -> str:
    """Hide credentials in a DB URL for safe logging."""
    s = str(url)
    if "://" in s and "@" in s:
        head, _, tail = s.partition("://")
        creds, _, rest = tail.partition("@")
        return f"{head}://***@{rest}"
    return s


class RosyBot(commands.Bot):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        intents = self._build_intents()
        super().__init__(command_prefix=self._prefix, intents=intents)

        # --- service wiring ---
        self.db = Database.from_settings(self.settings)
        init_encryption(self.settings.encryption_key, self.settings.encryption_salt)
        self.ai = AIManager(self.settings, self.db)
        register_native_providers(self.ai.registry)
        self.memory = MemoryService(self.db, self.settings)
        self.guild_settings = GuildSettingsService(self.db)
        self.moderation = ModerationService(self.db)
        self.reminders = ReminderService(self.db)
        self.decision = DecisionEngine()
        self.conversation = ConversationEngine(self.settings, self.ai, self.memory, self.decision)
        self.tools = build_default_registry(http=None, files=None)
        self.services = self  # cogs can access everything via bot

        self._stats = {"commands": 0, "messages": 0, "started": time.monotonic()}
    @staticmethod
    def _prefix(bot: RosyBot, message: discord.Message) -> list[str]:
        return [f"<@{bot.user.id}> ", f"<@!{bot.user.id}> "]

    def _build_intents(self) -> discord.Intents:
        s = self.settings
        intents = discord.Intents.default()
        intents.message_content = s.enable_message_content_intent
        intents.members = s.enable_member_intent
        intents.voice_states = s.enable_voice_state_intent
        intents.guilds = s.enable_guilds_intent
        intents.moderation = s.enable_moderation_intent
        return intents

    # ------------------------------------------------------------- lifecycle

    async def setup_hook(self) -> None:
        logger.info("Using database: %s", _redact_db_url(self.db.engine.url))
        await self.db.create_all()
        logger.info("Database schema ready.")
        await self.ai.start()
        self.tools = build_default_registry(http=self.ai.http, files=None)
        await self.load_cogs()
        await self.reminders.start(self.fire_reminder)
        logger.info("Rosy ready to sync commands.")

    async def sync_commands(self) -> None:
        """Register slash commands with Discord.

        Guilds in dev_guild_ids are synced instantly; otherwise commands are
        registered globally (global sync can take up to an hour to propagate).
        """
        guild_ids = self.settings.guild_ids()
        try:
            if guild_ids:
                for gid in guild_ids:
                    await self.tree.sync(guild=discord.Object(id=gid))
                logger.info("Synced %d slash commands to dev guilds %s", len(list(self.tree.get_commands())), guild_ids)
            else:
                await self.tree.sync()
                logger.info("Synced %d slash commands globally.", len(list(self.tree.get_commands())))
        except Exception:  # noqa: BLE001
            logger.exception("Command sync failed (commands will not appear until a later sync).")

    async def load_cogs(self) -> None:
        for cog in [
            "conversation",
            "memory",
            "admin",
            "moderation",
            "reminders",
            "games",
            "custom_commands",
            "music",
            "voice",
            "fun",
            "help",
        ]:
            try:
                await self.load_extension(f"rosy.cogs.{cog}")
            except Exception:
                logger.exception("Failed to load cog %s", cog)

    async def fire_reminder(self, reminder) -> None:
        try:
            channel = self.get_channel(reminder.channel_id)
            if channel is None:
                logger.warning("Reminder channel not found: %s", reminder.channel_id)
                return
            user = self.get_user(reminder.user_id) or await self.fetch_user(reminder.user_id)
            mention = user.mention if user else f"<@{reminder.user_id}>"
            await channel.send(f"🔔 {mention} Reminder: {reminder.message}")
        except discord.HTTPException:
            logger.exception("Could not send reminder id=%s", reminder.id)

    async def on_ready(self) -> None:
        logger.info("Logged in as %s (%s)", self.user, self.user.id)
        if not getattr(self, "_synced", False):
            await self.sync_commands()
            self._synced = True

    async def close(self) -> None:
        await self.reminders.stop()
        await self.ai.stop()
        await self.db.dispose()
        await super().close()

    # ---------- metrics / helpers

    def record_command(self) -> None:
        self._stats["commands"] += 1

    def record_message(self) -> None:
        self._stats["messages"] += 1

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    async def on_command_error(self, ctx, error) -> None:
        error = getattr(error, "original", error)
        message = safe_user_message(error)
        try:
            await ctx.send(embed=discord.Embed(description=message, color=discord.Color.red()))
        except discord.HTTPException:
            pass
        logger.info("Command error in %s: %s", ctx.command, message)


def build_bot(settings: Settings | None = None) -> RosyBot:
    return RosyBot(settings)