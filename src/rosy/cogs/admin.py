"""Admin commands: per-guild configuration through Discord.

All commands here require the ``manage_guild`` permission. Configuration is
server-specific and isolated per guild.
"""

import discord
from discord.ext import commands

from ..config import PERSONALITY_MODES
from ..db import session as db_session
from ..db.models import Guild


def is_admin():
    return commands.has_permissions(manage_guild=True)


class AdminCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _guild_row(self, guild_id: int):
        async with db_session.get_sessionmaker()() as s:
            g = await s.get(Guild, guild_id)
            if g is None:
                g = Guild(id=guild_id, personality=self.bot.settings.ros_personality)
                s.add(g)
                await s.commit()
                await s.refresh(g)
            return g, s

    @commands.command(name="setpersonality")
    @is_admin()
    async def set_personality(self, ctx: commands.Context, mode: str) -> None:
        """!setpersonality <mode> — set server personality."""
        if mode not in PERSONALITY_MODES:
            await ctx.send(f"Valid modes: {', '.join(sorted(PERSONALITY_MODES))}")
            return
        g, s = await self._guild_row(ctx.guild.id)
        g.personality = mode
        await s.commit()
        await ctx.send(f"Personality set to **{mode}** for this server.")

    @commands.command(name="autonomous")
    @is_admin()
    async def set_autonomous(self, ctx: commands.Context, on: str) -> None:
        """!autonomous <on|off> — allow Rosy to chat without being mentioned."""
        val = on.lower() in ("on", "true", "yes", "1")
        g, s = await self._guild_row(ctx.guild.id)
        g.autonomous_replies = val
        await s.commit()
        await ctx.send(f"Autonomous replies: **{'ON' if val else 'OFF'}**.")

    @commands.command(name="setmodel")
    @is_admin()
    async def set_model(self, ctx: commands.Context, *, model: str) -> None:
        """!setmodel <model> — set the AI model for this server."""
        g, s = await self._guild_row(ctx.guild.id)
        g.ai_model = model.strip()
        await s.commit()
        await ctx.send(f"AI model set to **{model.strip()}** for this server.")

    @commands.command(name="guildsettings")
    @is_admin()
    async def guild_settings(self, ctx: commands.Context) -> None:
        """!guildsettings — show this server's settings."""
        g, s = await self._guild_row(ctx.guild.id)
        embed = discord.Embed(title=f"Settings for {ctx.guild.name}", color=discord.Color.blurple())
        embed.add_field(name="Personality", value=g.personality, inline=True)
        embed.add_field(name="Autonomous replies", value=str(g.autonomous_replies), inline=True)
        embed.add_field(name="AI model", value=g.ai_model or "default", inline=True)
        embed.add_field(name="Provider", value=g.ai_provider, inline=True)
        await ctx.send(embed=embed)
