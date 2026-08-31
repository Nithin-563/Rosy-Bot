"""Memory isolation tests: DMs, guilds, and users must never leak."""

from __future__ import annotations

import pytest

from rosy.models import MemoryScope


async def test_dm_memory_requires_user(memory_service):
    with pytest.raises(Exception):
        await memory_service.remember("x", scope=MemoryScope.dm, guild_id=None, user_id=None)


async def test_memory_isolated_between_guilds(memory_service):
    await memory_service.remember(
        "guild A secret", scope=MemoryScope.guild, guild_id=111, user_id=None
    )
    await memory_service.remember(
        "guild B secret", scope=MemoryScope.guild, guild_id=222, user_id=None
    )
    a = await memory_service.recall(scope=MemoryScope.guild, guild_id=111, user_id=None)
    b = await memory_service.recall(scope=MemoryScope.guild, guild_id=222, user_id=None)
    assert len(a) == 1 and a[0].content == "guild A secret"
    assert len(b) == 1 and b[0].content == "guild B secret"


async def test_user_in_guild_isolated_between_users(memory_service):
    await memory_service.remember(
        "alice note", scope=MemoryScope.user_in_guild, guild_id=1, user_id=10
    )
    await memory_service.remember(
        "bob note", scope=MemoryScope.user_in_guild, guild_id=1, user_id=20
    )
    alice = await memory_service.recall(scope=MemoryScope.user_in_guild, guild_id=1, user_id=10)
    bob = await memory_service.recall(scope=MemoryScope.user_in_guild, guild_id=1, user_id=20)
    assert [m.content for m in alice] == ["alice note"]
    assert [m.content for m in bob] == ["bob note"]


async def test_forget_and_clear(memory_service):
    await memory_service.remember("tmp", scope=MemoryScope.dm, guild_id=None, user_id=5)
    assert len(await memory_service.recall(scope=MemoryScope.dm, guild_id=None, user_id=5)) == 1
    assert await memory_service.forget("tmp", scope=MemoryScope.dm, guild_id=None, user_id=5) is True
    assert await memory_service.recall(scope=MemoryScope.dm, guild_id=None, user_id=5) == []