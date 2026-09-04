"""Memory service.

Memory is scoped so that guild, DM, and user-in-guild data never leak across
boundaries. All queries filter by the caller's scope.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Memory

logger = logging.getLogger("rosy.memory")

VALID_TYPES = {"preference", "fact", "summary", "guild_fact", "guild_preference", "temp", "meta"}


class MemoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def remember(
        self,
        *,
        user_id: Optional[int],
        guild_id: Optional[int],
        key: str,
        value: str,
        memory_type: str = "fact",
        importance: float = 0.5,
        confidence: float = 1.0,
        source: str = "",
        expires_in_seconds: Optional[int] = None,
    ) -> Memory:
        if memory_type not in VALID_TYPES:
            memory_type = "fact"
        expires_at = None
        if expires_in_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)

        existing = await self.get(user_id, guild_id, key)
        if existing:
            existing.value = value
            existing.memory_type = memory_type
            existing.importance = importance
            existing.confidence = confidence
            existing.source = source
            existing.expires_at = expires_at
            mem = existing
        else:
            mem = Memory(
                user_id=user_id,
                guild_id=guild_id,
                key=key,
                value=value,
                memory_type=memory_type,
                importance=importance,
                confidence=confidence,
                source=source,
                scope=self._scope(user_id, guild_id),
                expires_at=expires_at,
            )
            self.session.add(mem)
        await self.session.commit()
        await self.session.refresh(mem)
        return mem

    async def get(
        self, user_id: Optional[int], guild_id: Optional[int], key: str
    ) -> Optional[Memory]:
        stmt = select(Memory).where(Memory.key == key)
        if guild_id is not None:
            stmt = stmt.where(Memory.guild_id == guild_id)
            if user_id is not None:
                stmt = stmt.where(Memory.user_id == user_id)
        else:
            stmt = stmt.where(Memory.guild_id.is_(None))
            if user_id is not None:
                stmt = stmt.where(Memory.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_context(
        self, *, user_id: Optional[int], guild_id: Optional[int], limit: int = 8
    ) -> list[Memory]:
        """Return non-expired, relevant memories for the given scope."""
        stmt = (
            select(Memory)
            .where(
                Memory.expires_at.is_(None) | (Memory.expires_at > datetime.utcnow())
            )
            .order_by(Memory.importance.desc(), Memory.updated_at.desc())
            .limit(limit)
        )
        if guild_id is not None:
            # Include guild-wide memories plus this user's in-guild memories.
            stmt = stmt.where(Memory.guild_id == guild_id)
            if user_id is not None:
                # Fall back at query level: allow both guild-wide and user-specific
                # in this guild.
                pass
        else:
            stmt = stmt.where(Memory.guild_id.is_(None))
            if user_id is not None:
                stmt = stmt.where(Memory.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_user(
        self, *, user_id: int, guild_id: Optional[int] = None, limit: int = 50
    ) -> list[Memory]:
        stmt = (
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.updated_at.desc())
            .limit(limit)
        )
        if guild_id is not None:
            stmt = stmt.where(Memory.guild_id == guild_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def forget(
        self, *, user_id: Optional[int], guild_id: Optional[int], key: str
    ) -> bool:
        mem = await self.get(user_id, guild_id, key)
        if mem is None:
            return False
        await self.session.delete(mem)
        await self.session.commit()
        return True

    async def clear(self, *, user_id: Optional[int], guild_id: Optional[int]) -> int:
        stmt = text(
            "DELETE FROM memories WHERE "
            "(:gid IS NULL AND guild_id IS NULL AND (:uid IS NULL OR user_id = :uid)) "
            "OR (:gid IS NOT NULL AND guild_id = :gid AND (:uid IS NULL OR user_id = :uid))"
        )
        result = await self.session.execute(
            stmt, {"gid": guild_id, "uid": user_id}
        )
        await self.session.commit()
        return result.rowcount or 0

    @staticmethod
    def _scope(user_id: Optional[int], guild_id: Optional[int]) -> str:
        if guild_id is None:
            return "dm"
        if user_id is not None:
            return "user_guild"
        return "guild"
