"""Shared test fixtures. Uses SQLite (in-memory) so no external DB is needed."""

from __future__ import annotations

import pytest
import pytest_asyncio

from rosy.core.db import Database
from rosy.config import Settings
from rosy.core import init_encryption
from rosy.memory import MemoryService
from rosy.settings import GuildSettingsService
from rosy.moderation import ModerationService
from rosy.reminders import ReminderService


@pytest_asyncio.fixture
async def db():
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_all()
    try:
        yield database
    finally:
        await database.dispose()


@pytest.fixture
def settings():
    return Settings(
        _env_file=None,
        discord_token="test-token",
        database_url="sqlite+aiosqlite:///:memory:",
        openrouter_api_key="test",
    )


@pytest_asyncio.fixture
async def memory_service(db, settings):
    return MemoryService(db, settings)


@pytest_asyncio.fixture
async def guild_settings(db):
    return GuildSettingsService(db)


@pytest_asyncio.fixture
async def moderation(db):
    return ModerationService(db)


@pytest_asyncio.fixture
async def reminders(db):
    return ReminderService(db, poll_seconds=0.2)


@pytest.fixture(autouse=True)
def _encryption():
    init_encryption("test-secret", "test-salt")