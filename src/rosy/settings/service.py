"""Guild-scoped settings service with strict guild isolation."""

from __future__ import annotations

import logging

from sqlalchemy import select

from rosy.models import Guild, GuildSettings, User, UserPreferences

logger = logging.getLogger("rosy.settings")


class GuildSettingsService:
    def __init__(self, db) -> None:
        self.db = db

    async def ensure_guild(self, guild_id: int, name: str = "") -> Guild:
        async with self.db.session() as session:
            guild = await session.get(Guild, guild_id)
            if guild is None:
                guild = Guild(id=guild_id, name=name or "")
                session.add(guild)
                await session.commit()
            elif name:
                guild.name = name
                await session.commit()
            return guild

    async def get_settings(self, guild_id: int, default: GuildSettings | None = None) -> GuildSettings:
        async with self.db.session() as session:
            await self.ensure_guild(guild_id)
            res = await session.execute(select(GuildSettings).where(GuildSettings.guild_id == guild_id))
            gs = res.scalar_one_or_none()
            if gs is None:
                gs = GuildSettings(guild_id=guild_id)
                session.add(gs)
                await session.commit()
            return gs

    async def update_settings(self, guild_id: int, **kwargs) -> GuildSettings:
        allowed = {
            "ai_provider", "ai_model", "autonomous_enabled", "autonomous_probability",
            "personality_mode", "memory_enabled", "prefix", "log_channel_id",
        }
        async with self.db.session() as session:
            existing = await session.get(GuildSettings, guild_id)
            if existing is None:
                await self.ensure_guild(guild_id)
                existing = GuildSettings(guild_id=guild_id)
                session.add(existing)
            for k, v in kwargs.items():
                if k in allowed:
                    setattr(existing, k, v)
            await session.commit()
            return existing

    async def ensure_user(self, user_id: int, username: str = "") -> User:
        async with self.db.session() as session:
            u = await session.get(User, user_id)
            if u is None:
                u = User(id=user_id, username=username)
                session.add(u)
                await session.commit()
            elif username and u.username != username:
                u.username = username
                await session.commit()
            return u

    async def get_user_prefs(self, user_id: int) -> UserPreferences:
        async with self.db.session() as session:
            p = await session.get(UserPreferences, user_id)
            if p is None:
                p = UserPreferences(user_id=user_id)
                session.add(p)
                await session.commit()
            return p

    async def update_user_prefs(self, user_id: int, **kwargs) -> UserPreferences:
        allowed = {"name", "timezone", "llm_preferred_model"}
        async with self.db.session() as session:
            p = await session.get(UserPreferences, user_id)
            if p is None:
                p = UserPreferences(user_id=user_id)
                session.add(p)
            for k, v in kwargs.items():
                if k in allowed:
                    setattr(p, k, v)
            await session.commit()
            return p