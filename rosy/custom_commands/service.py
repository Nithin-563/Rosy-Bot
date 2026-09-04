"""Custom command service — server-specific commands with fixed or AI responses."""
from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rosy.db.models import CustomCommand

log = logging.getLogger(__name__)


def parse_role_ids(raw: str) -> list[int]:
    try:
        parsed = json.loads(raw or "[]")
        return [int(x) for x in parsed] if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []


class CustomCommandService:
    async def get(self, session: AsyncSession, guild_id: int, name: str) -> CustomCommand | None:
        res = await session.execute(
            select(CustomCommand).where(
                CustomCommand.guild_id == guild_id,
                CustomCommand.name == name.lower(),
            )
        )
        return res.scalars().first()

    async def list(self, session: AsyncSession, guild_id: int) -> list[CustomCommand]:
        res = await session.execute(
            select(CustomCommand).where(CustomCommand.guild_id == guild_id).order_by(CustomCommand.name)
        )
        return list(res.scalars().all())

    async def upsert(
        self,
        session: AsyncSession,
        *,
        guild_id: int,
        name: str,
        response: str = "",
        ai_powered: bool = False,
        alias_of: Optional[str] = None,
        allowed_roles: list[int] | None = None,
    ) -> CustomCommand:
        existing = await self.get(session, guild_id, name)
        if existing:
            existing.response = response
            existing.ai_powered = ai_powered
            existing.alias_of = alias_of
            existing.allowed_roles = json.dumps(allowed_roles or [])
            existing.enabled = True
            await session.flush()
            return existing
        cmd = CustomCommand(
            guild_id=guild_id, name=name.lower(), response=response,
            ai_powered=ai_powered, alias_of=alias_of,
            allowed_roles=json.dumps(allowed_roles or []),
        )
        session.add(cmd)
        await session.flush()
        return cmd

    async def delete(self, session: AsyncSession, guild_id: int, name: str) -> bool:
        cmd = await self.get(session, guild_id, name)
        if cmd is None:
            return False
        await session.delete(cmd)
        await session.flush()
        return True

    async def set_enabled(self, session: AsyncSession, guild_id: int, name: str, enabled: bool) -> bool:
        cmd = await self.get(session, guild_id, name)
        if cmd is None:
            return False
        cmd.enabled = enabled
        await session.flush()
        return True
