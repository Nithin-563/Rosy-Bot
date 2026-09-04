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


def test_normalize_database_url():
    from rosy.config import normalize_database_url
    # Railway sync Postgres URL -> asyncpg dialect
    assert (
        normalize_database_url("postgresql://u:p@h:5432/db")
        == "postgresql+asyncpg://u:p@h:5432/db"
    )
    assert (
        normalize_database_url("postgres://u:p@h:5432/db")
        == "postgresql+asyncpg://u:p@h:5432/db"
    )
    assert (
        normalize_database_url("postgresql+psycopg2://u:p@h/db")
        == "postgresql+asyncpg://u:p@h/db"
    )
    # Already-async and SQLite URLs are unchanged
    assert normalize_database_url("postgresql+asyncpg://u:p@h/db") == "postgresql+asyncpg://u:p@h/db"
    assert normalize_database_url("sqlite+aiosqlite:///./x.db") == "sqlite+aiosqlite:///./x.db"
