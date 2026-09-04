"""Reminder commands and the background scheduler.

Reminders persist in PostgreSQL so they survive restarts. A polling loop
dispatches due reminders through the Discord client.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands, tasks

from ..db import session as db_session
from ..services.reminders import ReminderService

logger = logging.getLogger("rosy.reminders")

_PARSE = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}


def _parse_delta(text: str):
    """Parse '30m', '2h', '1d30m' etc into a timedelta."""
    total = 0.0
    num = ""
    for ch in text:
        if ch.isdigit():
            num += ch
        elif ch in _PARSE and num:
            total += int(num) * _PARSE[ch]
            num = ""
        elif ch.isalpha() or ch == " ":
            num = ""
    if not total:
        raise ValueError(f"Could not parse duration: {text}")
    return timedelta(seconds=int(total))


class ReminderCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._runner = asyncio.create_task(self._poll_loop())

    def cog_unload(self) -> None:
        self._runner.cancel()

    def _guild_id(self, ctx):
        return ctx.guild.id if ctx.guild else None

    @commands.command(name="remindme")
    async def remindme(self, ctx: commands.Context, duration: str, *, text: str) -> None:
        """!remindme <duration> <message> — e.g. !remindme 30m take a break."""
        try:
            delta = _parse_delta(duration)
        except ValueError:
            await ctx.send("Usage: `!remindme 30m <message>`. Use s/m/h/d units.")
            return
        remind_at = datetime.now(timezone.utc) + delta
        async with db_session.get_sessionmaker()() as s:
            svc = ReminderService(s)
            rem = await svc.create(
                guild_id=self._guild_id(ctx),
                user_id=ctx.author.id,
                channel_id=ctx.channel.id,
                text=text,
                remind_at=remind_at,
            )
        await ctx.send(f"⏰ I'll remind you in **{duration}**: \"{text}\" (id {rem.id}).")

    @commands.command(name="myreminders")
    async def my_reminders(self, ctx: commands.Context) -> None:
        async with db_session.get_sessionmaker()() as s:
            svc = ReminderService(s)
            rems = await svc.list_for_user(ctx.author.id)
        if not rems:
            await ctx.send("You have no pending reminders.")
            return
        lines = [f"`{r.id}` — {r.remind_at:%Y-%m-%d %H:%M %Z}: {r.text}" for r in rems]
        await ctx.send("\n".join(lines[:20]))

    @commands.command(name="cancelreminder")
    async def cancel_reminder(self, ctx: commands.Context, reminder_id: int) -> None:
        async with db_session.get_sessionmaker()() as s:
            svc = ReminderService(s)
            ok = await svc.cancel(reminder_id, ctx.author.id)
        await ctx.send("Reminder cancelled." if ok else "Reminder not found or not yours.")

    # ---- scheduler loop ------------------------------------------------------
    async def _poll_loop(self) -> None:
        await self.bot.wait_until_ready()
        while True:
            try:
                await self._dispatch_due()
            except asyncio.CancelledError:
                break
            except Exception:  # noqa: BLE001
                logger.exception("Reminder poll error")
            await asyncio.sleep(20)

    async def _dispatch_due(self) -> None:
        async with db_session.get_sessionmaker()() as s:
            svc = ReminderService(s)
            due = await svc.due()
            for rem in due:
                channel = self.bot.get_channel(rem.channel_id)
                if channel is not None:
                    try:
                        await channel.send(f"<@{rem.user_id}> ⏰ **Reminder:** {rem.text}")
                    except Exception:  # noqa: BLE001
                        logger.warning("Could not send reminder %s", rem.id)
                if rem.recurring_cron:
                    await svc.reschedule_next(rem)
                else:
                    await svc.mark_fired(rem.id)
