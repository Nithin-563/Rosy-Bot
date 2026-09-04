"""Conversations and their message history."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rosy.db.base import Base, SurrogatePK, TimestampMixin


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    # "dm" conversations have a NULL guild_id and a non-null user_id.
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    summary: Mapped[str] = mapped_column(Text, default="")

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationMessage.position"
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    role: Mapped[str] = mapped_column(String(16))  # system|user|assistant|tool
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
