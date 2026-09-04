"""Memory service tests, including guild/DM isolation."""

import pytest

from rosy.memory.service import MemoryService


async def _remember(session_factory, **kw):
    async with session_factory() as s:
        svc = MemoryService(s)
        mem = await svc.remember(**kw)
        return mem


@pytest.mark.asyncio
async def test_remember_and_retrieve(session_factory):
    async with session_factory() as s:
        svc = MemoryService(s)
        await svc.remember(
            user_id=1, guild_id=10, key="likes", value="coffee",
            memory_type="preference", importance=0.9,
        )
        mem = await svc.get(1, 10, "likes")
        assert mem is not None
        assert mem.value == "coffee"
        assert mem.scope == "user_guild"


@pytest.mark.asyncio
async def test_guild_isolation(session_factory):
    async with session_factory() as s:
        svc = MemoryService(s)
        await svc.remember(user_id=1, guild_id=10, key="k", value="guild-a")
        await svc.remember(user_id=1, guild_id=20, key="k", value="guild-b")
        a = await svc.get(1, 10, "k")
        b = await svc.get(1, 20, "k")
        assert a.value == "guild-a"
        assert b.value == "guild-b"


@pytest.mark.asyncio
async def test_dm_separate_from_guild(session_factory):
    async with session_factory() as s:
        svc = MemoryService(s)
        await svc.remember(user_id=1, guild_id=None, key="k", value="dm")
        await svc.remember(user_id=1, guild_id=10, key="k", value="guild")
        dm = await svc.get(1, None, "k")
        g = await svc.get(1, 10, "k")
        assert dm.value == "dm"
        assert g.value == "guild"
        assert dm.scope == "dm"


@pytest.mark.asyncio
async def test_forget(session_factory):
    async with session_factory() as s:
        svc = MemoryService(s)
        await svc.remember(user_id=1, guild_id=10, key="k", value="v")
        assert await svc.forget(user_id=1, guild_id=10, key="k") is True
        assert await svc.forget(user_id=1, guild_id=10, key="k") is False


@pytest.mark.asyncio
async def test_clear(session_factory):
    async with session_factory() as s:
        svc = MemoryService(s)
        await svc.remember(user_id=1, guild_id=10, key="a", value="1")
        await svc.remember(user_id=1, guild_id=10, key="b", value="2")
        count = await svc.clear(user_id=1, guild_id=10)
        assert count >= 2
        assert await svc.get(1, 10, "a") is None
