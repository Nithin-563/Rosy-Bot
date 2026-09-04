"""Usage statistics and aggregate AI/command counters."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from rosy.db.base import Base, SurrogatePK


class UsageStat(Base):
    __tablename__ = "usage_stats"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    day: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True, index=True)
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)

    category: Mapped[str] = mapped_column(String(40), default="ai")  # ai|command|tool|memory
    provider: Mapped[str] = mapped_column(String(40), default="")
    model: Mapped[str] = mapped_column(String(120), default="")
    count: Mapped[int] = mapped_column(Integer, default=0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
