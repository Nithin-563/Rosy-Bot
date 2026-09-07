"""Async SQLAlchemy database engine and session management.

Works with PostgreSQL in production (asyncpg) and SQLite (aiosqlite) in
tests / local dev. Connection pooling is configured for PostgreSQL.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from rosy.config import Settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def build_engine(url: str) -> AsyncEngine:
    kwargs: dict = {"echo": False}
    if url.startswith("postgresql"):
        kwargs.update(
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
    else:
        # SQLite does not support pooling the same way.
        kwargs.update(connect_args={"check_same_thread": False})
        if url.startswith("sqlite+aiosqlite:///:memory:"):
            from sqlalchemy.pool import StaticPool

            kwargs.update(poolclass=StaticPool)
    return create_async_engine(url, **kwargs)


class Database:
    """Owns the engine + session factory. Use `get_db` for sessions."""

    def __init__(self, url: str) -> None:
        self.engine = build_engine(url)
        self._session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> Database:
        return cls(settings.database_url)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            yield session

    async def create_all(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def dispose(self) -> None:
        await self.engine.dispose()


# Convenience default instance, replaced by the app container in prod.
_default_db: Database | None = None


def get_db() -> Database:
    if _default_db is None:
        raise RuntimeError("Database not initialised. Call set_db() first.")
    return _default_db


def set_db(db: Database) -> None:
    global _default_db
    _default_db = db