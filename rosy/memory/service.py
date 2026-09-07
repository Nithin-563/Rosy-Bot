"""Memory service — CRUD over the Memory model with strict scope isolation."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from rosy.config import get_settings
from rosy.db.models import Memory
from rosy.memory.scope import MemoryKey

log = logging.getLogger(__name__)


class MemoryService:
    def __init__(self, settings: object | None = None) -> None:
        self.settings = settings or get_settings()

    @staticmethod
    def _base_query(key: MemoryKey):
        q = select(Memory).where(Memory.scope == key.scope)
        if key.scope == "dm":
            q = q.where(Memory.owner_user_id == key.owner_user_id, Memory.guild_id.is_(None))
        elif key.scope == "guild":
            q = q.where(Memory.guild_id == key.guild_id, Memory.owner_user_id.is_(None))
        else:
            q = q.where(Memory.guild_id == key.guild_id, Memory.owner_user_id == key.owner_user_id)
        return q

    async def remember(
        self,
        session: AsyncSession,
        key: MemoryKey,
        content: str,
        *,
        kind: str = "fact",
        importance: float = 0.5,
        confidence: float = 0.7,
        expires_at: Optional[datetime] = None,
        source_message_id: Optional[int] = None,
        source_author_id: Optional[int] = None,
    ) -> Memory:
        key.validate()
        mem = Memory(
            scope=key.scope,
            owner_user_id=key.owner_user_id,
            guild_id=key.guild_id,
            kind=kind,
            content=content,
            importance=importance,
            confidence=confidence,
            expires_at=expires_at,
            source_message_id=source_message_id,
            source_author_id=source_author_id,
        )
        session.add(mem)
        await session.flush()
        return mem

    async def list_memories(
        self, session: AsyncSession, key: MemoryKey, *, limit: int | None = None
    ) -> list[Memory]:
        key.validate()
        now = datetime.now(timezone.utc)
        q = self._base_query(key).where(
            (Memory.expires_at.is_(None)) | (Memory.expires_at > now)
        )
        q = q.order_by(Memory.importance.desc(), Memory.created_at.desc())
        if limit:
            q = q.limit(limit)
        res = await session.execute(q)
        return list(res.scalars().all())

    async def top_memories(
        self, session: AsyncSession, key: MemoryKey, *, k: int | None = None
    ) -> list[str]:
        k = k or get_settings().memory_top_k
        mems = await self.list_memories(session, key, limit=k)
        return [m.content for m in mems]

    async def forget(self, session: AsyncSession, key: MemoryKey, memory_id: int) -> bool:
        """Delete a memory only if it is visible within `key`'s scope."""
        key.validate()
        allowed = self._base_query(key).where(Memory.id == memory_id)
        found = (await session.execute(allowed)).scalar_one_or_none()
        if found is None:
            return False  # not found or not visible in this scope
        await session.delete(found)
        await session.flush()
        return True

    async def clear(self, session: AsyncSession, key: MemoryKey) -> int:
        key.validate()
        ids = select(Memory.id).where(
            Memory.scope == key.scope,
            Memory.guild_id.is_(key.guild_id),
            Memory.owner_user_id.is_(key.owner_user_id),
        )
        res = await session.execute(delete(Memory).where(Memory.id.in_(ids)))
        return res.rowcount or 0

    async def search(self, session: AsyncSession, key: MemoryKey, term: str) -> list[Memory]:
        key.validate()
        like = f"%{term}%"
        q = self._base_query(key).where(Memory.content.ilike(like)).order_by(Memory.importance.desc())
        res = await session.execute(q)
        return list(res.scalars().all())

    async def prune_expired(self, session: AsyncSession) -> int:
        now = datetime.now(timezone.utc)
        res = await session.execute(delete(Memory).where(Memory.expires_at.is_not(None), Memory.expires_at < now))
        return res.rowcount or 0
