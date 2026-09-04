"""Persistent conversation store.

Logs every user message and Rosy reply to the database and can replay recent
history into the model context, so Rosie never forgets an ongoing thread even
across restarts.
"""

from __future__ import annotations

import logging

from sqlalchemy import select

from rosy.models import Conversation, Message

logger = logging.getLogger("rosy.conversation.store")


class ConversationStore:
    def __init__(self, db) -> None:
        self.db = db
        self._cache: dict[tuple, int] = {}

    async def _conversation_id(
        self, guild_id: int | None, channel_id: int | None, user_id: int | None, is_dm: bool
    ) -> int:
        """Reuse a conversation row per (guild/channel or dm-user)."""
        if is_dm:
            key = ("dm", user_id)
            match = (Conversation.is_dm == True, Conversation.user_id == user_id)  # noqa: E712
        else:
            key = ("guild", channel_id)
            match = (Conversation.guild_id == guild_id, Conversation.channel_id == channel_id)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        async with self.db.session() as session:
            stmt = select(Conversation).where(*match).order_by(Conversation.updated_at.desc())
            row = (await session.execute(stmt)).scalars().first()
            if row is None:
                row = Conversation(
                    guild_id=guild_id,
                    channel_id=channel_id,
                    user_id=user_id,
                    is_dm=is_dm,
                    summary="",
                )
                session.add(row)
                await session.commit()
                await session.refresh(row)
        self._cache[key] = row.id
        return row.id

    async def append(
        self,
        *,
        guild_id: int | None,
        channel_id: int | None,
        user_id: int | None,
        is_dm: bool,
        role: str,
        content: str,
    ) -> None:
        try:
            cid = await self._get_conversation_id(guild_id, channel_id, user_id, is_dm)
            async with self.db.session() as session:
                session.add(Message(conversation_id=cid, role=role, content=content))
                await session.commit()
        except Exception:  # pragma: no cover - never let logging break a reply
            logger.exception("Failed to persist a conversation message")

    async def recent(
        self,
        *,
        guild_id: int | None,
        channel_id: int | None,
        user_id: int | None,
        is_dm: bool,
        limit: int = 12,
    ) -> list[dict]:
        try:
            cid = await self._get_conversation_id(guild_id, channel_id, user_id, is_dm)
            async with self.db.session() as session:
                stmt = (
                    select(Message)
                    .where(Message.conversation_id == cid)
                    .order_by(Message.id.desc())
                    .limit(limit)
                )
                rows = list((await session.execute(stmt)).scalars().all())
            return [{"role": r.role, "content": r.content} for r in reversed(rows)]
        except Exception:  # pragma: no cover
            logger.exception("Could not recall recent conversation")
            return []

    async def _get_conversation_id(
        self, guild_id: int | None, channel_id: int | None, user_id: int | None, is_dm: bool
    ) -> int:
        return await self._conversation_id(guild_id, channel_id, user_id, is_dm)