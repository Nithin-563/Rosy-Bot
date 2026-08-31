"""Moderation cog. All actions respect Discord's own permission model."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class Moderation(commands.Cog, name="Moderation"):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _record(self, guild_id, target, action, reason, actor):
        return self.bot.moderation.record(
            guild_id=guild_id,
            target_user_id=target.id,
            actor_user_id=actor.id if actor else None,
            action=action,
            reason=reason or "",
        )

    @app_commands.command(name="warn", description="Warn a member.")
    @app_commands.default_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "") -> None:
        await self._record(interaction.guild_id, member, "warn", reason, interaction.user)
        await interaction.response.send_message(
            f"⚠️ {member.mention} warned" + (f" — {reason}" if reason else ""), ephemeral=False
        )

    @app_commands.command(name="timeout", description="Timeout a member.")
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int = 60, reason: str = "") -> None:
        if not interaction.guild.me.guild_permissions.moderate_members:
            await interaction.response.send_message("I lack the moderate_members permission.", ephemeral=True)
            return
        await member.timeout(duration=minutes * 60, reason=reason)
        await self._record(interaction.guild_id, member, "timeout", reason or f"{minutes}m", interaction.user)
        await interaction.response.send_message(f"⏱️ Timed out {member} for {minutes} minutes.")

    @app_commands.command(name="kick", description="Kick a member.")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "") -> None:
        if not interaction.author.guild_permissions.kick_members:
            await interaction.response.send_message("You lack permission.", ephemeral=True)
            return
        await member.kick(reason=reason)
        await self._record(interaction.guild_id, member, "kick", reason, interaction.user)
        await interaction.response.send_message(f"Kicked {member}.")

    @app_commands.command(name="ban", description="Ban a member.")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "") -> None:
        if not interaction.author.guild_permissions.ban_members:
            await interaction.response.send_message("You lack permission.", ephemeral=True)
            return
        await member.ban(reason=reason)
        await self._record(interaction.guild_id, member, "ban", reason, interaction.user)
        await interaction.response.send_message(f"Banned {member}.")

    @app_commands.command(name="mod_history", description="Show moderation history for a member.")
    @app_commands.default_permissions(moderate_members=True)
    async def history(self, interaction: discord.Interaction, member: discord.Member) -> None:
        rows = await self.bot.moderation.history(interaction.guild_id, member.id)
        if not rows:
            await interaction.response.send_message(f"No moderation history for {member}.", ephemeral=True)
            return
        lines = [f"- **{r.action}** {r.created_at:%Y-%m-%d %H:%M} — {r.reason or 'no reason'}" for r in rows]
        embed = discord.Embed(title=f"Moderation history: {member}", description="\n".join(lines))
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))