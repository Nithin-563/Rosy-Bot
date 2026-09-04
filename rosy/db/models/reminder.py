"""Reminders and scheduled tasks (survive bot restarts via DB)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from rosy.db.base import Base, SurrogatePK, TimestampMixin


class Reminder(TimestampMixin, Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    # ISO 8601 recurrence, e.g. "FREQ=DAILY" — empty for one-shot reminders.
    recurrence: Mapped[str] = mapped_column(String(255), default="")
    fired: Mapped[bool] = mapped_column(Boolean, default=False)
    times_fired: Mapped[int] = mapped_column(Integer, default=0)
