"""Memory system.

Supports scoped memories (dm, guild, user_in_guild) with metadata, expiration,
importance/confidence, and strict guild/user isolation in every query.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from rosy.config import Settings
from rosy.core.errors import PermissionDenied
from rosy.models import Memory, MemoryScope, MemoryType

logger = logging.getLogger("rosy.memory")


class MemoryService:
    def __init__(self, db, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    # ----------------------------------------------------------- authorization

    @staticmethod
    def _scope_args(scope: MemoryScope, guild_id: int | None, user_id: int | None) -> dict:
        if scope == MemoryScope.dm:
            if user_id is None:
                raise PermissionDenied("DM memory requires a user.")
            return {"scope": scope, "user_id": user_id, "guild_id": None}
        if scope == MemoryScope.guild:
            if guild_id is None:
                raise PermissionDenied("Guild memory requires a guild.")
            return {"scope": scope, "guild_id": guild_id, "user_id": None}
        if scope == MemoryScope.user_in_guild:
            if guild_id is None or user_id is None:
                raise PermissionDenied("user_in_guild memory requires both.")
            return {"scope": scope, "guild_id": guild_id, "user_id": user_id}
        raise PermissionDenied("Unknown memory scope.")

    async def remember(
        self,
        content: str,
        *,
        scope: MemoryScope,
        guild_id: int | None,
        user_id: int | None,
        mtype: MemoryType = MemoryType.useful_fact,
        importance: float = 0.5,
        confidence: float = 0.7,
        source: str = "user",
        expires_in_seconds: int | None = None,
    ) -> Memory:
        kwargs = self._scope_args(scope, guild_id, user_id)
        expires = datetime.now(UTC) + timedelta(seconds=expires_in_seconds) if expires_in_seconds else None
        async with self.db.session() as session:
            # If identical content already exists, update importance/refresh.
            existing = await session.execute(
                select(Memory).where(
                    Memory.scope == scope,
                    Memory.guild_id == kwargs["guild_id"],
                    Memory.user_id == kwargs["user_id"],
                    Memory.content == content,
                )
            )
            mem = existing.scalar_one_or_none()
            if mem is not None:
                mem.importance = max(mem.importance, importance)
                mem.expires_at = expires
                await session.commit()
                return mem
            mem = Memory(
                type=mtype,
                content=content,
                importance=importance,
                confidence=confidence,
                source=source,
                expires_at=expires,
                **kwargs,
            )
            session.add(mem)
            await session.commit()
            return mem

    async def recall(
        self,
        *,
        scope: MemoryScope,
        guild_id: int | None,
        user_id: int | None,
        limit: int = 20,
        include_expired: bool = False,
    ) -> list[Memory]:
        kwargs = self._scope_args(scope, guild_id, user_id)
        stmt = (
            select(Memory)
            .where(
                Memory.scope == scope,
                Memory.guild_id == kwargs["guild_id"],
                Memory.user_id == kwargs["user_id"],
            )
            .order_by(Memory.importance.desc(), Memory.updated_at.desc())
            .limit(limit)
        )
        if not include_expired:
            stmt = stmt.where(
                (Memory.expires_at.is_(None)) | (Memory.expires_at > datetime.now(UTC))
            )
        async with self.db.session() as session:
            res = await session.execute(stmt)
            return list(res.scalars().all())

    async def forget(
        self,
        content: str,
        *,
        scope: MemoryScope,
        guild_id: int | None,
        user_id: int | None,
    ) -> bool:
        kwargs = self._scope_args(scope, guild_id, user_id)
        async with self.db.session() as session:
            res = await session.execute(
                select(Memory).where(
                    Memory.scope == scope,
                    Memory.guild_id == kwargs["guild_id"],
                    Memory.user_id == kwargs["user_id"],
                    Memory.content == content,
                )
            )
            mem = res.scalar_one_or_none()
            if mem is None:
                return False
            await session.delete(mem)
            await session.commit()
            return True

    async def clear_scope(
        self,
        *,
        scope: MemoryScope,
        guild_id: int | None,
        user_id: int | None,
    ) -> int:
        kwargs = self._scope_args(scope, guild_id, user_id)
        async with self.db.session() as session:
            res = await session.execute(
                select(Memory).where(
                    Memory.scope == scope,
                    Memory.guild_id == kwargs["guild_id"],
                    Memory.user_id == kwargs["user_id"],
                )
            )
            rows = list(res.scalars().all())
            for r in rows:
                await session.delete(r)
            await session.commit()
            return len(rows)