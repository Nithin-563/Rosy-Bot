"""Moderation commands: warn, timeout, kick, ban, history.

Permissions are enforced by Discord's permission system via decorators. Rosy
never bypasses Discord permissions.
"""

import datetime

import discord
from discord.ext import commands

from ..db import session as db_session
from ..services.moderation import ModerationService

require_mod = commands.has_permissions(manage_messages=True)
require_admin = commands.has_permissions(ban_members=True)


class ModerationCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name="warn")
    @require_mod
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason given") -> None:
        async with db_session.get_sessionmaker()() as s:
            svc = ModerationService(s)
            await svc.record(
                guild_id=ctx.guild.id,
                user_id=member.id,
                moderator_id=ctx.author.id,
                action="warn",
                reason=reason,
            )
            count = await svc.warning_count(guild_id=ctx.guild.id, user_id=member.id)
        await ctx.send(f"⚠️ {member.mention} warned ({count} total). Reason: {reason}")

    @commands.command(name="timeout")
    @require_mod
    async def timeout(self, ctx: commands.Context, member: discord.Member, minutes: int = 10, *, reason: str = "No reason given") -> None:
        try:
            await member.timeout(discord.utils.utcnow() + datetime.timedelta(minutes=minutes), reason=reason)
        except discord.Forbidden:
            await ctx.send("I don't have permission to timeout that member.")
            return
        async with db_session.get_sessionmaker()() as s:
            svc = ModerationService(s)
            await svc.record(guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action="timeout", reason=reason)
        await ctx.send(f"⏱️ {member.mention} timed out for {minutes} min. Reason: {reason}")

    @commands.command(name="kick")
    @require_admin
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason given") -> None:
        try:
            await member.kick(reason=reason)
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick that member.")
            return
        async with db_session.get_sessionmaker()() as s:
            svc = ModerationService(s)
            await svc.record(guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action="kick", reason=reason)
        await ctx.send(f"👢 {member} was kicked. Reason: {reason}")

    @commands.command(name="ban")
    @require_admin
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason given") -> None:
        try:
            await member.ban(reason=reason)
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that member.")
            return
        async with db_session.get_sessionmaker()() as s:
            svc = ModerationService(s)
            await svc.record(guild_id=ctx.guild.id, user_id=member.id, moderator_id=ctx.author.id, action="ban", reason=reason)
        await ctx.send(f"🔨 {member} was banned. Reason: {reason}")

    @commands.command(name="modhistory")
    @require_mod
    async def mod_history(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        async with db_session.get_sessionmaker()() as s:
            svc = ModerationService(s)
            records = await svc.history(guild_id=ctx.guild.id, user_id=member.id if member else None)
        if not records:
            await ctx.send("No moderation records.")
            return
        lines = [f"{r.created_at:%Y-%m-%d %H:%M} — {r.action} on <@{r.user_id}> by <@{r.moderator_id}>: {r.reason}" for r in records]
        await ctx.send("\n".join(lines[:20]))
