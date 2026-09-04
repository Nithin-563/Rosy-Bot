"""Provider manager: resolves a provider for a guild/DM and handles fallback."""

import logging
from typing import Optional

from ..config import get_settings
from ..db import encryption
from .base import ChatMessage, ChatProvider, ChatResult
from .providers import PROVIDER_CONFIGS, OpenAICompatProvider

logger = logging.getLogger("rosy.ai.manager")


class AIProviderManager:
    """Creates provider instances from settings or stored guild credentials."""

    def __init__(self) -> None:
        self._cache: dict[tuple[Optional[int], str], ChatProvider] = {}

    def _build(
        self, provider: str, api_key: str, model: str | None, base_url: str | None
    ) -> ChatProvider:
        if provider not in PROVIDER_CONFIGS:
            raise ValueError(f"Unknown provider: {provider}")
        cfg = PROVIDER_CONFIGS[provider]
        resolved_model = model or cfg.default_model
        resolved_base = base_url or cfg.base_url
        return OpenAICompatProvider(
            api_key=api_key, model=resolved_model, base_url=resolved_base
        )

    def get_default_provider(self) -> ChatProvider:
        """Provider from global environment settings."""
        settings = get_settings()
        provider = settings.default_provider
        return self._build(
            provider,
            settings.provider_api_key(provider),
            settings.default_model,
            getattr(settings, f"{provider}_base_url", None),
        )

    async def resolve(
        self,
        *,
        guild_id: Optional[int] = None,
        stored_provider: Optional[str] = None,
        stored_model: Optional[str] = None,
        session=None,
    ) -> ChatProvider:
        """Resolve a provider, preferring per-guild stored credentials.

        ``stored_provider``/``stored_model`` come from the Guild record. If a
        matching encrypted credential row exists we use it; otherwise we fall
        back to the global default provider.
        """
        settings = get_settings()
        provider_name = stored_provider or "default"

        if provider_name == "default" or not provider_name:
            return self.get_default_provider()

        # Try to find guild credential override.
        if guild_id is not None and session is not None:
            try:
                from ..db.models import AIProviderCredential

                stmt = AIProviderCredential.__table__.select().where(
                    AIProviderCredential.__table__.c.guild_id == guild_id,
                    AIProviderCredential.__table__.c.provider == provider_name,
                    AIProviderCredential.__table__.c.is_active.is_(True),
                )
                row = (await session.execute(stmt)).first()
                if row is not None:
                    api_key = encryption.decrypt(row.api_key_enc)
                    model = stored_model or row.model
                    base_url = row.base_url
                    return self._build(provider_name, api_key, model, base_url)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to resolve guild provider; falling back.")

        # Fall back to env key for the named provider.
        api_key = settings.provider_api_key(provider_name)
        if not api_key:
            return self.get_default_provider()
        model = stored_model or getattr(settings, f"{provider_name}_model", None)
        base_url = getattr(settings, f"{provider_name}_base_url", None)
        return self._build(provider_name, api_key, model, base_url)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        provider: Optional[ChatProvider] = None,
        temperature: float = 0.8,
        max_tokens: int | None = None,
        tools: list[dict] | None = None,
    ) -> ChatResult:
        provider = provider or self.get_default_provider()
        try:
            return await provider.chat(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )
        except Exception:
            logger.exception("Chat request failed on %s", provider.name)
            raise
