"""Reminder scheduler, moderation, and guild-settings tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


async def test_reminder_crud(reminders):
    fire_at = datetime.now(timezone.utc) + timedelta(hours=1)
    r = await reminders.add(
        channel_id=111, user_id=1, message="wake up", fire_at=fire_at, guild_id=5
    )
    assert r.id is not None
    # not due yet
    assert await reminders.due() == []
    # wrong user cannot cancel
    assert await reminders.cancel(r.id, 999) is False
    # owner can cancel
    assert await reminders.cancel(r.id, 1) is True


async def test_reminder_due_and_fired(reminders):
    past = datetime.now(timezone.utc) - timedelta(seconds=5)
    r = await reminders.add(
        channel_id=111, user_id=1, message="now", fire_at=past
    )
    due = await reminders.due()
    assert any(x.id == r.id for x in due)
    await reminders.mark_fired(r.id)
    assert await reminders.due() == []


async def test_moderation_record_and_history(moderation):
    await moderation.record(guild_id=1, target_user_id=10, action="warn", reason="spam")
    await moderation.record(guild_id=1, target_user_id=10, action="kick", reason="again")
    await moderation.record(guild_id=2, target_user_id=10, action="ban", reason="other guild")
    hist = await moderation.history(1, target_user_id=10)
    assert len(hist) == 2
    # isolated by guild
    hist2 = await moderation.history(2, target_user_id=10)
    assert len(hist2) == 1


async def test_guild_settings_isolation(guild_settings):
    await guild_settings.update_settings(1, personality_mode="technical")
    s1 = await guild_settings.get_settings(1)
    s2 = await guild_settings.get_settings(2)
    assert s1.personality_mode == "technical"
    assert s2.personality_mode == "friendly"