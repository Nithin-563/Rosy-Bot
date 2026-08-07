"""AI providers module for Rosy Discord Bot.

This module provides a unified interface for interacting with various AI providers
through a common abstraction layer. Each provider implements the base provider interface.
"""

from providers.base import (
    AIProviderBase,
    AIProviderType,
    AIRequest,
    AIResponse,
    ProviderConfig,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    Message,
)
from providers.openrouter import OpenRouterProvider
from providers.factory import ProviderFactory

__all__ = [
    "AIProviderBase",
    "AIProviderType",
    "AIRequest",
    "AIResponse",
    "Message",
    "ProviderConfig",
    "ProviderError",
    "RateLimitError",
    "AuthenticationError",
    "OpenRouterProvider",
    "ProviderFactory",
]
