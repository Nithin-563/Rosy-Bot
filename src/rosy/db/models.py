"""ORM models for Rosy.

The schema is deliberately extensible. Every guild-related table is keyed by
``guild_id`` (Discord snowflake stored as String) so multi-server isolation is
enforced at the query layer. DM data carries ``guild_id=None``.
"""

from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Guild(Base, TimestampMixin):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    personality: Mapped[str] = mapped_column(String(40), default="casual")
    autonomous_replies: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_provider: Mapped[str] = mapped_column(String(40), default="default")
    ai_model: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    prefix: Mapped[str] = mapped_column(String(10), default="!")
    settings: Mapped[dict] = mapped_column(JSON, default=dict)

    memories: Mapped[list["Memory"]] = relationship(back_populates="guild")
    custom_commands: Mapped[list["CustomCommand"]] = relationship(
        back_populates="guild", cascade="all, delete-orphan"
    )
    mod_records: Mapped[list["ModerationRecord"]] = relationship(
        back_populates="guild", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="guild", cascade="all, delete-orphan"
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    prefs: Mapped[dict] = mapped_column(JSON, default=dict)


class Channel(Base, TimestampMixin):
    __tablename__ = "channels"
    __table_args__ = (UniqueConstraint("guild_id", "channel_id", name="uq_guild_channel"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guilds.id"), nullable=True)
    channel_id: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String(200), default="")
    allow_autonomous: Mapped[bool] = mapped_column(Boolean, default=False)


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guilds.id"), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    channel_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    summary: Mapped[Text] = mapped_column(Text, default="")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))  # user / assistant
    content: Mapped[Text] = mapped_column(Text)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class Memory(Base, TimestampMixin):
    """A stored memory. Scope controls guild vs DM vs user-in-guild isolation."""

    __tablename__ = "memories"
    __table_args__ = (UniqueConstraint("guild_id", "user_id", "key", name="uq_memory_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guilds.id"), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    key: Mapped[str] = mapped_column(String(200))
    value: Mapped[Text] = mapped_column(Text)
    memory_type: Mapped[str] = mapped_column(String(40), default="fact")  # preference/fact/summary/guild_fact...
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[str] = mapped_column(String(200), default="")
    scope: Mapped[str] = mapped_column(String(20), default="guild")  # dm / guild / user_guild
    expires_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    guild: Mapped[Optional[Guild]] = relationship(back_populates="memories")
    user: Mapped[Optional[User]] = relationship()


class AIProviderCredential(Base, TimestampMixin):
    __tablename__ = "ai_providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guilds.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(40))
    api_key_enc: Mapped[str] = mapped_column(Text)  # encrypted
    model: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    base_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UsageStat(Base, TimestampMixin):
    __tablename__ = "usage_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guilds.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(40), default="openrouter")
    model: Mapped[str] = mapped_column(String(120), default="")
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[str] = mapped_column(String(40), default="chat")  # chat / image / voice


class Reminder(Base, TimestampMixin):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guilds.id"), nullable=True)
    user_id: Mapped[int] = mapped_column()
    channel_id: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column(Text)
    remind_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    recurring_cron: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fired: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")

    guild: Mapped[Optional[Guild]] = relationship(back_populates="reminders")


class ScheduledTask(Base, TimestampMixin):
    __tablename__ = "scheduled_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guilds.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    cron: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ModerationRecord(Base, TimestampMixin):
    __tablename__ = "moderation_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id"))
    user_id: Mapped[int] = mapped_column()
    moderator_id: Mapped[int] = mapped_column()
    action: Mapped[str] = mapped_column(String(40))  # warn / timeout / kick / ban
    reason: Mapped[str] = mapped_column(Text, default="")
    expires_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    guild: Mapped[Guild] = relationship(back_populates="mod_records")


class CustomCommand(Base, TimestampMixin):
    __tablename__ = "custom_commands"
    __table_args__ = (
        UniqueConstraint("guild_id", "name", name="uq_guild_custom_command"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id"))
    name: Mapped[str] = mapped_column(String(100))
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    use_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)

    guild: Mapped[Guild] = relationship(back_populates="custom_commands")


class Knowledge(Base, TimestampMixin):
    __tablename__ = "knowledge"

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[Optional[int]] = mapped_column(ForeignKey("guilds.id"), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    content: Mapped[Text] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(300), default="")
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-encoded vector


class GuildConfig(Base, TimestampMixin):
    """Generic per-guild key/value settings (moderation, tools, voice, music...)."""

    __tablename__ = "guild_config"
    __table_args__ = (UniqueConstraint("guild_id", "key", name="uq_guild_config_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id"))
    key: Mapped[str] = mapped_column(String(120))
    value: Mapped[dict] = mapped_column(JSON, default=dict)
