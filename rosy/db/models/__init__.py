"""Database models. Importing this package registers all models on Base.metadata."""
from __future__ import annotations

from rosy.db.base import Base
from rosy.db.models.conversation import Conversation, ConversationMessage
from rosy.db.models.credential import Credential, ProviderConfig
from rosy.db.models.custom_command import CustomCommand
from rosy.db.models.guild import Channel, Guild, GuildPreference
from rosy.db.models.knowledge import KnowledgeRecord
from rosy.db.models.memory import Memory
from rosy.db.models.moderation import ModerationRecord
from rosy.db.models.reminder import Reminder
from rosy.db.models.usage import UsageStat
from rosy.db.models.user import User, UserPreference

__all__ = [
    "Base",
    "Channel",
    "Conversation",
    "ConversationMessage",
    "Credential",
    "CustomCommand",
    "Guild",
    "GuildPreference",
    "KnowledgeRecord",
    "Memory",
    "ModerationRecord",
    "ProviderConfig",
    "Reminder",
    "UsageStat",
    "User",
    "UserPreference",
]
