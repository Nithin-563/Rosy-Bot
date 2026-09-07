"""Knowledge records — a memory-like store for learnable facts, guild-isolated."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from rosy.db.base import Base, SurrogatePK, TimestampMixin


class KnowledgeRecord(TimestampMixin, Base):
    __tablename__ = "knowledge_records"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(24), default="guild")  # guild|dm
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    owner_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)

    topic: Mapped[str] = mapped_column(String(160), index=True)
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), default="conversation")
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_knowledge_guild_topic", "guild_id", "topic"),
    )
