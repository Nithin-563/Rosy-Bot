"""Entertainment / games commands.

Modular design: each game is a small command so more can be added later.
Deterministic where possible (dice, 8-ball) rather than asking the LLM.
"""

import random

import discord
from discord.ext import commands

_BALL = [
    "It is certain.", "Without a doubt.", "Yes, definitely.", "Most likely.",
    "Outlook good.", "Reply hazy, try again.", "Ask again later.", "Cannot predict now.",
    "Don't count on it.", "My reply is no.", "Very doubtful.",
]

_TRIVIA = [
    ("What is the capital of France?", "Paris"),
    ("How many planets are in our solar system?", "8"),
    ("What language does a Raspberry Pi run best with for this bot?", "Python"),
    ("What is 7 * 8?", "56"),
    ("Which planet is known as the Red Planet?", "Mars"),
    ("What year did humans first land on the Moon?", "1969"),
]


class FunCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name="roll", aliases=["dice"])
    async def roll(self, ctx: commands.Context, sides: int = 6) -> None:
        if not (1 <= sides <= 1000000):
            await ctx.send("Sides must be between 1 and 1,000,000.")
            return
        await ctx.send(f"🎲 You rolled a **{random.randint(1, sides)}** (d{sides}).")

    @commands.command(name="8ball", aliases=["eightball"])
    async def eightball(self, ctx: commands.Context, *, question: str) -> None:
        await ctx.send(f"🎱 {random.choice(_BALL)}")

    @commands.command(name="flip")
    async def flip(self, ctx: commands.Context) -> None:
        await ctx.send("🪙 " + ("Heads!" if random.random() < 0.5 else "Tails!"))

    @commands.command(name="trivia")
    async def trivia(self, ctx: commands.Context) -> None:
        question, answer = random.choice(_TRIVIA)
        await ctx.send(f"🤔 **Trivia:** {question}\nReply with `!answer <your answer>`. The answer is a single word/number.")
        self.bot._trivia_answer = answer.lower()

    @commands.command(name="answer")
    async def answer(self, ctx: commands.Context, *, guess: str) -> None:
        correct = getattr(self.bot, "_trivia_answer", None)
        if correct is None:
            await ctx.send("No active trivia question. Try `!trivia`.")
            return
        if guess.strip().lower() == correct:
            await ctx.send(f"✅ Correct, {ctx.author.mention}! 🎉")
            self.bot._trivia_answer = None
        else:
            await ctx.send("❌ Nope, try again!")
