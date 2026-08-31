"""Games & entertainment cog (modular: trivia, 8-ball, dice, guess)."""

from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

TRIVIA = [
    ("What is the capital of France?", "Paris"),
    ("How many planets are in our solar system?", "8"),
    ("What language is Python written in primarily?", "C"),
    ("What does HTTP stand for?", "HyperText Transfer Protocol"),
    ("What is the largest ocean on Earth?", "Pacific"),
]


class Games(commands.Cog, name="Games"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question.")
    async def eight_ball(self, interaction: discord.Interaction, question: str) -> None:
        answers = [
            "It is certain.", "Without a doubt.", "Yes — definitely.",
            "Most likely.", "Outlook good.", "Reply hazy, try again.",
            "Ask again later.", "Better not tell you now.", "Cannot predict now.",
            "Don't count on it.", "My sources say no.", "Very doubtful.",
        ]
        await interaction.response.send_message(f"🎱 **Q:** {question}\n**A:** {random.choice(answers)}")

    @app_commands.command(name="dice", description="Roll one or more dice (e.g. 2d6).")
    async def dice(self, interaction: discord.Interaction, dice: str = "1d6") -> None:
        try:
            count, sides = dice.lower().split("d")
            count, sides = int(count), int(sides)
            if count < 1 or count > 10 or sides < 2 or sides > 1000:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("Use format like `2d6`.", ephemeral=True)
            return
        rolls = [random.randint(1, sides) for _ in range(count)]
        await interaction.response.send_message(f"🎲 {dice}: {rolls} (total {sum(rolls)})")

    @app_commands.command(name="trivia", description="Answer a random trivia question.")
    async def trivia(self, interaction: discord.Interaction) -> None:
        question, answer = random.choice(TRIVIA)
        self.bot.trivia_answers = getattr(self.bot, "trivia_answers", {})
        self.bot.trivia_answers[interaction.channel_id] = answer.lower()
        await interaction.response.send_message(f"🧠 **Trivia:** {question}\nReply with your answer.")

    @app_commands.command(name="guess", description="Play a quick guessing game (1-100).")
    async def guess(self, interaction: discord.Interaction) -> None:
        number = random.randint(1, 100)
        if not hasattr(self.bot, "guess_games"):
            self.bot.guess_games = {}
        self.bot.guess_games[interaction.channel_id] = number
        await interaction.response.send_message(
            "🎯 I've picked a number between 1 and 100. Reply with `guess <number>` to try!"
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        content = message.content.lower().strip()
        if content.startswith("guess ") and hasattr(self.bot, "guess_games"):
            try:
                num = int(content.split()[1])
            except (IndexError, ValueError):
                return
            target = self.bot.guess_games.get(message.channel.id)
            if target is None:
                return
            if num == target:
                del self.bot.guess_games[message.channel.id]
                await message.reply(f"🎉 Correct! The number was **{num}**.")
            else:
                await message.reply("Too high! 📈" if num > target else "Too low! 📉")
        # trivia answers
        if content and getattr(self.bot, "trivia_answers", {}).get(message.channel.id) == content:
            del self.bot.trivia_answers[message.channel.id]
            await message.reply("✅ Correct! Well done.")


async def setup(bot) -> None:
    await bot.add_cog(Games(bot))