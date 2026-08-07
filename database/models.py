"""SQLAlchemy models for Rosy Discord Bot.

This module defines all database tables and their relationships.
Models are organized by domain: guild/server, users, conversations, AI, etc.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import BaseModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# =============================================================================
# Guild/Server Models
# =============================================================================

class Guild(BaseModel):
    """Represents a Discord server/guild.
    
    Stores configuration and state specific to each server the bot is in.
    """
    
    __tablename__ = "guilds"
    
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    settings: Mapped[list["GuildSetting"]] = relationship(
        "GuildSetting",
        back_populates="guild",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="guild",
        cascade="all, delete-orphan",
    )
    memories: Mapped[list["Memory"]] = relationship(
        "Memory",
        back_populates="guild",
        cascade="all, delete-orphan",
    )
    provider: Mapped[Optional["AIProvider"]] = relationship(
        "AIProvider",
        back_populates="guild",
        uselist=False,
        cascade="all, delete-orphan",
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="guild",
        cascade="all, delete-orphan",
    )
    personality: Mapped[Optional["PersonalityPreference"]] = relationship(
        "PersonalityPreference",
        back_populates="guild",
        uselist=False,
        cascade="all, delete-orphan",
    )


class GuildSetting(BaseModel):
    """Key-value settings for a specific guild.
    
    Allows flexible configuration per server.
    """
    
    __tablename__ = "guild_settings"
    
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("guilds.id", ondelete="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Relationships
    guild: Mapped["Guild"] = relationship("Guild", back_populates="settings")
    
    __table_args__ = (
        Index("ix_guild_settings_guild_key", "guild_id", "key", unique=True),
    )


# =============================================================================
# User Models
# =============================================================================

class User(BaseModel):
    """Represents a Discord user across all servers.
    
    Stores global user data and preferences.
    """
    
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    global_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_bot_owner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    memories: Mapped[list["Memory"]] = relationship(
        "Memory",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# =============================================================================
# Conversation Models
# =============================================================================

class Conversation(BaseModel):
    """Represents a conversation context.
    
    Can be per-guild, per-user, or DM conversations.
    """
    
    __tablename__ = "conversations"
    
    guild_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("guilds.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    conversation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="guild",
    )
    is_dm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    guild: Mapped[Optional["Guild"]] = relationship(
        "Guild",
        back_populates="conversations",
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="conversations",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    
    __table_args__ = (
        Index("ix_conversations_guild_user", "guild_id", "user_id"),
        Index("ix_conversations_dm", "is_dm", "user_id"),
    )


class Message(BaseModel):
    """Represents a single message in a conversation.
    
    Stores message content and metadata for AI context.
    """
    
    __tablename__ = "messages"
    
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    discord_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user",
    )
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )
    
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )


# =============================================================================
# Memory Models
# =============================================================================

class Memory(BaseModel):
    """Persistent memory storage for users and guilds.
    
    Stores important information that should persist across conversations.
    """
    
    __tablename__ = "memories"
    
    guild_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("guilds.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    guild: Mapped[Optional["Guild"]] = relationship(
        "Guild",
        back_populates="memories",
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="memories",
    )
    
    __table_args__ = (
        Index("ix_memories_guild_user", "guild_id", "user_id"),
        Index("ix_memories_type_key", "memory_type", "key"),
    )


# =============================================================================
# AI Provider Models
# =============================================================================

class AIProvider(BaseModel):
    """AI provider configuration for a guild.
    
    Stores provider-specific settings like model, API keys, etc.
    """
    
    __tablename__ = "ai_providers"
    
    guild_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("guilds.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
    )
    provider_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="openrouter",
    )
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    temperature: Mapped[float] = mapped_column(default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(default=2048, nullable=False)
    
    # Relationships
    guild: Mapped[Optional["Guild"]] = relationship(
        "Guild",
        back_populates="provider",
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="provider",
        cascade="all, delete-orphan",
    )


class APIKey(BaseModel):
    """Encrypted API key storage.
    
    Stores provider-specific API keys with encryption.
    """
    
    __tablename__ = "api_keys"
    
    guild_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("guilds.id", ondelete="CASCADE"),
        nullable=True,
    )
    provider_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("ai_providers.id", ondelete="CASCADE"),
        nullable=True,
    )
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    guild: Mapped[Optional["Guild"]] = relationship(
        "Guild",
        back_populates="api_keys",
    )
    provider: Mapped[Optional["AIProvider"]] = relationship(
        "AIProvider",
        back_populates="api_keys",
    )
    
    __table_args__ = (
        Index("ix_api_keys_guild_provider", "guild_id", "provider_name"),
    )


# =============================================================================
# Personality Models
# =============================================================================

class PersonalityPreference(BaseModel):
    """Personality configuration for a guild.
    
    Stores personality traits and behavior preferences.
    """
    
    __tablename__ = "personality_preferences"
    
    guild_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("guilds.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
    )
    personality_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="friendly",
    )
    traits: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    response_length: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )
    humor_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )
    formality_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )
    
    # Relationships
    guild: Mapped[Optional["Guild"]] = relationship(
        "Guild",
        back_populates="personality",
    )


# =============================================================================
# Logging Models
# =============================================================================

class Log(BaseModel):
    """Application log storage.
    
    Stores structured logs for debugging and analytics.
    """
    
    __tablename__ = "logs"
    
    log_level: Mapped[str] = mapped_column(String(20), nullable=False)
    logger_name: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    __table_args__ = (
        Index("ix_logs_guild_time", "guild_id", "created_at"),
        Index("ix_logs_level_time", "log_level", "created_at"),
    )


# =============================================================================
# Reminder Models
# =============================================================================

class Reminder(BaseModel):
    """Scheduled reminders for users.
    
    Stores reminder information for future notification.
    """
    
    __tablename__ = "reminders"
    
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    repeat_interval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    __table_args__ = (
        Index("ix_reminders_user_scheduled", "user_id", "scheduled_at"),
        Index("ix_reminders_completed", "is_completed", "scheduled_at"),
    )
