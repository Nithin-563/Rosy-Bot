"""Application settings loaded from environment variables.

This module provides validated settings for the entire application using Pydantic.
It ensures all required configuration is present at startup and provides helpful
error messages for missing values.
"""

import os
import secrets
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Discord Configuration
    discord_bot_token: str = Field(
        default="",
        description="Your Discord bot token from the Discord Developer Portal",
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/rosy_bot",
        description="PostgreSQL connection URL (use postgresql+asyncpg:// for async)",
    )

    # AI Provider Configuration
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key for AI requests",
    )
    openrouter_default_model: str = Field(
        default="openrouter/auto",
        description="Default AI model (OpenRouter free routing model)",
    )
    openrouter_site_url: str = Field(
        default="https://github.com/rosy-bot/rosy",
        description="Site URL for OpenRouter requests",
    )
    openrouter_site_name: str = Field(
        default="Rosy Bot",
        description="Site name for OpenRouter requests",
    )

    # Security Configuration
    encryption_secret: str = Field(
        default="",
        description="Secret key for encrypting stored API keys",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    log_format: str = Field(
        default="json",
        description="Log format: json, console",
    )

    # Bot Configuration
    bot_owner_id: str = Field(
        default="",
        description="Bot owner Discord user ID",
    )
    command_prefix: str = Field(
        default="!",
        description="Command prefix for text commands",
    )
    max_history_messages: int = Field(
        default=50,
        description="Maximum conversation history messages to keep per user",
    )
    max_memory_items: int = Field(
        default=100,
        description="Maximum memory items per user per guild",
    )

    # FastAPI Health Check
    health_host: str = Field(
        default="0.0.0.0",
        description="Host for health check server",
    )
    health_port: int = Field(
        default=8080,
        description="Port for health check server (Railway provides PORT env var)",
    )
    enable_health_check: bool = Field(
        default=True,
        description="Enable/disable health check endpoint",
    )

    @property
    def port(self) -> int:
        """Get port from Railway's PORT env var or default."""
        import os
        return int(os.environ.get("PORT", self.health_port))

    @field_validator("database_url", mode="before")
    @classmethod
    def convert_database_url_for_asyncpg(cls, v: str) -> str:
        """Convert DATABASE_URL for asyncpg compatibility (Railway auto-provides)."""
        if not v:
            return "postgresql+asyncpg://postgres:password@localhost:5432/rosy_bot"
        # Railway provides postgresql://, convert to postgresql+asyncpg://
        if v.startswith("postgresql://") and "asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got: {v}")
        return upper_v

    @field_validator("encryption_secret")
    @classmethod
    def validate_encryption_secret(cls, v: str) -> str:
        """Validate encryption secret length for security."""
        if v and len(v) < 32:
            raise ValueError(
                "ENCRYPTION_SECRET must be at least 32 characters long for security"
            )
        return v

    def validate_required(self) -> list[str]:
        """Validate all required configuration is present.
        
        Returns a list of missing configuration names.
        Note: ENCRYPTION_SECRET is optional - a default will be generated.
        """
        missing: list[str] = []
        
        if not self.discord_bot_token:
            missing.append("DISCORD_BOT_TOKEN")
        
        if not self.openrouter_api_key:
            missing.append("OPENROUTER_API_KEY")
        
        # ENCRYPTION_SECRET is optional - will use default if not provided
        # Only warn if they want to encrypt stored API keys
        
        return missing

    def get_required_error_message(self) -> str:
        """Generate a helpful error message for missing configuration."""
        missing = self.validate_required()
        if not missing:
            return ""
        
        lines = [
            "=" * 60,
            "Rosy Bot - Missing Required Configuration",
            "=" * 60,
            "",
            "The following environment variables are required but not set:",
            "",
        ]
        
        for var in missing:
            lines.append(f"  • {var}")
        
        lines.extend([
            "",
            "Please set these variables in your .env file or environment.",
            "See .env.example for reference.",
            "",
            "Quick setup:",
            f"  1. Copy .env.example to .env",
            f"  2. Fill in your values",
            f"  3. Generate encryption secret with:",
            f"     python -c \"import secrets; print(secrets.token_hex(32))\"",
            "=" * 60,
        ])
        
        return "\n".join(lines)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    This function uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
