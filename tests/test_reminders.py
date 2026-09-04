"""Reminder service tests."""

from datetime import datetime, timedelta, timezone

import pytest

from rosy.services.reminders import ReminderService


@pytest.mark.asyncio
async def test_create_and_due(session_factory):
    async with session_factory() as s:
        svc = ReminderService(s)
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        await svc.create(guild_id=10, user_id=1, channel_id=5, text="hello",
                         remind_at=past, timezone="UTC")
        await svc.create(guild_id=10, user_id=1, channel_id=5, text="later",
                         remind_at=future, timezone="UTC")
        due = await svc.due()
        assert len(due) == 1
        assert due[0].text == "hello"


@pytest.mark.asyncio
async def test_mark_fired_and_cancel(session_factory):
    async with session_factory() as s:
        svc = ReminderService(s)
        past = datetime.now(timezone.utc) - timedelta(seconds=30)
        rem = await svc.create(guild_id=10, user_id=1, channel_id=5, text="x",
                               remind_at=past, timezone="UTC")
        await svc.mark_fired(rem.id)
        assert await svc.due() == []

        rem2 = await svc.create(guild_id=10, user_id=1, channel_id=5, text="y",
                                remind_at=past, timezone="UTC")
        assert await svc.cancel(rem2.id, user_id=1) is True
        # Only the owner can cancel.
        assert await svc.cancel(rem2.id, user_id=999) is False
