"""Memory cog — remember / forget / list / clear with strict scope isolation."""
from __future__ import annotations

from discord.ext import commands

from rosy.memory.scope import MemoryKey
from rosy.ux import embed, safe_send


class MemoryCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _key(self, ctx, *, scope: str = "auto") -> MemoryKey:
        if ctx.guild is None:
            return MemoryKey(scope="dm", owner_user_id=ctx.author.id)
        if scope == "dm":
            return MemoryKey(scope="dm", owner_user_id=ctx.author.id)
        if scope == "user_in_guild":
            return MemoryKey(scope="user_in_guild", owner_user_id=ctx.author.id, guild_id=ctx.guild.id)
        return MemoryKey(scope="guild", guild_id=ctx.guild.id)

    @commands.command(name="remember")
    async def remember(self, ctx, *, text: str) -> None:
        if not text.strip():
            await safe_send(ctx, "Tell me what to remember.")
            return
        key = self._key(ctx)
        async with self.bot.sessions() as session:
            await self.bot.memory.remember(session, key, text.strip(), kind="fact")
        await safe_send(ctx, embed=embed(description="✅ Got it — I'll remember that.", footer="Rosy"))

    @commands.command(name="memories")
    async def memories(self, ctx) -> None:
        key = self._key(ctx)
        async with self.bot.sessions() as session:
            rows = await self.bot.memory.list_memories(session, key, limit=15)
        if not rows:
            await safe_send(ctx, "I don't have any memories here yet.")
            return
        lines = [f"`{m.id}` · ({m.kind}) {m.content}" for m in rows]
        await safe_send(ctx, embed=embed("Memories", "\n".join(lines), footer="Rosy"))

    @commands.command(name="forget")
    async def forget(self, ctx, memory_id: int) -> None:
        key = self._key(ctx)
        async with self.bot.sessions() as session:
            removed = await self.bot.memory.forget(session, key, memory_id)
        if removed:
            await safe_send(ctx, "✅ Memory forgotten.")
        else:
            await safe_send(ctx, "I couldn't find a memory with that id in your scope.")

    @commands.command(name="clear-memory")
    async def clear_memory(self, ctx) -> None:
        key = self._key(ctx)
        async with self.bot.sessions() as session:
            count = await self.bot.memory.clear(session, key)
        await safe_send(ctx, embed=embed(description=f"🧹 Cleared {count} memories.", footer="Rosy"))
