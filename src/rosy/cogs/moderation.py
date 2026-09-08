"""Moderation cog. All actions respect Discord's own permission model."""

from __future__ import annotations

import discord
from datetime import timedelta
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
        await interaction.response.defer()
        await self._record(interaction.guild_id, member, "warn", reason, interaction.user)
        await interaction.followup.send(
            f"⚠️ {member.mention} warned" + (f" — {reason}" if reason else ""), ephemeral=False
        )

    @app_commands.command(name="timeout", description="Timeout a member.")
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int = 60, reason: str = "") -> None:
        await interaction.response.defer()
        if minutes < 1 or minutes > 40320:
            await interaction.followup.send("Timeout must be between 1 and 40320 minutes.", ephemeral=True)
            return
        me = interaction.guild.me
        if not me or not me.guild_permissions.moderate_members:
            await interaction.followup.send("I lack the moderate_members permission.", ephemeral=True)
            return
        if member == interaction.user or (me.top_role <= member.top_role):
            await interaction.followup.send("I cannot timeout that member because of Discord role hierarchy.", ephemeral=True)
            return
        await member.timeout(duration=timedelta(minutes=minutes), reason=reason)
        await self._record(interaction.guild_id, member, "timeout", reason or f"{minutes}m", interaction.user)
        await interaction.followup.send(f"⏱️ Timed out {member} for {minutes} minutes.")

    @app_commands.command(name="kick", description="Kick a member.")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "") -> None:
        await interaction.response.defer()
        if not interaction.user.guild_permissions.kick_members:
            await interaction.followup.send("You lack permission.", ephemeral=True)
            return
        await member.kick(reason=reason)
        await self._record(interaction.guild_id, member, "kick", reason, interaction.user)
        await interaction.followup.send(f"Kicked {member}.")

    @app_commands.command(name="ban", description="Ban a member.")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "") -> None:
        await interaction.response.defer()
        if not interaction.user.guild_permissions.ban_members:
            await interaction.followup.send("You lack permission.", ephemeral=True)
            return
        await member.ban(reason=reason)
        await self._record(interaction.guild_id, member, "ban", reason, interaction.user)
        await interaction.followup.send(f"Banned {member}.")

    @app_commands.command(name="mod_history", description="Show moderation history for a member.")
    @app_commands.default_permissions(moderate_members=True)
    async def history(self, interaction: discord.Interaction, member: discord.Member) -> None:
        await interaction.response.defer()
        rows = await self.bot.moderation.history(interaction.guild_id, member.id)
        if not rows:
            await interaction.followup.send(f"No moderation history for {member}.", ephemeral=True)
            return
        lines = [f"- **{r.action}** {r.created_at:%Y-%m-%d %H:%M} — {r.reason or 'no reason'}" for r in rows]
        embed = discord.Embed(title=f"Moderation history: {member}", description="\n".join(lines))
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(Moderation(bot))
