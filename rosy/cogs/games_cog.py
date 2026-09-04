"""Games & entertainment cog."""
from __future__ import annotations

from discord.ext import commands

from rosy.ux import embed, safe_send


class GamesCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name="trivia")
    async def trivia(self, ctx) -> None:
        sess = self.bot.games.start_trivia(ctx.channel.id)
        await safe_send(
            ctx,
            embed=embed("🧠 Trivia", f"**{sess.question}**\nType your answer in chat!", footer="Rosy"),
        )

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if message.author.bot:
            return
        result = self.bot.games.try_answer(message.channel.id, message.author.id, message.content)
        if result == "correct":
            await message.channel.send(f"🎉 Correct, {message.author.mention}!")
        elif result == "wrong":
            sess = self.bot.games._active.get(message.channel.id)
            if sess and sess.attempts % 3 == 0:
                await message.channel.send(f"❌ Not quite! Keep guessing ({sess.attempts} attempts so far).")

    @commands.command(name="8ball")
    async def eightball(self, ctx, *, question: str = "") -> None:
        if not question.strip():
            await safe_send(ctx, "Ask me a yes/no question!")
            return
        await safe_send(ctx, embed=embed("🎱 Magic 8-Ball", f"**Q:** {question}\n**A:** {self.bot.games.eightball()}", footer="Rosy"))

    @commands.command(name="roll")
    async def roll(self, ctx, dice: int = 1, sides: int = 6) -> None:
        rolls = self.bot.games.roll(dice, sides)
        await safe_send(ctx, embed=embed("🎲 Dice", f"Rolled `{dice}d{sides}`: **{sum(rolls)}**\n(`{'`, `'.join(map(str, rolls))}`)", footer="Rosy"))
