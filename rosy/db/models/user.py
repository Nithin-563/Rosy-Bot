"""User records and per-user (DM) preferences."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from rosy.db.base import Base, SurrogatePK, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str] = mapped_column(String(80), default="")
    # "global" memory of the user (DM-scoped). Guild-scoped knowledge lives in
    # KnowledgeRecord with a guild_id.
    personality_mode: Mapped[str] = mapped_column(String(24), default="")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<User id={self.id} username={self.username!r}>"


class UserPreference(TimestampMixin, Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    key: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(Text, default="")
    __table_args__ = (__import__("sqlalchemy").UniqueConstraint("user_id", "key", name="uq_user_pref"),)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<UserPreference user={self.user_id} {self.key}={self.value!r}>"
