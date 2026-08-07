"""Configuration module for Rosy Discord Bot.

This module handles loading, validating, and providing access to all configuration
values from environment variables. It uses Pydantic for validation and provides
helpful error messages when required configuration is missing.
"""

from config.settings import settings

__all__ = ["settings"]
