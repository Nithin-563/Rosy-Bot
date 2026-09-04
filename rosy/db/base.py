"""SQLAlchemy declarative base for all Rosy models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Surrogate primary-key type that autoincrements on both PostgreSQL (BIGSERIAL)
# and SQLite (INTEGER PRIMARY KEY). Plain BigInteger breaks SQLite autoincrement.
SurrogatePK = BigInteger().with_variant(Integer(), "sqlite")


class Base(DeclarativeBase):
    """Declarative base providing a shared timestamp convention."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
