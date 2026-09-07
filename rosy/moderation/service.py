"""Moderation service — records actions and provides automod filtering.

Actions are executed by the Discord cog using Discord's own permission system;
this service only records history and applies configurable text filters.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rosy.db.models import ModerationRecord

log = logging.getLogger(__name__)


@dataclass
class ModConfig:
    warn_limit: int = 3
    anti_spam_enabled: bool = True
    anti_flood_interval_seconds: int = 5
    anti_flood_max_messages: int = 6
    blocked_words: list[str] = field(default_factory=list)
    blocked_urls: bool = False


class ModerationService:
    def __init__(self, config: ModConfig | None = None) -> None:
        self.config = config or ModConfig()
        # In-memory flood tracker per (guild, user): deque of timestamps.
        self._flood: dict[tuple[int, int], list[float]] = {}

    # --- Record keeping ---
    async def record(
        self,
        session: AsyncSession,
        *,
        guild_id: int,
        action: str,
        target_user_id: Optional[int] = None,
        moderator_id: Optional[int] = None,
        reason: str = "",
        duration_seconds: Optional[int] = None,
    ) -> ModerationRecord:
        rec = ModerationRecord(
            guild_id=guild_id, action=action, target_user_id=target_user_id,
            moderator_id=moderator_id, reason=reason, duration_seconds=duration_seconds,
        )
        session.add(rec)
        await session.flush()
        return rec

    async def history(self, session: AsyncSession, guild_id: int, *, limit: int = 25) -> list[ModerationRecord]:
        res = await session.execute(
            select(ModerationRecord)
            .where(ModerationRecord.guild_id == guild_id)
            .order_by(ModerationRecord.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())

    async def warning_count(self, session: AsyncSession, guild_id: int, user_id: int) -> int:
        res = await session.execute(
            select(func.count(ModerationRecord.id)).where(
                ModerationRecord.guild_id == guild_id,
                ModerationRecord.target_user_id == user_id,
                ModerationRecord.action == "warn",
            )
        )
        return res.scalar_one() or 0

    # --- Automod checks (deterministic, offline) ---
    def check_blocked_words(self, content: str) -> list[str]:
        lowered = content.lower()
        return [w for w in self.config.blocked_words if w.lower() in lowered]

    def check_flood(self, guild_id: int, user_id: int, now: float) -> bool:
        if not self.config.anti_spam_enabled:
            return False
        key = (guild_id, user_id)
        times = self._flood.setdefault(key, [])
        cutoff = now - self.config.anti_flood_interval_seconds
        times[:] = [t for t in times if t > cutoff]
        times.append(now)
        return len(times) > self.config.anti_flood_max_messages

    def check_url(self, content: str) -> bool:
        if not self.config.blocked_urls:
            return False
        return bool(re.search(r"https?://\S+", content, re.I))
