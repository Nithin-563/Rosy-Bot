"""Fun / entertainment + stats commands."""

from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

INSULTS = [
    "You're like a cloud — when you disappear, it's a beautiful day.",
    "I'd agree with you, but then we'd both be wrong.",
    "You're not stupid; you're just unlucky at thinking.",
    "I'd give you a piece of my mind, but I don't think you'd use it.",
]


class Fun(commands.Cog, name="Fun"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="echo", description="Make Rosy repeat something.")
    async def echo(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.send_message(text[:1900])

    @app_commands.command(name="insult", description="A (friendly) roast.")
    async def insult(self, interaction: discord.Interaction, member: discord.Member) -> None:
        await interaction.response.send_message(f"{member.mention} {random_insult()}")

    @app_commands.command(name="stats", description="Show Rosy's uptime and activity stats.")
    async def stats(self, interaction: discord.Interaction) -> None:
        s = self.bot.stats
        import time

        uptime = int(time.monotonic() - s["started"])
        embed = discord.Embed(title="Rosy stats", color=discord.Color.green())
        embed.add_field(name="Uptime", value=f"{uptime // 3600}h {(uptime % 3600) // 60}m")
        embed.add_field(name="Commands", value=str(s["commands"]), inline=True)
        embed.add_field(name="Messages seen", value=str(s["messages"]), inline=True)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Version", value="0.1.0", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check Rosy's latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🏓 Pong! {round(self.bot.latency * 1000)}ms")


def random_insult() -> str:

    return random.choice(INSULTS)


async def setup(bot) -> None:
    await bot.add_cog(Fun(bot))