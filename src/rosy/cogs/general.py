"""General commands: ping, help, info."""

import discord
from discord.ext import commands


class GeneralCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! Latency: {latency}ms")

    @commands.command(name="info")
    async def info(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="Rosy",
            description=(
                "A modular, extensible AI Discord bot.\n"
                "Try `!help` to see commands, or just talk to me."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(name="AI Provider", value=self.bot.settings.default_provider, inline=True)
        embed.add_field(name="Model", value=self.bot.settings.default_model, inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="about")
    async def about(self, ctx: commands.Context) -> None:
        await ctx.send("I'm Rosy — your friendly AI companion. I can chat, remember things, remind you, moderate, and more. Type `!help` to see what I can do.")
