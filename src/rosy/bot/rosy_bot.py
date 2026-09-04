"""RosyBot: wires the Discord layer to services and AI."""

import logging

import discord
from discord.ext import commands

from ..ai.base import ChatMessage
from ..ai.manager import AIProviderManager
from ..config import get_settings
from ..conversation.engine import ConversationEngine, BOT_NAME
from ..conversation.personality import Personality
from ..db import session as db_session
from ..db.models import Guild, User
from ..memory.service import MemoryService
from ..services.reminders import ReminderService
from ..tools.registry import ToolRegistry

logger = logging.getLogger("rosy.bot")

BOT_IDS = {1000000000000000000}  # populated at runtime with Rosy's own id


class RosyBot(commands.Bot):
    def __init__(self) -> None:
        settings = get_settings()
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings
        self.provider_manager = AIProviderManager()
        self.engine = ConversationEngine(provider_manager=self.provider_manager)
        self.tools = ToolRegistry()
        self.tools.register_defaults()
        self.ready = False

    # ---- lifecycle ---------------------------------------------------------
    async def setup_hook(self) -> None:
        db_session.init_engine()
        from ..db import encryption

        if self.settings.encryption_key:
            encryption.configure_encryption(self.settings.encryption_key)

        from ..cogs import (
            AdminCog,
            CustomCommandsCog,
            FunCog,
            GeneralCog,
            MemoryCog,
            ModerationCog,
            ReminderCog,
        )

        for cog in (GeneralCog, AdminCog, MemoryCog, ModerationCog, ReminderCog, CustomCommandsCog, FunCog):
            await self.add_cog(cog(self))
        logger.info("Cogs loaded.")

    async def on_ready(self) -> None:
        if not self.ready:
            self.ready = True
            if self.user:
                BOT_IDS.add(self.user.id)
            logger.info("Rosy is online as %s (id=%s)", self.user, self.user.id if self.user else "?")

    # ---- helpers -----------------------------------------------------------
    async def get_or_create_guild(self, guild_id: int, name: str = "") -> Guild:
        async with db_session.get_sessionmaker()() as s:
            g = await s.get(Guild, guild_id)
            if g is None:
                g = Guild(id=guild_id, name=name, personality=self.settings.ros_personality)
                s.add(g)
                await s.commit()
                await s.refresh(g)
            elif name and g.name != name:
                g.name = name
                await s.commit()
            return g

    async def get_or_create_user(self, user_id: int, name: str = "") -> User:
        async with db_session.get_sessionmaker()() as s:
            u = await s.get(User, user_id)
            if u is None:
                u = User(id=user_id, name=name)
                s.add(u)
                await s.commit()
                await s.refresh(u)
            elif name and u.name != name:
                u.name = name
                await s.commit()
            return u

    async def resolve_personality(self, guild_id: int | None) -> Personality:
        mode = self.settings.ros_personality
        if guild_id is not None:
            g = await self.get_or_create_guild(guild_id)
            mode = g.personality or self.settings.ros_personality
        return Personality(mode)

    # ---- message handling ----------------------------------------------------
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        # Always allow commands.
        await self.process_commands(message)

        if not self.ready:
            return

        # Only respond to the AI-facing content path for non-command messages.
        if message.content.startswith(self.command_prefix):
            return

        try:
            await self._maybe_respond(message)
        except Exception:  # noqa: BLE001
            logger.exception("Error handling message %s", message.id)

    async def _maybe_respond(self, message: discord.Message) -> None:
        guild_id = message.guild.id if message.guild else None
        guild_name = message.guild.name if message.guild else None
        author_id = message.author.id
        content = message.content or ""

        is_mention = self.user is not None and self.user in message.mentions
        is_reply_to_bot = (
            message.reference is not None
            and isinstance(message.reference.resolved, discord.Message)
            and message.reference.resolved.author == self.user
        )
        has_bot_name = BOT_NAME.lower() in content.lower()
        allow_autonomous = self.settings.ros_autonomous_replies
        if guild_id is not None:
            g = await self.get_or_create_guild(guild_id)
            allow_autonomous = bool(g.autonomous_replies)

        decision = self.engine.decide(
            content=content,
            is_mention=is_mention,
            is_reply_to_bot=is_reply_to_bot,
            has_bot_name=has_bot_name,
            allow_autonomous=allow_autonomous,
            channel_id=message.channel.id,
        )
        if not decision.should_reply:
            return

        async with message.channel.typing():
            personality = await self.resolve_personality(guild_id)
            # Adapt personality tone heuristically.
            inferred = personality.infer_mode_from_text(content)
            if inferred:
                personality.set_mode(inferred)

            await self.get_or_create_user(author_id, message.author.display_name)
            async with db_session.get_sessionmaker()() as s:
                mem_service = MemoryService(s)
                memories = await mem_service.list_for_context(
                    user_id=author_id, guild_id=guild_id
                )

            provider = await self.provider_manager.resolve(guild_id=guild_id)

            # Build a small recent-history for context from Discord itself.
            recent_history: list[ChatMessage] = []
            try:
                async for msg in message.channel.history(limit=6, before=message):
                    if msg.author.bot:
                        recent_history.insert(0, ChatMessage(role="assistant", content=msg.clean_content))
                    else:
                        recent_history.insert(0, ChatMessage(role="user", content=f"{msg.author.display_name}: {msg.clean_content}"))
            except Exception:  # noqa: BLE001
                pass

            reply = await self.engine.respond(
                message_text=content,
                author_name=message.author.display_name,
                guild_id=guild_id,
                guild_name=guild_name,
                provider=provider,
                personality=personality,
                memories=memories,
                recent_history=recent_history[-8:] if recent_history else None,
            )
            self.engine.record_participation(message.channel.id)

            await self._safe_send(message.channel, reply, reference=message)

    @staticmethod
    async def _safe_send(channel, text: str, *, reference=None) -> None:
        if len(text) > 2000:
            text = text[:1997] + "..."
        try:
            await channel.send(text, reference=reference)
        except discord.Forbidden:
            logger.warning("Missing permission to send in %s", channel)
