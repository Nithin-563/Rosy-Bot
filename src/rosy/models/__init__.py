"""SQLAlchemy ORM models.

Schema is deliberately separated into isolated tables that scale across many
guilds. Every per-guild table carries a `guild_id` and every per-user table a
`user_id`; authorization is enforced in the service layer.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rosy.core.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class MemoryType(str, enum.Enum):
    user_preference = "user_preference"
    useful_fact = "useful_fact"
    conversation_summary = "conversation_summary"
    guild_fact = "guild_fact"
    guild_preference = "guild_preference"
    temporary_context = "temporary_context"
    relationship = "relationship"
    knowledge = "knowledge"


class MemoryScope(str, enum.Enum):
    dm = "dm"  # private to a user
    guild = "guild"  # server-wide
    user_in_guild = "user_in_guild"  # a user within a specific server


class ProviderKind(str, enum.Enum):
    openrouter = "openrouter"
    openai = "openai"
    gemini = "gemini"
    anthropic = "anthropic"
    groq = "groq"
    mistral = "mistral"
    custom = "custom"


# ---------------------------------------------------------------- guilds/users


class Guild(Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    settings: Mapped[GuildSettings] = relationship(
        back_populates="guild", uselist=False, cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------- preferences


class GuildSettings(Base):
    """Per-guild isolated configuration (JSON blobs for extensibility)."""

    __tablename__ = "guild_settings"

    guild_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), primary_key=True
    )
    ai_provider: Mapped[str] = mapped_column(String(40), default="openrouter")
    ai_model: Mapped[str] = mapped_column(String(120), default="")
    autonomous_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    autonomous_probability: Mapped[float] = mapped_column(Float, default=0.15)
    personality_mode: Mapped[str] = mapped_column(String(30), default="friendly")
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    prefix: Mapped[str] = mapped_column(String(16), default="")
    log_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Extensible per-guild feature toggles / settings.
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    guild: Mapped[Guild] = relationship(back_populates="settings")


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    llm_preferred_model: Mapped[str] = mapped_column(String(120), default="")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------- credentials


class ProviderCredential(Base):
    """Encrypted stored provider credentials (per guild, optional)."""

    __tablename__ = "provider_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    api_key_cipher: Mapped[str] = mapped_column(Text)  # encrypted at rest
    base_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    default_model: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (UniqueConstraint("guild_id", "provider", name="uq_cred_guild_provider"),)


# ---------------------------------------------------------------- memory


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope: Mapped[MemoryScope] = mapped_column(Enum(MemoryScope, name="memory_scope"), index=True)
    type: Mapped[MemoryType] = mapped_column(Enum(MemoryType, name="memory_type"), default=MemoryType.useful_fact)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    source: Mapped[str] = mapped_column(String(120), default="")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("scope", "guild_id", "user_id", "content", name="uq_memory_dedup"),
    )


# ---------------------------------------------------------------- conversations


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    is_dm: Mapped[bool] = mapped_column(Boolean, default=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Message(Base):
    """Stored message context (trimmed, not full user content by default)."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


# ---------------------------------------------------------------- usage


class Usage(Base):
    __tablename__ = "usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), default="")
    model: Mapped[str] = mapped_column(String(120), default="")
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[str] = mapped_column(String(40), default="chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


# ---------------------------------------------------------------- reminders


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    message: Mapped[str] = mapped_column(Text)
    fire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    recurring: Mapped[str] = mapped_column(String(20), default="")  # cron-ish or "daily"/"weekly"
    fired: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------------------------------------------------------------- moderation


class ModerationRecord(Base):
    __tablename__ = "moderation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True)
    target_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


# ---------------------------------------------------------------- custom commands


class CustomCommand(Base):
    __tablename__ = "custom_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(String(64))
    response: Mapped[str] = mapped_column(Text, default="")
    ai_powered: Mapped[bool] = mapped_column(Boolean, default=False)
    aliases: Mapped[dict] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (UniqueConstraint("guild_id", "name", name="uq_custom_command_guild_name"),)


# ---------------------------------------------------------------- knowledge


class Knowledge(Base):
    __tablename__ = "knowledge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    scope: Mapped[MemoryScope] = mapped_column(Enum(MemoryScope, name="knowledge_scope"), default=MemoryScope.guild)
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    source: Mapped[str] = mapped_column(String(120), default="")
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------------------------------------------------------------- plugin state


class PluginConfig(Base):
    __tablename__ = "plugin_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    plugin: Mapped[str] = mapped_column(String(80))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (UniqueConstraint("guild_id", "plugin", name="uq_plugin_guild_plugin"),)


# ---------------------------------------------------------------- personality


class PersonalityState(Base):
    __tablename__ = "personality_state"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mode: Mapped[str] = mapped_column(String(30), default="friendly")
    history: Mapped[dict] = mapped_column(JSON, default=list)  # last N mode switches
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)