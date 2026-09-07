"""Timezone-aware reminder scheduling backed by PostgreSQL (survives restarts)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rosy.db.models import Reminder

log = logging.getLogger(__name__)


def parse_reminder_time(text: str, now: datetime | None = None) -> datetime | None:
    """Parse natural-language relative reminders. Supports '30m','2h','1d', and
    plain numbers in minutes ('30'). Returns None if unparseable."""
    from rosy.memory.scope import parse_duration

    now = now or datetime.now(timezone.utc)
    text = text.strip().lower()
    # absolute HH:MM today/tomorrow
    if ":" in text:
        try:
            hh, mm = text.split(":")
            t = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            if t <= now:
                t += timedelta(days=1)
            return t
        except ValueError:
            return None
    delta = parse_duration(text)
    if delta is not None:
        return now + delta
    # bare number => minutes
    try:
        mins = float(text)
        return now + timedelta(minutes=mins)
    except ValueError:
        return None


class ReminderService:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions
        self._task: asyncio.Task | None = None
        self._senders: dict[str, object] = {}

    def set_sender(self, name: str, send: object) -> None:
        """Register an async callable used to deliver reminders (by user id)."""
        self._senders[name] = send

    async def create(
        self,
        user_id: int,
        message: str,
        due_at: datetime,
        *,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        recurrence: str = "",
    ) -> Reminder:
        rem = Reminder(
            user_id=user_id, guild_id=guild_id, channel_id=channel_id,
            message=message, due_at=due_at, recurrence=recurrence,
        )
        async with self.sessions() as session:
            session.add(rem)
            await session.commit()
            await session.refresh(rem)
        return rem

    async def due(self, limit: int = 50) -> list[Reminder]:
        now = datetime.now(timezone.utc)
        async with self.sessions() as session:
            res = await session.execute(
                select(Reminder)
                .where(Reminder.due_at <= now, Reminder.fired.is_(False))
                .order_by(Reminder.due_at)
                .limit(limit)
            )
            return list(res.scalars().all())

    async def mark_fired(self, reminder_id: int, *, recurrence_next: Optional[datetime] = None) -> None:
        async with self.sessions() as session:
            rem = await session.get(Reminder, reminder_id)
            if rem is None:
                return
            rem.times_fired += 1
            if recurrence_next:
                rem.due_at = recurrence_next
                rem.fired = False
            else:
                rem.fired = True
            await session.commit()

    def _next_recurrence(self, recurrence: str, base: datetime) -> Optional[datetime]:
        """Very small recurrence interpreter: 'daily'|'hourly'|'weekly'."""
        key = recurrence.strip().upper()
        if key == "DAILY":
            return base + timedelta(days=1)
        if key == "HOURLY":
            return base + timedelta(hours=1)
        if key == "WEEKLY":
            return base + timedelta(weeks=1)
        if key == "MINUTELY":
            return base + timedelta(minutes=1)
        return None

    async def tick(self) -> int:
        """Fire all due reminders. Returns how many were delivered."""
        delivered = 0
        for rem in await self.due():
            send = self._senders.get(str(rem.user_id))
            try:
                if send is not None:
                    await send(rem)
                delivered += 1
            except Exception:  # noqa: BLE001
                log.exception("Failed to deliver reminder %s", rem.id)
                # Do not mark fired so it retries next tick.
                continue
            next_due = self._next_recurrence(rem.recurrence, rem.due_at)
            await self.mark_fired(rem.id, recurrence_next=next_due)
        return delivered

    async def loop(self, interval_seconds: int = 20) -> None:
        """Background loop. Call once from the bot's startup task group."""
        while True:
            try:
                await self.tick()
            except Exception:  # noqa: BLE001
                log.exception("Reminder tick failed")
            await asyncio.sleep(interval_seconds)
