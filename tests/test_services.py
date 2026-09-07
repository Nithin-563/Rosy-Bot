"""Reminder, moderation, games, custom-command service tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from rosy.custom_commands.service import CustomCommandService, parse_role_ids
from rosy.games.service import GamesService
from rosy.moderation.service import ModConfig, ModerationService
from rosy.reminders.service import ReminderService, parse_reminder_time

NOW = datetime.now(timezone.utc)


# --- reminders ---
def test_parse_relative_times():
    assert parse_reminder_time("30m", NOW) - NOW == timedelta(minutes=30)
    assert parse_reminder_time("2h", NOW) - NOW == timedelta(hours=2)
    assert parse_reminder_time("45", NOW) - NOW == timedelta(minutes=45)
    assert parse_reminder_time("gibberish", NOW) is None


def test_recurrence_next():
    svc = ReminderService.__new__(ReminderService)  # no DB needed for this helper
    base = NOW
    assert svc._next_recurrence("DAILY", base) == base + timedelta(days=1)
    assert svc._next_recurrence("WEEKLY", base) == base + timedelta(weeks=1)
    assert svc._next_recurrence("", base) is None


# --- moderation ---
def test_mod_blocked_words():
    m = ModerationService(ModConfig(blocked_words=["spam", "badword"]))
    assert m.check_blocked_words("this is spam content") == ["spam"]
    assert m.check_blocked_words("clean message") == []


def test_mod_flood():
    m = ModerationService(ModConfig(anti_flood_max_messages=3))
    now = 1000.0
    assert m.check_flood(1, 1, now) is False
    assert m.check_flood(1, 1, now) is False
    assert m.check_flood(1, 1, now) is False
    assert m.check_flood(1, 1, now) is True


def test_mod_blocked_urls():
    m = ModerationService(ModConfig(blocked_urls=True))
    assert m.check_url("visit https://evil.example") is True
    m2 = ModerationService(ModConfig(blocked_urls=False))
    assert m2.check_url("https://x.com") is False


# --- games ---
def test_games_roll_and_eightball():
    g = GamesService()
    rolls = g.roll(3, 6)
    assert len(rolls) == 3 and all(1 <= r <= 6 for r in rolls)
    answer = g.eightball()
    assert isinstance(answer, str) and len(answer) > 0
    # Rolls are bounded and valid.
    assert all(1 <= r <= 6 for r in g.roll(2, 6))


def test_trivia_flow():
    g = GamesService()
    sess = g.start_trivia(42)
    assert sess.question
    assert g.try_answer(42, 1, "wrong guess") == "wrong"
    correct = next(iter(sess.answer))
    assert g.try_answer(42, 2, correct) == "correct"
    assert g.try_answer(42, 3, "anything") == "no_game"


# --- custom commands ---
def test_parse_role_ids():
    assert parse_role_ids("[1, 2, 3]") == [1, 2, 3]
    assert parse_role_ids("[]") == []
    assert parse_role_ids("bogus") == []


@pytest.mark.asyncio
async def test_custom_command_upsert_and_get(sessions):
    svc = CustomCommandService()
    async with sessions() as s:
        await svc.upsert(s, guild_id=1, name="hi", response="Hello!")
        await s.commit()
        cmd = await svc.get(s, 1, "hi")
        assert cmd is not None and cmd.response == "Hello!"
        # guild 2 cannot see it
        assert await svc.get(s, 2, "hi") is None
        await s.commit()


@pytest.mark.asyncio
async def test_custom_command_delete(sessions):
    svc = CustomCommandService()
    async with sessions() as s:
        await svc.upsert(s, guild_id=1, name="bye", response="cya")
        await s.commit()
        assert await svc.delete(s, 1, "bye") is True
        await s.commit()
        assert await svc.get(s, 1, "bye") is None
