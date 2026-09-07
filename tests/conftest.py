"""Shared test fixtures — in-memory SQLite, no real API keys required."""
from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from rosy.db.base import Base
from rosy.db.models import *  # noqa: F401,F403 - register models


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def sessions(engine):
    yield async_sessionmaker(engine, expire_on_commit=False)
