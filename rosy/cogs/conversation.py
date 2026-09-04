"""Conversation cog — decides whether to reply and drives the AI engine."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from rosy.ai.base import Message, ProviderError
from rosy.conversation.decision import DecisionInput
from rosy.memory.scope import MemoryKey
from rosy.ux import embed, safe_send

log = logging.getLogger(__name__)


class ConversationCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._last_participation: dict[int, datetime] = {}

    def _key_for(self, ctx) -> MemoryKey:
        if ctx.guild is None:
            return MemoryKey(scope="dm", owner_user_id=ctx.author.id)
        return MemoryKey(scope="guild", guild_id=ctx.guild.id)

    async def _guild_pref(self, ctx) -> dict:
        prefs = {"autonomous": False, "personality": None}
        if ctx.guild is None:
            return prefs
        try:
            from rosy.db.models import GuildPreference
            async with self.bot.sessions() as session:
                gp = await session.get(GuildPreference, ctx.guild.id)
                if gp is not None:
                    prefs["autonomous"] = gp.autonomous_replies
                    prefs["personality"] = gp.personality_mode or None
        except Exception:  # noqa: BLE001
            log.exception("Could not read guild preferences")
        return prefs

    async def _maybe_respond(self, ctx) -> None:
        content = ctx.message.content or ""
        # Ignore commands starting with the prefix.
        if content.startswith(self.bot.settings.discord_command_prefix):
            return
        if not content.strip():
            return

        is_dm = ctx.guild is None
        mentions_bot = self.bot.user in (ctx.message.mentions or [])
        is_reply = ctx.message.reference is not None
        is_reply_to_bot = False
        if is_reply and ctx.message.reference.resolved is not None:
            ref = ctx.message.reference.resolved
            is_reply_to_bot = getattr(ref, "author", None) == self.bot.user

        guild_id = ctx.guild.id if ctx.guild else None
        prefs = await self._guild_pref(ctx)
        last_part = self._last_participation.get(guild_id or ctx.author.id)

        rate_key = f"conv:{guild_id or ctx.author.id}"
        decision = self.bot.engine_ai.decider.decide(
            DecisionInput(
                is_dm=is_dm,
                mentions_bot=mentions_bot,
                is_reply_to_bot=is_reply_to_bot,
                content=content,
                autonomous=prefs["autonomous"],
                cooldown_active=(
                    last_part is not None
                    and (datetime.now(timezone.utc) - last_part).total_seconds() < 6
                ),
                rate_limited=not self.bot.rate_limiter.hit(rate_key),
            )
        )
        if not decision.should_reply:
            return

        # Strip the mention prefix if present.
        clean = content
        if mentions_bot:
            clean = clean.replace(f"<@{self.bot.user.id}>", "").strip()
            clean = clean.replace(f"<@!{self.bot.user.id}>", "").strip()

        await self._respond(ctx, clean)

    async def _respond(self, ctx, text: str) -> None:
        if not text:
            text = "Hi!"
        self._last_participation[ctx.guild.id if ctx.guild else ctx.author.id] = datetime.now(timezone.utc)

        key = self._key_for(ctx)
        user_id = ctx.author.id
        guild_id = ctx.guild.id if ctx.guild else None
        channel_id = ctx.channel.id

        prefs = await self._guild_pref(ctx)

        async with self.bot.sessions() as session:
            memories = await self.bot.memory.top_memories(session, key)
        history = await self.bot.conversations.to_messages(
            guild_id=guild_id, channel_id=channel_id, user_id=user_id, limit=10
        )
        summary = await self.bot.conversations.summary(
            guild_id=guild_id, channel_id=channel_id, user_id=user_id
        )

        messages = history + [Message(role="user", content=text)]
        tool_context = {
            "user_id": user_id,
            "guild_id": guild_id,
            "session_factory": self.bot.sessions,
            "scope": "guild" if guild_id else "dm",
        }

        try:
            await self.bot.conversations.append(
                guild_id=guild_id, channel_id=channel_id, user_id=user_id,
                role="user", content=text, author_id=user_id,
            )
            response = await self.bot.engine_ai.respond(
                recent_messages=messages,
                memories=memories,
                summary=summary,
                guild_id=guild_id,
                user_id=user_id,
                mode=prefs["personality"],
                tool_context=tool_context,
            )
            reply_text = response.content.strip()
            await self.bot.conversations.append(
                guild_id=guild_id, channel_id=channel_id, user_id=user_id,
                role="assistant", content=reply_text,
            )
        except ProviderError as exc:
            log.warning("AI response failed: %s", exc)
            reply_text = "Sorry, I couldn't reach my AI backend right now. Please try again in a moment."
        except Exception:  # noqa: BLE001
            log.exception("Conversation handler failed")
            reply_text = "Something went wrong on my end. Try again in a moment."

        await safe_send(ctx, embed=embed(description=reply_text, footer="Rosy"))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if self.bot.user is None:
            return
        ctx = await self.bot.get_context(message)
        if ctx.command is not None:
            return
        try:
            await self._maybe_respond(ctx)
        except Exception:  # noqa: BLE001
            log.exception("on_message handler failed")
