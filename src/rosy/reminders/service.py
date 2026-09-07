"""Reminder scheduler.

Persists reminders in PostgreSQL and fires them when due. Survives restarts by
re-scanning the DB for due reminders at startup and on an interval.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime

from sqlalchemy import select, update

from rosy.models import Reminder

logger = logging.getLogger("rosy.reminders")


class ReminderService:
    def __init__(self, db, poll_seconds: float = 20.0) -> None:
        self.db = db
        self.poll_seconds = poll_seconds
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def add(
        self,
        *,
        channel_id: int,
        user_id: int,
        message: str,
        fire_at: datetime,
        guild_id: int | None = None,
        recurring: str = "",
    ) -> Reminder:
        async with self.db.session() as session:
            r = Reminder(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                message=message,
                fire_at=fire_at.astimezone(UTC),
                recurring=recurring,
            )
            session.add(r)
            await session.commit()
            await session.refresh(r)
            return r

    async def cancel(self, reminder_id: int, user_id: int) -> bool:
        async with self.db.session() as session:
            r = await session.get(Reminder, reminder_id)
            if r is None or r.user_id != user_id:
                return False
            await session.delete(r)
            await session.commit()
            return True

    async def list_for_user(self, user_id: int, limit: int = 25) -> list[Reminder]:
        async with self.db.session() as session:
            res = await session.execute(
                select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.fire_at).limit(limit)
            )
            return list(res.scalars().all())

    async def due(self, now: datetime | None = None) -> list[Reminder]:
        now = now or datetime.now(UTC)
        async with self.db.session() as session:
            res = await session.execute(
                select(Reminder)
                .where(Reminder.fire_at <= now, Reminder.fired == False)  # noqa: E712
                .order_by(Reminder.fire_at)
                .limit(200)
            )
            return list(res.scalars().all())

    async def mark_fired(self, reminder_id: int) -> None:
        async with self.db.session() as session:
            await session.execute(update(Reminder).where(Reminder.id == reminder_id).values(fired=True))
            await session.commit()

    async def _poll(self, fire: Callable[[Reminder], Coroutine]) -> None:
        while not self._stop.is_set():
            try:
                due = await self.due()
                for r in due:
                    try:
                        await fire(r)
                    except Exception:
                        logger.exception("Failed to fire reminder id=%s", r.id)
                    if not r.recurring:
                        await self.mark_fired(r.id)
            except Exception as exc:
                logger.warning("Reminder poll error: %s", exc)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.poll_seconds)
            except TimeoutError:
                pass

    async def start(self, fire: Callable[[Reminder], Coroutine]) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._poll(fire))
            logger.info("Reminder scheduler started")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None