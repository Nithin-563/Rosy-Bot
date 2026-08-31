"""AI service layer.

Resolves per-guild (or global) provider configuration, builds a `Provider`,
handles fallback, and records usage. It depends on the credential store for
decrypting stored keys.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from rosy.ai.base import (
    ChatMessage,
    ChatResult,
    ProviderConfig,
    ProviderRegistry,
)
from rosy.config import Settings
from rosy.core.errors import AIProviderError

logger = logging.getLogger("rosy.ai.manager")


class CredentialStore:
    """Resolves provider credentials.

    Precedence: stored DB credentials (per guild) > environment variables.
    """

    def __init__(self, settings: Settings, db) -> None:
        self.settings = settings
        self.db = db

    def _env_credentials(self, provider: str) -> dict:
        s = self.settings
        by_provider = {
            "openrouter": (s.openrouter_api_key, s.openrouter_base_url, s.default_model),
            "openai": (s.openai_api_key, s.openai_base_url, s.openai_default_model),
            "gemini": (s.gemini_api_key, s.gemini_base_url, s.gemini_default_model),
            "anthropic": (s.anthropic_api_key, s.anthropic_base_url, s.anthropic_default_model),
            "groq": (s.groq_api_key, s.groq_base_url, s.groq_default_model),
            "mistral": (s.mistral_api_key, s.mistral_base_url, s.mistral_default_model),
        }
        key, base, model = by_provider.get(provider, ("", "", ""))
        extra = {}
        if provider == "openrouter":
            extra = {"referer": s.openrouter_referer, "title": s.openrouter_title}
        return {"api_key": key, "base_url": base, "model": model, "extra": extra}

    async def resolve(self, provider: str, guild_id: int | None, model: str = "") -> ProviderConfig:
        """Build a ProviderConfig, preferring DB-stored guild credentials."""
        if guild_id is not None:
            db_cred = await self._db_credentials(provider, guild_id)
            if db_cred is not None:
                return db_cred
        env = self._env_credentials(provider)
        if not env["api_key"]:
            raise AIProviderError(
                f"Provider '{provider}' has no API key configured.",
                provider=provider,
            )
        return ProviderConfig(
            provider=provider,
            api_key=env["api_key"],
            base_url=env["base_url"],
            model=model or env["model"],
            extra=env["extra"],
        )

    async def _db_credentials(self, provider: str, guild_id: int) -> ProviderConfig | None:
        from rosy.core import decrypt

        async with self.db.session() as session:
            from sqlalchemy import select

            from rosy.models import ProviderCredential

            res = await session.execute(
                select(ProviderCredential).where(
                    ProviderCredential.guild_id == guild_id,
                    ProviderCredential.provider == provider,
                )
            )
            row = res.scalar_one_or_none()
            if row is None:
                return None
            try:
                key = decrypt(row.api_key_cipher)
            except ValueError:
                logger.warning("Could not decrypt stored credential for guild=%s provider=%s", guild_id, provider)
                return None
            env = self._env_credentials(provider)
            return ProviderConfig(
                provider=provider,
                api_key=key,
                base_url=row.base_url or env["base_url"],
                model=row.default_model or env["model"],
                extra=env["extra"],
            )


class AIManager:
    """High-level AI facade used by the conversation engine."""

    def __init__(self, settings: Settings, db, registry: ProviderRegistry | None = None) -> None:
        self.settings = settings
        self.db = db
        self.registry = registry or ProviderRegistry()
        self.credentials = CredentialStore(settings, db)
        self._http: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._http = httpx.AsyncClient(timeout=self.settings.http_timeout_seconds)

    async def stop(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None:
            raise RuntimeError("AIManager not started.")
        return self._http

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        provider: str | None = None,
        model: str = "",
        guild_id: int | None = None,
        temperature: float | None = None,
        tools: list[dict] | None = None,
    ) -> ChatResult:
        provider = provider or self.settings.default_provider
        try:
            cfg = await self.credentials.resolve(provider, guild_id, model)
        except AIProviderError:
            raise
        prov = self.registry.create(cfg.provider, cfg, self.http)
        try:
            result = await prov.chat(messages, temperature=temperature, tools=tools)
        except AIProviderError:
            # fallback: try the default provider if a per-guild one failed
            if provider != self.settings.default_provider and self.settings.default_provider:
                return await self.chat(
                    messages,
                    provider=self.settings.default_provider,
                    model=model,
                    guild_id=None,
                    temperature=temperature,
                    tools=tools,
                )
            raise
        await self._record_usage(result, guild_id)
        return result

    async def _record_usage(self, result: ChatResult, guild_id: int | None) -> None:
        try:
            from rosy.models import Usage

            async with self.db.session() as session:
                session.add(
                    Usage(
                        guild_id=guild_id,
                        provider=result.provider,
                        model=result.model,
                        prompt_tokens=result.prompt_tokens,
                        completion_tokens=result.completion_tokens,
                        kind="chat",
                    )
                )
                await session.commit()
        except Exception:  # pragma: no cover - never break chat on usage failure
            logger.exception("Failed to record usage")


def from_error(exc: Exception) -> str:
    """Re-exported helper (safety wrapper)."""
    from rosy.core.errors import AIProviderError as _AE

    if isinstance(exc, _AE):
        return str(exc)
    return "AI error"