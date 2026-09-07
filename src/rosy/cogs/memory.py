"""Memory commands: remember, forget, show, clear. Guild/user isolation enforced."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from rosy.models import MemoryScope


class Memory(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _scopes(self, interaction: discord.Interaction) -> tuple[MemoryScope, int | None, int | None]:
        if interaction.guild is None:
            return MemoryScope.dm, None, interaction.user.id
        return MemoryScope.user_in_guild, interaction.guild.id, interaction.user.id

    @app_commands.command(name="remember", description="Ask Rosy to remember something.")
    async def remember(self, interaction: discord.Interaction, content: str) -> None:
        scope, guild_id, user_id = self._scopes(interaction)
        await self.bot.memory.remember(
            content, scope=scope, guild_id=guild_id, user_id=user_id, source="user", importance=0.6
        )
        await interaction.response.send_message("I've remembered that. 🧠", ephemeral=True)

    @app_commands.command(name="forget", description="Ask Rosy to forget something specific.")
    async def forget(self, interaction: discord.Interaction, content: str) -> None:
        scope, guild_id, user_id = self._scopes(interaction)
        ok = await self.bot.memory.forget(content, scope=scope, guild_id=guild_id, user_id=user_id)
        await interaction.response.send_message(
            "Forgotten." if ok else "I didn't have that memorized.",
            ephemeral=True,
        )

    @app_commands.command(name="memories", description="Show what Rosy remembers for you.")
    async def show(self, interaction: discord.Interaction) -> None:
        scope, guild_id, user_id = self._scopes(interaction)
        memories = await self.bot.memory.recall(scope=scope, guild_id=guild_id, user_id=user_id, limit=25)
        if not memories:
            await interaction.response.send_message("I don't have any memories here yet.", ephemeral=True)
            return
        lines = [f"- {m.content}" for m in memories]
        embed = discord.Embed(title="Your memories", description="\n".join(lines))
        embed.set_footer(text=f"{len(memories)} memories")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clear_memories", description="Clear all your permitted memories here.")
    async def clear(self, interaction: discord.Interaction) -> None:
        scope, guild_id, user_id = self._scopes(interaction)
        n = await self.bot.memory.clear_scope(scope=scope, guild_id=guild_id, user_id=user_id)
        await interaction.response.send_message(f"Cleared {n} memories.", ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(Memory(bot))