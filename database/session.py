"""Database session and engine management.

This module provides async database session handling using SQLAlchemy's
async support with asyncpg driver for PostgreSQL.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.
    
    This is a dependency for use with FastAPI or other frameworks
    that support dependency injection.
    
    Yields:
        AsyncSession: An async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session as a context manager.
    
    This is useful for non-FastAPI contexts like Discord bot events.
    
    Yields:
        AsyncSession: An async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize the database by creating all tables.
    
    This function imports all models to ensure they are registered
    with the Base metadata before creating tables.
    """
    from database.models import (  # noqa: F401
        Guild,
        User,
        Conversation,
        Message,
        Memory,
        AIProvider,
        APIKey,
        PersonalityPreference,
        Log,
        Reminder,
        GuildSetting,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database connections and cleanup resources."""
    await engine.dispose()
    logger.info("Database connections closed")
