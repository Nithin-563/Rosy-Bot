# Rosy configuration — all values come from environment variables.
# See .env.example for the full documented list and README.md for setup.

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Discord ---
    # Empty by default so the package can be imported in tests; the runner
    # (main.py) validates that a token is present before starting.
    discord_token: str = Field(default="", description="Discord bot token (required at runtime).")
    discord_command_prefix: str = "!"
    discord_app_id: str | None = None
    discord_public_key: str | None = None

    # --- Default AI provider (OpenRouter) ---
    ai_default_provider: str = "openrouter"
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openrouter/auto"
    openrouter_default_model: str = "openrouter/auto"

    # Optional provider keys (all optional; used only when configured).
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    mistral_api_key: str | None = None
    mistral_model: str = "mistral-small-latest"

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./rosy_dev.db"
    # Override at deploy time, e.g. postgresql+asyncpg://user:pass@host:5432/rosy

    # --- Security / crypto ---
    # Secret used to derive the Fernet key encrypting stored credentials.
    encryption_key: str | None = None
    # Rate limiting.
    rate_limit_max: int = 20
    rate_limit_window_seconds: int = 60

    # --- Conversation / memory ---
    max_context_messages: int = 12
    max_context_tokens: int = 6000
    memory_top_k: int = 8
    summarization_threshold_messages: int = 40
    response_min_confidence: float = 0.35

    # --- Autonomous participation ---
    auto_reply_default: bool = False

    # --- Web search ---
    tavily_api_key: str | None = None
    brave_api_key: str | None = None
    serper_api_key: str | None = None

    # --- Observability ---
    log_level: LogLevel = "INFO"
    log_json: bool = False
    sentry_dsn: str | None = None

    # --- Runtime ---
    sql_echo: bool = False

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def default_provider_name(self) -> str:
        return self.ai_default_provider.lower()


@lru_cache
def get_settings() -> Settings:
    return Settings()


def normalize_database_url(url: str) -> str:
    """Force a URL onto an async driver so the bot runs anywhere.

    Railway's Postgres plugin provides a *sync* URL such as
    ``postgresql://user:pass@host:5432/db``. Our engine is async (asyncpg), so a
    plain ``postgresql://`` prefix would make SQLAlchemy try to import the
    ``psycopg2`` sync driver, which is not installed. Rewrite it to the async
    dialect instead. SQLite URLs pass through unchanged.
    """
    url = (url or "").strip()
    for prefix in ("postgresql://", "postgres://", "postgresql+psycopg2://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url[len(prefix):]
    return url
