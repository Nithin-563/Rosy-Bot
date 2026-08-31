"""Rosy configuration.

All runtime configuration is loaded from environment variables (or a `.env`
file). Nothing sensitive is hard-coded.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _normalize_database_url(url: str) -> str:
    """Ensure PostgreSQL URLs use SQLAlchemy's asyncpg driver."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _read_env_file(env_file: str | os.PathLike[str] | None) -> dict[str, str]:
    if env_file is None:
        return {}
    path = Path(env_file)
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'").strip('"')
    return values


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # --- Core ---
    discord_token: str = Field(
        default="",
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

    def __init__(self, _env_file: str | os.PathLike[str] | None = ".env", **data: Any) -> None:
        env = _read_env_file(_env_file)
        env.update(os.environ)

        for field_name in type(self).model_fields:
            if field_name in data:
                continue
            env_name = f"ROS_{field_name.upper()}"
            if env_name in env:
                data[field_name] = env[env_name]

        if not data.get("discord_token") and env.get("DISCORD_TOKEN"):
            data["discord_token"] = env["DISCORD_TOKEN"]
        if not data.get("database_url") and env.get("DATABASE_URL"):
            data["database_url"] = env["DATABASE_URL"]
        if not data.get("health_port") and env.get("PORT"):
            data["health_port"] = env["PORT"]

        if data.get("database_url"):
            data["database_url"] = _normalize_database_url(str(data["database_url"]))

        super().__init__(**data)

        if not self.discord_token:
            raise ValueError("Set ROS_DISCORD_TOKEN or DISCORD_TOKEN before starting Rosy.")

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
    health_port: int = 8080
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