"""Reminders cog — set, list, and cancel reminders."""
from __future__ import annotations

from datetime import datetime, timezone

from discord.ext import commands

from rosy.reminders.service import parse_reminder_time
from rosy.ux import embed, safe_send


class RemindersCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name="remind")
    async def remind(self, ctx, when: str, *, message: str = "Time's up! ⏰") -> None:
        due = parse_reminder_time(when)
        if due is None:
            await safe_send(ctx, "I couldn't parse that time. Try `!remind 30m ...` or `!remind 14:30 ...`.")
            return
        guild_id = ctx.guild.id if ctx.guild else None
        channel_id = ctx.channel.id
        rem = await self.bot.reminders.create(
            ctx.author.id, message, due, guild_id=guild_id, channel_id=channel_id
        )
        await safe_send(
            ctx,
            embed=embed(
                "⏰ Reminder set",
                f"`{message}` — {due.strftime('%Y-%m-%d %H:%M UTC')} (id `{rem.id}`)",
                footer="Rosy",
            ),
        )

    @commands.command(name="reminders")
    async def reminders(self, ctx) -> None:
        async with self.bot.sessions() as session:
            from sqlalchemy import select
            from rosy.db.models import Reminder
            res = await session.execute(
                select(Reminder).where(Reminder.user_id == ctx.author.id, Reminder.fired.is_(False))
                .order_by(Reminder.due_at)
            )
            rows = list(res.scalars().all())
        if not rows:
            await safe_send(ctx, "You have no pending reminders.")
            return
        lines = [f"`{r.id}` · {r.due_at.strftime('%Y-%m-%d %H:%M')} UTC · {r.message}" for r in rows[:20]]
        await safe_send(ctx, embed=embed("Your reminders", "\n".join(lines), footer="Rosy"))

    @commands.command(name="cancel-reminder")
    async def cancel_reminder(self, ctx, reminder_id: int) -> None:
        from rosy.db.models import Reminder
        from sqlalchemy import delete
        async with self.bot.sessions() as session:
            res = await session.execute(
                delete(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == ctx.author.id)
            )
            removed = res.rowcount
        await safe_send(ctx, "✅ Reminder cancelled." if removed else "No matching reminder found.")
