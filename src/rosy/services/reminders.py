"""Reminder and scheduled-task service.

Reminders are stored in PostgreSQL so they survive bot restarts. A background
scheduler (APScheduler) polls for due reminders and dispatches them via the
Discord client. This service is timezone-aware (stored tz is honoured).
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Reminder, ScheduledTask

logger = logging.getLogger("rosy.reminders")


class ReminderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        guild_id: Optional[int],
        user_id: int,
        channel_id: int,
        text: str,
        remind_at: datetime,
        timezone: str = "UTC",
        recurring_cron: Optional[str] = None,
    ) -> Reminder:
        rem = Reminder(
            guild_id=guild_id,
            user_id=user_id,
            channel_id=channel_id,
            text=text,
            remind_at=remind_at,
            recurring_cron=recurring_cron,
            timezone=timezone,
        )
        self.session.add(rem)
        await self.session.commit()
        await self.session.refresh(rem)
        return rem

    async def due(self, now: Optional[datetime] = None) -> list[Reminder]:
        now = now or datetime.now(timezone.utc)
        stmt = (
            select(Reminder)
            .where(Reminder.remind_at <= now, Reminder.fired.is_(False))
            .order_by(Reminder.remind_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_fired(self, reminder_id: int) -> None:
        rem = await self.session.get(Reminder, reminder_id)
        if rem is not None:
            rem.fired = True
            await self.session.commit()

    async def reschedule_next(self, reminder: Reminder) -> None:
        """For a recurring reminder, push the next fire time forward by a day."""
        reminder.remind_at = reminder.remind_at + timedelta(days=1)
        reminder.fired = False
        await self.session.commit()

    async def cancel(self, reminder_id: int, user_id: int) -> bool:
        rem = await self.session.get(Reminder, reminder_id)
        if rem is None or rem.user_id != user_id:
            return False
        await self.session.delete(rem)
        await self.session.commit()
        return True

    async def list_for_user(self, user_id: int) -> list[Reminder]:
        stmt = (
            select(Reminder)
            .where(Reminder.user_id == user_id, Reminder.fired.is_(False))
            .order_by(Reminder.remind_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ScheduledTaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_enabled(self) -> list[ScheduledTask]:
        stmt = select(ScheduledTask).where(ScheduledTask.enabled.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
