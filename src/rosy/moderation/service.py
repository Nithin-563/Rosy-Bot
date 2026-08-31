"""Moderation subsystem.

Warning/timeout/kick/ban actions recorded in the DB, with basic spam/flood
detection. All actions respect Discord permissions (enforced at the cog layer).
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from sqlalchemy import select

from rosy.models import ModerationRecord

logger = logging.getLogger("rosy.moderation")


class ModerationService:
    def __init__(self, db) -> None:
        self.db = db
        self._flood: dict[tuple[int, int], deque[float]] = defaultdict(lambda: deque(maxlen=10))

    async def record(
        self,
        *,
        guild_id: int,
        target_user_id: int,
        action: str,
        reason: str = "",
        actor_user_id: int | None = None,
    ) -> ModerationRecord:
        async with self.db.session() as session:
            rec = ModerationRecord(
                guild_id=guild_id,
                target_user_id=target_user_id,
                actor_user_id=actor_user_id,
                action=action,
                reason=reason,
            )
            session.add(rec)
            await session.commit()
            await session.refresh(rec)
            return rec

    async def history(self, guild_id: int, target_user_id: int | None = None, limit: int = 25) -> list[ModerationRecord]:
        stmt = select(ModerationRecord).where(ModerationRecord.guild_id == guild_id)
        if target_user_id is not None:
            stmt = stmt.where(ModerationRecord.target_user_id == target_user_id)
        stmt = stmt.order_by(ModerationRecord.created_at.desc()).limit(limit)
        async with self.db.session() as session:
            res = await session.execute(stmt)
            return list(res.scalars().all())

    def is_flooding(self, guild_id: int, author_id: int, *, window_seconds: int = 5, max_messages: int = 5) -> bool:
        """Basic anti-flood: more than N messages in a short window."""
        now = time.monotonic()
        q = self._flood[(guild_id, author_id)]
        q.append(now)
        while q and q[0] < now - window_seconds:
            q.popleft()
        return len(q) >= max_messages