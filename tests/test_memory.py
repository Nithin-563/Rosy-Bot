"""Memory service + scope isolation tests."""
from __future__ import annotations

import pytest

from rosy.memory.scope import MemoryKey, parse_duration
from rosy.memory.service import MemoryService

svc = MemoryService()


def test_scope_validation():
    MemoryKey(scope="dm", owner_user_id=1).validate()
    MemoryKey(scope="guild", guild_id=2).validate()
    MemoryKey(scope="user_in_guild", owner_user_id=1, guild_id=2).validate()
    with pytest.raises(ValueError):
        MemoryKey(scope="guild", owner_user_id=1).validate()
    with pytest.raises(ValueError):
        MemoryKey(scope="bogus").validate()


def test_parse_duration():
    assert parse_duration("30m").total_seconds() == 1800
    assert parse_duration("2h").total_seconds() == 7200
    assert parse_duration("1d").total_seconds() == 86400
    assert parse_duration("nonsense") is None


@pytest.mark.asyncio
async def test_guild_isolation(sessions):
    k1 = MemoryKey(scope="guild", guild_id=1)
    k2 = MemoryKey(scope="guild", guild_id=2)
    async with sessions() as s:
        await svc.remember(s, k1, "secret of guild 1")
        await svc.remember(s, k2, "secret of guild 2")
        await s.commit()
        mems1 = await svc.list_memories(s, k1)
        mems2 = await svc.list_memories(s, k2)
    assert [m.content for m in mems1] == ["secret of guild 1"]
    assert [m.content for m in mems2] == ["secret of guild 2"]


@pytest.mark.asyncio
async def test_dm_vs_guild_isolation(sessions):
    dm = MemoryKey(scope="dm", owner_user_id=1)
    guild = MemoryKey(scope="guild", guild_id=5)
    async with sessions() as s:
        await svc.remember(s, dm, "private note")
        await svc.remember(s, guild, "guild note")
        await s.commit()
        dm_rows = await svc.list_memories(s, dm)
        guild_rows = await svc.list_memories(s, guild)
    assert [m.content for m in dm_rows] == ["private note"]
    assert [m.content for m in guild_rows] == ["guild note"]


@pytest.mark.asyncio
async def test_forget_scope_guarded(sessions):
    k = MemoryKey(scope="guild", guild_id=1)
    other = MemoryKey(scope="guild", guild_id=2)
    async with sessions() as s:
        mem = await svc.remember(s, k, "xyz")
        await s.commit()
        # Other scope cannot forget it.
        assert await svc.forget(s, other, mem.id) is False
        # Own scope can.
        assert await svc.forget(s, k, mem.id) is True
        await s.commit()


@pytest.mark.asyncio
async def test_search(sessions):
    k = MemoryKey(scope="dm", owner_user_id=1)
    async with sessions() as s:
        await svc.remember(s, k, "loves python")
        await svc.remember(s, k, "hates onions")
        await s.commit()
        hits = await svc.search(s, k, "python")
    assert len(hits) == 1 and hits[0].content == "loves python"


@pytest.mark.asyncio
async def test_clear(sessions):
    k = MemoryKey(scope="dm", owner_user_id=1)
    async with sessions() as s:
        await svc.remember(s, k, "a")
        await svc.remember(s, k, "b")
        await s.commit()
        count = await svc.clear(s, k)
    assert count == 2
