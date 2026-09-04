"""Guild- and channel-scoped records (multi-server isolation)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rosy.db.base import Base, SurrogatePK, TimestampMixin


class Guild(TimestampMixin, Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(120), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_reply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    channels: Mapped[list["Channel"]] = relationship(
        back_populates="guild", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Guild id={self.id} name={self.name!r}>"


class Channel(TimestampMixin, Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    guild_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), default="")
    # "text" | "voice" | "dm" (dm => guild_id is NULL)
    kind: Mapped[str] = mapped_column(String(16), default="text")
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    guild: Mapped[Optional[Guild]] = relationship(back_populates="channels")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Channel id={self.id} name={self.name!r}>"


class GuildPreference(TimestampMixin, Base):
    __tablename__ = "guild_preferences"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    provider_name: Mapped[str] = mapped_column(String(40), default="")  # "" => use default
    model: Mapped[str] = mapped_column(String(120), default="")  # "" => use default
    personality_mode: Mapped[str] = mapped_column(String(24), default="friendly")
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    autonomous_replies: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    tools_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    music_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_tokens_per_msg: Mapped[int] = mapped_column(default=1500)
