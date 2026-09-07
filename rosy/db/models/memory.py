"""Memory records — the heart of Rosy's memory system."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from rosy.db.base import Base, SurrogatePK, TimestampMixin


class Memory(TimestampMixin, Base):
    """A single stored memory.

    scope: "dm" | "guild" | "user_in_guild"
    For "guild" and "user_in_guild" memories, guild_id is required.
    For "dm" memories, owner_user_id is the owning user.
    """

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(24), index=True)
    owner_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    guild_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    # For user_in_guild memories, which user the fact is about.
    subject_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    kind: Mapped[str] = mapped_column(String(32), default="fact")  # preference|fact|summary|...
    content: Mapped[str] = mapped_column(Text)
    source_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    source_author_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
