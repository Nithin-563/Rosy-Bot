"""Knowledge/learning service — guild-isolated learnable facts with provenance."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from rosy.db.models import KnowledgeRecord

log = logging.getLogger(__name__)


class KnowledgeService:
    """Stores and retrieves knowledge records, strictly scoped per guild or DM.

    A record is keyed by (scope, guild_id | owner_user_id, topic). Records are
    only ever queried within the same scope+owner they were written under, so
    no knowledge can leak across guilds.
    """

    async def learn(
        self,
        session: AsyncSession,
        *,
        topic: str,
        content: str,
        scope: str = "guild",
        guild_id: Optional[int] = None,
        owner_user_id: Optional[int] = None,
        source: str = "conversation",
        importance: float = 0.5,
        confidence: float = 0.7,
    ) -> KnowledgeRecord:
        existing = await self.find(session, topic=topic, scope=scope, guild_id=guild_id, owner_user_id=owner_user_id)
        if existing:
            existing.content = content
            existing.importance = importance
            existing.confidence = confidence
            existing.source = source
            await session.flush()
            return existing
        rec = KnowledgeRecord(
            topic=topic, content=content, scope=scope, guild_id=guild_id,
            owner_user_id=owner_user_id, source=source, importance=importance, confidence=confidence,
        )
        session.add(rec)
        await session.flush()
        return rec

    async def find(
        self,
        session: AsyncSession,
        *,
        topic: str,
        scope: str,
        guild_id: Optional[int] = None,
        owner_user_id: Optional[int] = None,
    ) -> KnowledgeRecord | None:
        now = datetime.now(timezone.utc)
        q = select(KnowledgeRecord).where(
            KnowledgeRecord.topic == topic,
            KnowledgeRecord.scope == scope,
            KnowledgeRecord.guild_id == guild_id,
            KnowledgeRecord.owner_user_id == owner_user_id,
            (KnowledgeRecord.expires_at.is_(None)) | (KnowledgeRecord.expires_at > now),
        )
        res = await session.execute(q)
        return res.scalars().first()

    async def search(
        self,
        session: AsyncSession,
        *,
        term: str,
        scope: str,
        guild_id: Optional[int] = None,
        owner_user_id: Optional[int] = None,
        limit: int = 8,
    ) -> list[KnowledgeRecord]:
        like = f"%{term}%"
        q = (
            select(KnowledgeRecord)
            .where(
                KnowledgeRecord.scope == scope,
                KnowledgeRecord.guild_id == guild_id,
                KnowledgeRecord.owner_user_id == owner_user_id,
                KnowledgeRecord.topic.ilike(like),
            )
            .order_by(KnowledgeRecord.importance.desc())
            .limit(limit)
        )
        res = await session.execute(q)
        return list(res.scalars().all())

    async def delete(self, session: AsyncSession, record_id: int) -> bool:
        rec = await session.get(KnowledgeRecord, record_id)
        if rec is None:
            return False
        await session.delete(rec)
        await session.flush()
        return True

    async def clear_scope(
        self, session: AsyncSession, *, scope: str, guild_id: Optional[int] = None, owner_user_id: Optional[int] = None
    ) -> int:
        res = await session.execute(
            delete(KnowledgeRecord).where(
                KnowledgeRecord.scope == scope,
                KnowledgeRecord.guild_id == guild_id,
                KnowledgeRecord.owner_user_id == owner_user_id,
            )
        )
        return res.rowcount or 0
