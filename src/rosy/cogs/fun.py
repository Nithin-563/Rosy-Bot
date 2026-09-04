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

JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "I told my computer I needed a break. Now it won't stop sending me KitKat ads.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "There are only 10 kinds of people: those who understand binary and those who don't.",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
]

COMPLIMENTS = [
    "You're absolutely radiant today! ✨",
    "You have a brilliant mind, honestly.",
    "The world is better because you're in it. 💜",
    "You're doing amazing — keep going!",
    "Your energy is contagious in the best way.",
]

ADVICE = [
    "Drink some water and take a short break — future you will thank you. 💧",
    "Break big problems into small steps; you'll get there.",
    "Kindness is free, sprinkle it around.",
    "Back up your important files today. Future you says thanks.",
]

TOPICS = [
    "If you could have dinner with any fictional character, who would it be?",
    "What's a skill you wish you could learn instantly?",
    "What's the best advice you've ever received?",
    "If you could teleport anywhere right now, where would you go?",
]


def _rps_winner(you: str, me: str) -> int:
    rules = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    if you == me:
        return 0
    return 1 if rules[you] == me else -1


class Fun(commands.Cog, name="Fun"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="echo", description="Make Rosy repeat something.")
    async def echo(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.send_message(text[:1900])

    @app_commands.command(name="insult", description="A (friendly) roast.")
    async def insult(self, interaction: discord.Interaction, member: discord.Member) -> None:
        await interaction.response.send_message(f"{member.mention} {random_insult()}")

    @app_commands.command(name="joke", description="Tell a random programming joke.")
    async def joke(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"😄 {random.choice(JOKES)}")

    @app_commands.command(name="compliment", description="Get a nice compliment.")
    async def compliment(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"💜 {random.choice(COMPLIMENTS)}")

    @app_commands.command(name="advice", description="Get a small piece of advice.")
    async def advice(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"📌 {random.choice(ADVICE)}")

    @app_commands.command(name="topic", description="Suggest a conversation topic.")
    async def topic(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🗣️ {random.choice(TOPICS)}")

    @app_commands.command(name="rps", description="Play Rock-Paper-Scissors.")
    async def rps(self, interaction: discord.Interaction, choice: str) -> None:
        you = choice.lower()
        if you not in ("rock", "paper", "scissors"):
            await interaction.response.send_message("Choose `rock`, `paper`, or `scissors`.", ephemeral=True)
            return
        me = random.choice(["rock", "paper", "scissors"])
        outcome = _rps_winner(you, me)
        text = f"✊🖐️✌️ You: **{you}**  Me: **{me}**\n"
        if outcome == 0:
            text += "It's a tie! 🤝"
        elif outcome == 1:
            text += "You win! 🎉"
        else:
            text += "I win! 😎"
        await interaction.response.send_message(text)

    @app_commands.command(name="stats", description="Show Rosy's uptime and activity stats.")
    async def stats(self, interaction: discord.Interaction) -> None:
        s = self.bot.stats
        import time

        uptime = int(time.monotonic() - s["started"])
        embed = discord.Embed(
            title="Rosy stats",
            description="Powered by Wisee Models · MakeIt Company 💜",
            color=discord.Color.green(),
        )
        embed.add_field(name="Uptime", value=f"{uptime // 3600}h {(uptime % 3600) // 60}m")
        embed.add_field(name="Commands", value=str(s["commands"]), inline=True)
        embed.add_field(name="Messages seen", value=str(s["messages"]), inline=True)
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Version", value="2.0.0", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check Rosy's latency.")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🏓 Pong! {round(self.bot.latency * 1000)}ms")


def random_insult() -> str:

    return random.choice(INSULTS)


async def setup(bot) -> None:
    await bot.add_cog(Fun(bot))