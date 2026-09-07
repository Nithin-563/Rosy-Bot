"""Custom (server-specific) commands."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from rosy.db.base import Base, SurrogatePK, TimestampMixin


class CustomCommand(TimestampMixin, Base):
    __tablename__ = "custom_commands"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    # If ai_powered is False, `response` is returned verbatim.
    response: Mapped[str] = mapped_column(Text, default="")
    ai_powered: Mapped[bool] = mapped_column(Boolean, default=False)
    alias_of: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    allowed_roles: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of role ids
