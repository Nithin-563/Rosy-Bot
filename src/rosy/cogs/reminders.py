"""Reminder commands (timezone-aware, persisted in PostgreSQL)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_delta(text: str) -> timedelta | None:
    """Parse strings like '30m', '2h', '1d', '90 seconds'."""
    text = text.strip().lower()
    m = re.match(r"^(\d+)\s*(s|m|h|d|w)?$", text)
    if m:
        num = int(m.group(1))
        unit = m.group(2) or "m"
        return timedelta(seconds=num * _UNIT_SECONDS[unit])
    if text in ("tomorrow", "tomorrow at noon"):
        return timedelta(days=1)
    return None


class Reminders(commands.Cog, name="Reminders"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="remind", description="Set a reminder (e.g. '30m', '2h', 'tomorrow').")
    async def remind(self, interaction: discord.Interaction, duration: str, message: str) -> None:
        delta = parse_delta(duration)
        if delta is None:
            await interaction.response.send_message(
                "I couldn't parse that duration. Use e.g. `30m`, `2h`, `1d`, `tomorrow`.", ephemeral=True
            )
            return
        fire_at = datetime.now(UTC) + delta
        r = await self.bot.reminders.add(
            channel_id=interaction.channel_id,
            user_id=interaction.user.id,
            message=message,
            fire_at=fire_at,
            guild_id=interaction.guild_id,
        )
        await interaction.response.send_message(
            f"✅ Reminder #{r.id} set for <t:{int(fire_at.timestamp())}:R>."
        )

    @app_commands.command(name="reminders", description="List your pending reminders.")
    async def list_reminders(self, interaction: discord.Interaction) -> None:
        rows = await self.bot.reminders.list_for_user(interaction.user.id)
        if not rows:
            await interaction.response.send_message("You have no pending reminders.", ephemeral=True)
            return
        lines = [
            f"`#{r.id}` {r.fire_at:%Y-%m-%d %H:%M} — {r.message[:60]}" for r in rows if not r.fired
        ]
        await interaction.response.send_message(
            embed=discord.Embed(title="Your reminders", description="\n".join(lines) or "none pending"),
            ephemeral=True,
        )

    @app_commands.command(name="cancel_reminder", description="Cancel one of your reminders by id.")
    async def cancel(self, interaction: discord.Interaction, reminder_id: int) -> None:
        ok = await self.bot.reminders.cancel(reminder_id, interaction.user.id)
        await interaction.response.send_message(
            "Reminder cancelled." if ok else "Couldn't find that reminder.", ephemeral=True
        )


async def setup(bot) -> None:
    await bot.add_cog(Reminders(bot))