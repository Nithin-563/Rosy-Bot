"""Shared fixtures. No real API keys required."""

import os
import tempfile

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Use a local-disk SQLite file so the network-mounted workspace isn't hit.
_TEST_DB = os.path.join(tempfile.gettempdir(), "rosy_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)

from rosy.db import encryption  # noqa: E402
from rosy.db.base import Base  # noqa: E402

# Import all models so they register on Base.metadata.
from rosy.db import models  # noqa: E402,F401


@pytest.fixture(scope="session")
def engine():
    encryption.set_encryption_disabled(True)
    eng = create_async_engine(f"sqlite+aiosqlite:///{_TEST_DB}")
    yield eng
    import asyncio

    asyncio.run(eng.dispose())


@pytest.fixture
async def session_factory(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(session_factory):
    async with session_factory() as s:
        yield s
