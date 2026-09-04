"""Async engine and session factory for Rosy."""

import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import get_settings
from .url import normalize_database_url

logger = logging.getLogger("rosy.db")

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _make_engine(database_url: str) -> AsyncEngine:
    # SQLite for local tests: -1 pool means single connection per process,
    # which avoids asyncio SQLite lock issues with asyncpg-style pooling.
    if database_url.startswith("sqlite"):
        return create_async_engine(database_url, connect_args={"check_same_thread": False})
    return create_async_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def init_engine(database_url: str | None = None) -> AsyncEngine:
    """Initialise the global engine. Idempotent."""
    global _engine, _sessionmaker
    if _engine is not None:
        return _engine
    url = normalize_database_url(database_url or get_settings().database_url)
    logger.info("Initialising database engine.")
    _engine = _make_engine(url)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        init_engine()
    assert _sessionmaker is not None
    return _sessionmaker


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
