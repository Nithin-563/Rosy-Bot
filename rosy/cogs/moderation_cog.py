"""Moderation cog — warn/timeout/kick/ban/purge with Discord permission checks.

Rosy never bypasses Discord's own permission system. Actions are executed via
the standard Discord API and every action is recorded to moderation history.
"""
from __future__ import annotations

from datetime import timedelta

import discord
from discord.ext import commands

from rosy.security.permissions import can_moderate, is_moderator
from rosy.ux import embed, safe_send


class ModerationCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _mod(self, ctx, action: str, target, reason: str, *, duration=None) -> None:
        if ctx.guild is None:
            return
        if not can_moderate(ctx.author, target):
            await safe_send(ctx, "You don't have permission to moderate that member.", ephemeral=True)
            return
        if target is not None and (target == ctx.author or target == ctx.guild.me):
            await safe_send(ctx, "You can't do that to yourself or me.", ephemeral=True)
            return
        try:
            if action == "warn":
                pass  # no-op action; recorded below
            elif action == "kick":
                await target.kick(reason=reason)
            elif action == "ban":
                await target.ban(reason=reason)
            elif action == "unban":
                await ctx.guild.unban(discord.Object(id=target.id), reason=reason)
            elif action == "timeout":
                await target.timeout(timedelta(seconds=duration or 300), reason=reason)
        except discord.Forbidden:
            await safe_send(ctx, "I don't have permission to do that.", ephemeral=True)
            return
        except discord.HTTPException as exc:
            await safe_send(ctx, f"Discord error: {exc}", ephemeral=True)
            return

        async with self.bot.sessions() as session:
            rec = await self.bot.moderation.record(
                session,
                guild_id=ctx.guild.id,
                action=action,
                target_user_id=target.id if target else None,
                moderator_id=ctx.author.id,
                reason=reason,
                duration_seconds=duration,
            )
            await session.commit()
            rec_id = rec.id
        await safe_send(ctx, embed=embed(f"🔨 {action.title()}", f"`{reason}`\nrecord `{rec_id}`", footer="Rosy"))

    @commands.command(name="warn")
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason given") -> None:
        if not is_moderator(ctx.author):
            await safe_send(ctx, "You need to be a moderator.", ephemeral=True)
            return
        await self._mod(ctx, "warn", member, reason)

    @commands.command(name="timeout")
    async def timeout(self, ctx, member: discord.Member, minutes: int = 5, *, reason: str = "No reason given") -> None:
        if not is_moderator(ctx.author):
            await safe_send(ctx, "You need to be a moderator.", ephemeral=True)
            return
        await self._mod(ctx, "timeout", member, reason, duration=minutes * 60)

    @commands.command(name="kick")
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason given") -> None:
        if not is_moderator(ctx.author):
            await safe_send(ctx, "You need to be a moderator.", ephemeral=True)
            return
        await self._mod(ctx, "kick", member, reason)

    @commands.command(name="ban")
    async def ban(self, ctx, user: discord.User, *, reason: str = "No reason given") -> None:
        if not is_moderator(ctx.author):
            await safe_send(ctx, "You need to be a moderator.", ephemeral=True)
            return
        await self._mod(ctx, "ban", user, reason)

    @commands.command(name="unban")
    async def unban(self, ctx, user_id: int, *, reason: str = "No reason given") -> None:
        if not is_moderator(ctx.author):
            await safe_send(ctx, "You need to be a moderator.", ephemeral=True)
            return
        await self._mod(ctx, "unban", discord.Object(id=user_id), reason)

    @commands.command(name="purge")
    async def purge(self, ctx, amount: int = 10) -> None:
        if not is_moderator(ctx.author):
            await safe_send(ctx, "You need to be a moderator.", ephemeral=True)
            return
        amount = max(1, min(amount, 100))
        deleted = await ctx.channel.purge(limit=amount)
        await safe_send(ctx, f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)

    @commands.command(name="warnings")
    async def warnings(self, ctx, member: discord.Member) -> None:
        if not is_moderator(ctx.author):
            await safe_send(ctx, "You need to be a moderator.", ephemeral=True)
            return
        async with self.bot.sessions() as session:
            count = await self.bot.moderation.warning_count(session, ctx.guild.id, member.id)
            history = await self.bot.moderation.history(session, ctx.guild.id, limit=10)
        lines = [f"{h.action} · <@{h.target_user_id}> · {h.reason}" for h in history]
        text = f"**Warnings:** {count}\n\n" + ("\n".join(lines) if lines else "No recent history.")
        await safe_send(ctx, embed=embed("Moderation", text, footer="Rosy"))
