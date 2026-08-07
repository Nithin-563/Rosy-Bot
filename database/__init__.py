"""Database module for Rosy Discord Bot.

This module provides database connection management, session handling,
and SQLAlchemy model definitions for all persistent data.
"""

from database.base import Base, BaseModel
from database.session import get_session, AsyncSessionLocal, engine
from database.models import (
    Guild,
    User,
    Conversation,
    Message,
    Memory,
    AIProvider,
    APIKey,
    PersonalityPreference,
    Log,
    Reminder,
    GuildSetting,
)

__all__ = [
    "Base",
    "BaseModel",
    "get_session",
    "AsyncSessionLocal",
    "engine",
    "Guild",
    "User",
    "Conversation",
    "Message",
    "Memory",
    "AIProvider",
    "APIKey",
    "PersonalityPreference",
    "Log",
    "Reminder",
    "GuildSetting",
]