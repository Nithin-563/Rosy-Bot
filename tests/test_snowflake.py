"""Regression: Discord snowflake ids (64-bit) must not overflow the DB.

The initial migration used 32-bit INTEGER columns which overflow on large
snowflake ids (e.g. 1521043156618055720). This test proves a large id can be
stored and retrieved.
"""

import pytest

from rosy.db.models import Guild, Memory
from rosy.memory.service import MemoryService

BIG_ID = 1521043156618055720  # real Discord snowflake


@pytest.mark.asyncio
async def test_large_snowflake_guild_id(session_factory):
    async with session_factory() as s:
        g = Guild(id=BIG_ID, name="Big Server")
        s.add(g)
        await s.commit()
        await s.refresh(g)
        assert g.id == BIG_ID


@pytest.mark.asyncio
async def test_large_snowflake_memory(session_factory):
    async with session_factory() as s:
        svc = MemoryService(s)
        await svc.remember(
            user_id=BIG_ID, guild_id=BIG_ID, key="k", value="v"
        )
        mem = await svc.get(BIG_ID, BIG_ID, "k")
        assert mem is not None
        assert mem.user_id == BIG_ID
        assert mem.guild_id == BIG_ID
