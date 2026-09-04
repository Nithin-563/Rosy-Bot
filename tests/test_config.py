"""Config tests."""
from __future__ import annotations

from rosy.config import Settings


def test_default_provider_is_openrouter():
    s = Settings(discord_token="x")
    assert s.default_provider_name == "openrouter"
    assert s.ai_default_provider == "openrouter"


def test_postgres_detection():
    s = Settings(discord_token="x", database_url="postgresql+asyncpg://u:p@h/db")
    assert s.is_postgres is True
    s2 = Settings(discord_token="x", database_url="sqlite+aiosqlite:///./x.db")
    assert s2.is_postgres is False


def test_token_defaults_empty():
    s = Settings()
    assert s.discord_token == ""
