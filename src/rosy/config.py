"""Rosy configuration.

All runtime configuration is loaded from environment variables (or a `.env`
file) via pydantic-settings. Nothing sensitive is hard-coded.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_prefix="ROS_",
    )

    # --- Core ---
    discord_token: str = Field(
        validation_alias=AliasChoices("ROS_DISCORD_TOKEN", "DISCORD_TOKEN"),
        description="Discord bot token from the Developer Portal.",
    )
    app_id: int | None = None
    # Comma separated list of guild ids to register slash commands in (development).
    dev_guild_ids: str = ""
    default_prefix: str = "!"

    # --- Intents ---
    enable_message_intent: bool = True
    enable_member_intent: bool = True
    enable_voice_state_intent: bool = True
    enable_message_content_intent: bool = True
    enable_guilds_intent: bool = True
    enable_moderation_intent: bool = True

    # --- Database ---
    # Prefers ROS_DATABASE_URL, then falls back to Railway's standard
    # DATABASE_URL, then to the local default.
    database_url: str = Field(
        default="postgresql+asyncpg://rosy:rosy@localhost:5432/rosy",
        description="SQLAlchemy async database URL.",
    )

    @model_validator(mode="after")
    def _apply_database_url_fallback(self) -> Settings:
        placeholder = "postgresql+asyncpg://rosy:rosy@localhost:5432/rosy"
        if self.database_url == placeholder:
            env_url = os.environ.get("DATABASE_URL")
            if env_url:
                # Railway's URL is postgres://... not asyncpg; adapt the driver.
                self.database_url = env_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self

    # --- Encryption (used for at-rest credential encryption) ---
    # Provide a stable 32-byte base64 key. If empty, a random key is derived
    # per-process (secrets stored in DB will not survive restarts).
    encryption_key: str = ""
    # Salt for deterministic key derivation; keep stable across restarts.
    encryption_salt: str = "rosy-encryption-salt"

    # --- Default AI provider ---
    default_provider: str = "openrouter"
    default_model: str = "openrouter/auto"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_referer: str = "https://rosy.bot"
    openrouter_title: str = "Rosy"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_default_model: str = "gpt-4o-mini"

    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_default_model: str = "gemini-1.5-flash"

    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    anthropic_default_model: str = "claude-3-5-haiku-latest"

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_default_model: str = "llama-3.1-8b-instant"

    mistral_api_key: str = ""
    mistral_base_url: str = "https://api.mistral.ai/v1"
    mistral_default_model: str = "mistral-small-latest"

    # --- Conversation ---
    max_context_messages: int = 20
    max_context_tokens: int = 6000
    response_cooldown_seconds: int = 4
    mention_threshold: int = 1
    allow_autonomous: bool = True
    autonomous_probability: float = 0.15
    temperature: float = 0.85

    # --- Memory ---
    default_importance: float = 0.5
    memory_max_per_scope: int = 200
    memory_summary_chunk: int = 30

    # --- Web / Tools ---
    web_search_enabled: bool = True
    http_timeout_seconds: float = 15.0
    max_file_bytes: int = 8 * 1024 * 1024

    # --- Voice / Music ---
    ffmpeg_path: str = "ffmpeg"
    ytdlp_path: str = "yt-dlp"
    music_max_queue: int = 50
    tts_enabled: bool = False
    tts_voice: str = "en-US-JennyNeural"

    # --- Moderation / Rate limits ---
    command_rate_limit_per_minute: int = 10
    dm_rate_limit_per_minute: int = 20

    # --- Logging ---
    log_level: str = "INFO"
    log_json: bool = False

    # --- Health / Service ---
    health_port: int = Field(default=8080, validation_alias=AliasChoices("ROS_HEALTH_PORT", "PORT"))
    health_bind_host: str = "0.0.0.0"

    @property
    def intents(self) -> int:
        """Bitmask of intents to enable (kept for validation/tests)."""
        # Real intents are built in bot.py from the individual flags.
        mask = 0
        if self.enable_guilds_intent:
            mask |= 1 << 0
        return mask

    def guild_ids(self) -> list[int]:
        return [int(x) for x in self.dev_guild_ids.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()