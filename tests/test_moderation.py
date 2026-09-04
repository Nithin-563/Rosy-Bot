"""Moderation service tests."""

import pytest

from rosy.services.moderation import ModerationService


@pytest.mark.asyncio
async def test_record_and_warning_count(session_factory):
    async with session_factory() as s:
        svc = ModerationService(s)
        await svc.record(guild_id=10, user_id=1, moderator_id=2, action="warn", reason="spam")
        await svc.record(guild_id=10, user_id=1, moderator_id=2, action="warn", reason="spam")
        assert await svc.warning_count(guild_id=10, user_id=1) == 2


@pytest.mark.asyncio
async def test_history_scoped_to_guild(session_factory):
    async with session_factory() as s:
        svc = ModerationService(s)
        await svc.record(guild_id=10, user_id=1, moderator_id=2, action="warn", reason="a")
        await svc.record(guild_id=20, user_id=1, moderator_id=2, action="ban", reason="b")
        g10 = await svc.history(guild_id=10, user_id=1)
        assert len(g10) == 1
        assert g10[0].action == "warn"
        assert g10[0].guild_id == 10
