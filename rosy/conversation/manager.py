"""Conversation manager — persists recent message context per channel/user."""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rosy.ai.base import Message
from rosy.db.models import Conversation, ConversationMessage

log = logging.getLogger(__name__)

MAX_STORED = 80


class ConversationManager:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    async def _find(self, session: AsyncSession, *, guild_id, channel_id, user_id) -> Conversation | None:
        q = select(Conversation).where(
            Conversation.guild_id == guild_id,
            Conversation.channel_id == channel_id,
            Conversation.user_id == user_id,
        )
        res = await session.execute(q)
        return res.scalars().first()

    async def append(
        self, *, guild_id: Optional[int], channel_id: Optional[int],
        user_id: Optional[int], role: str, content: str,
        author_id: Optional[int] = None,
    ) -> None:
        async with self.sessions() as session:
            conv = await self._find(session, guild_id=guild_id, channel_id=channel_id, user_id=user_id)
            if conv is None:
                conv = Conversation(guild_id=guild_id, channel_id=channel_id, user_id=user_id)
                session.add(conv)
                await session.flush()
            max_pos = await session.execute(
                select(func.coalesce(func.max(ConversationMessage.position), 0)).where(
                    ConversationMessage.conversation_id == conv.id
                )
            )
            position = (max_pos.scalar_one() or 0) + 1
            session.add(
                ConversationMessage(
                    conversation_id=conv.id, position=position,
                    role=role, content=content, author_id=author_id,
                )
            )
            # Trim old messages beyond a bound.
            excess = await session.execute(
                select(ConversationMessage.id)
                .where(ConversationMessage.conversation_id == conv.id)
                .order_by(ConversationMessage.position.desc())
                .offset(MAX_STORED)
            )
            stale_ids = list(excess.scalars().all())
            if stale_ids:
                await session.execute(
                    delete(ConversationMessage).where(ConversationMessage.id.in_(stale_ids))
                )
            await session.commit()

    async def recent(
        self, *, guild_id: Optional[int], channel_id: Optional[int],
        user_id: Optional[int], limit: int = 20,
    ) -> list[ConversationMessage]:
        async with self.sessions() as session:
            conv = await self._find(session, guild_id=guild_id, channel_id=channel_id, user_id=user_id)
            if conv is None:
                return []
            res = await session.execute(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == conv.id)
                .order_by(ConversationMessage.position.desc())
                .limit(limit)
            )
            return list(reversed(res.scalars().all()))

    async def to_messages(self, *, guild_id: Optional[int], channel_id: Optional[int],
                          user_id: Optional[int], limit: int = 20) -> list[Message]:
        rows = await self.recent(guild_id=guild_id, channel_id=channel_id, user_id=user_id, limit=limit)
        out: list[Message] = []
        for r in rows:
            if r.role in ("system", "user", "assistant", "tool"):
                out.append(Message(role=r.role, content=r.content, name=(None if r.role != "tool" else str(r.author_id))))
        return out

    async def summary(self, *, guild_id: Optional[int], channel_id: Optional[int],
                      user_id: Optional[int]) -> str:
        async with self.sessions() as session:
            conv = await self._find(session, guild_id=guild_id, channel_id=channel_id, user_id=user_id)
            return conv.summary if conv else ""

    async def set_summary(self, *, guild_id: Optional[int], channel_id: Optional[int],
                          user_id: Optional[int], text: str) -> None:
        async with self.sessions() as session:
            conv = await self._find(session, guild_id=guild_id, channel_id=channel_id, user_id=user_id)
            if conv is not None:
                conv.summary = text
                await session.commit()
