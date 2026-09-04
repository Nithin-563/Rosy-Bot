"""Moderation records (warnings, kicks, bans, timeouts, automod actions)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from rosy.db.base import Base, SurrogatePK, TimestampMixin


class ModerationRecord(TimestampMixin, Base):
    __tablename__ = "moderation_records"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True)
    action: Mapped[str] = mapped_column(String(24))  # warn|timeout|kick|ban|unban|purge
    target_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    moderator_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
