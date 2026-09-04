"""Memory commands: remember / forget / whatdoyouremember / clear."""

import discord
from discord.ext import commands

from ..db import session as db_session
from ..memory.service import MemoryService


class MemoryCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _guild_id(self, ctx: commands.Context):
        return ctx.guild.id if ctx.guild else None

    @commands.command(name="remember", aliases=["remindme_remember", "memorize"])
    async def remember(self, ctx: commands.Context, *, content: str) -> None:
        """!remember <key> = <value>  — store a memory about you."""
        if "=" not in content:
            await ctx.send("Format: `!remember <key> = <value>`")
            return
        key, value = content.split("=", 1)
        async with db_session.get_sessionmaker()() as s:
            svc = MemoryService(s)
            await svc.remember(
                user_id=ctx.author.id,
                guild_id=self._guild_id(ctx),
                key=key.strip(),
                value=value.strip(),
                memory_type="preference" if "prefer" in key.lower() else "fact",
                source="user_command",
            )
        await ctx.send(f"Okay, I'll remember: **{key.strip()}**.")

    @commands.command(name="forget", aliases=["unremember"])
    async def forget(self, ctx: commands.Context, *, key: str) -> None:
        """!forget <key> — delete a memory."""
        async with db_session.get_sessionmaker()() as s:
            svc = MemoryService(s)
            ok = await svc.forget(
                user_id=ctx.author.id, guild_id=self._guild_id(ctx), key=key.strip()
            )
        await ctx.send("Forgotten." if ok else "I don't have that memory.")

    @commands.command(name="whatdoyouremember", aliases=["memories", "mymemories"])
    async def whatdoyouremember(self, ctx: commands.Context) -> None:
        """!whatdoyouremember — list memories about you."""
        async with db_session.get_sessionmaker()() as s:
            svc = MemoryService(s)
            mems = await svc.list_user(
                user_id=ctx.author.id, guild_id=self._guild_id(ctx)
            )
        if not mems:
            await ctx.send("I don't have any memories about you yet.")
            return
        lines = [f"**{m.key}** — {m.value} ({m.memory_type})" for m in mems]
        await ctx.send("\n".join(lines[:20]))

    @commands.command(name="clearmymemories")
    async def clear(self, ctx: commands.Context) -> None:
        """!clearmymemories — clear memories about you."""
        async with db_session.get_sessionmaker()() as s:
            svc = MemoryService(s)
            count = await svc.clear(
                user_id=ctx.author.id, guild_id=self._guild_id(ctx)
            )
        await ctx.send(f"Cleared {count} memory/ies about you.")
