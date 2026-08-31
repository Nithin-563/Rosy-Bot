"""Shared, reusable exceptions and error utilities."""

from __future__ import annotations


class RosyError(Exception):
    """Base class for all Rosy errors."""


class ConfigError(RosyError):
    """Invalid or missing configuration."""


class DatabaseError(RosyError):
    """Database operation failed."""


class AIProviderError(RosyError):
    """An AI provider call failed."""

    def __init__(self, message: str, *, provider: str | None = None) -> None:
        super().__init__(message)
        self.provider = provider


class ProviderRateLimited(AIProviderError):
    """Provider returned a rate-limit / overloaded response."""


class ProviderUnavailable(AIProviderError):
    """Provider could not be reached."""


class ProviderAuthError(AIProviderError):
    """Provider rejected credentials."""


class PermissionDenied(RosyError):
    """Caller lacks the required permission."""


class NotFound(RosyError):
    """Requested resource was not found."""


class ToolError(RosyError):
    """A tool failed to execute safely."""


class RateLimitExceeded(RosyError):
    """The caller exceeded a configured rate limit."""


def safe_user_message(exc: Exception) -> str:
    """Return a safe, user-facing message that never leaks internals."""
    if isinstance(exc, PermissionDenied):
        return "You do not have permission to do that."
    if isinstance(exc, ProviderRateLimited):
        return "Rosy's AI service is busy right now. Try again in a moment."
    if isinstance(exc, ProviderUnavailable):
        return "Rosy couldn't reach the AI service. Try again shortly."
    if isinstance(exc, ProviderAuthError):
        return "The AI service is not configured correctly. Ask an admin."
    if isinstance(exc, AIProviderError):
        return "Rosy hit an AI service error. Try again shortly."
    if isinstance(exc, RateLimitExceeded):
        return "You're sending messages too quickly. Please slow down."
    if isinstance(exc, RosyError):
        return str(exc)
    # Unknown exceptions: never leak stack traces to users.
    return "Something went wrong on my end. Please try again."