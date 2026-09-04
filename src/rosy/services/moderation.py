"""Moderation subsystem.

Tracks warnings/timeouts/kicks/bans in the database and provides helper
methods used by the moderation cog. Discord-side permission enforcement is
always delegated to Discord's own permission checks — Rosy never bypasses them.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import ModerationRecord

logger = logging.getLogger("rosy.moderation")


class ModerationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        action: str,
        reason: str = "",
    ) -> ModerationRecord:
        rec = ModerationRecord(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            action=action,
            reason=reason,
        )
        self.session.add(rec)
        await self.session.commit()
        await self.session.refresh(rec)
        return rec

    async def warning_count(self, *, guild_id: int, user_id: int) -> int:
        from sqlalchemy import select, func

        stmt = (
            select(func.count())
            .select_from(ModerationRecord)
            .where(
                ModerationRecord.guild_id == guild_id,
                ModerationRecord.user_id == user_id,
                ModerationRecord.action == "warn",
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def history(
        self, *, guild_id: int, user_id: Optional[int] = None, limit: int = 20
    ) -> list[ModerationRecord]:
        from sqlalchemy import select

        stmt = (
            select(ModerationRecord)
            .where(ModerationRecord.guild_id == guild_id)
            .order_by(ModerationRecord.created_at.desc())
            .limit(limit)
        )
        if user_id is not None:
            stmt = stmt.where(ModerationRecord.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
