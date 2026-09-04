"""Central environment-based configuration for Rosy.

All configuration comes from environment variables via pydantic-settings so the
bot runs identically in dev and on Railway. Secrets are never hard-coded.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

PERSONALITY_MODES = {
    "friendly",
    "casual",
    "humorous",
    "playful",
    "excited",
    "curious",
    "serious",
    "professional",
    "supportive",
    "calm",
    "technical",
}

# provider key -> attr for default model
PROVIDER_DEFAULTS = {
    "openrouter": "openrouter_model",
    "openai": "openai_model",
    "gemini": "gemini_model",
    "anthropic": "anthropic_model",
    "groq": "groq_model",
    "mistral": "mistral_model",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Discord
    discord_token: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://rosy:rosy@localhost:5432/rosy"
    encryption_key: str = ""

    # AI - OpenRouter default
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Optional providers
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-latest"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    mistral_api_key: str = ""
    mistral_model: str = "mistral-small-latest"

    # Behaviour
    ros_personality: str = "casual"
    ros_autonomous_replies: bool = False
    ros_image_gen_enabled: bool = False
    ros_autonomous_cooldown: int = 45

    # Misc
    log_level: str = "INFO"
    ai_timeout: float = 30.0
    web_search_timeout: float = 10.0
    max_history_messages: int = 20
    max_context_tokens: int = 4000

    @property
    def default_provider(self) -> str:
        # Prefer OpenRouter; fall back to whichever provider has a key.
        if self.openrouter_api_key:
            return "openrouter"
        for key in PROVIDER_DEFAULTS:
            if getattr(self, f"{key}_api_key"):
                return key
        return "openrouter"

    @property
    def default_model(self) -> str:
        provider = self.default_provider
        attr = PROVIDER_DEFAULTS[provider]
        return getattr(self, attr)

    def provider_api_key(self, provider: str) -> str:
        return getattr(self, f"{provider}_api_key", "")

    @property
    def personality_valid(self) -> bool:
        return self.ros_personality in PERSONALITY_MODES


@lru_cache
def get_settings() -> Settings:
    return Settings()
