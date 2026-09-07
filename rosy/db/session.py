"""Async SQLAlchemy engine, session factory, and lifecycle helpers."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from rosy.config import get_settings, normalize_database_url


def build_engine(url: str | None = None, echo: bool | None = None) -> AsyncEngine:
    settings = get_settings()
    database_url = normalize_database_url(url or settings.database_url)
    kwargs: dict = {"echo": settings.sql_echo if echo is None else echo}
    # Only apply pool sizing to PostgreSQL (SQLite is file/connection based).
    if database_url.startswith("postgresql"):
        kwargs.update(
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
    else:
        kwargs.update(pool_pre_ping=True)
    return create_async_engine(database_url, **kwargs)


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def session_scope(sessions: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a series of operations."""
    async with sessions() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
