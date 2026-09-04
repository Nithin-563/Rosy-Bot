"""Provider router — selects the active provider for a guild and handles fallback."""
from __future__ import annotations

import logging
from typing import Sequence

from rosy.ai.base import BaseProvider, ChatResponse, Message, ProviderError, ToolDef
from rosy.ai.factory import ProviderRegistry

log = logging.getLogger(__name__)


class ProviderRouter:
    """Resolves and caches providers, applies per-guild overrides, and fails over.

    Resolution order for a request:
      1. Explicit provider/model override supplied at call time.
      2. Per-guild ProviderConfig (if any credential/override exists).
      3. Global default from settings.
    """

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()
        self._cache: dict[str, BaseProvider] = {}

    def resolve(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        guild_id: int | None = None,
    ) -> BaseProvider:
        """Return a provider instance for the given override + guild context."""
        chosen = provider or "default"
        cache_key = f"{chosen}:{model or ''}:{guild_id or ''}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        inst = self.registry.build(chosen, api_key=api_key, base_url=base_url, model=model)
        self._cache[cache_key] = inst
        return inst

    async def complete(
        self,
        messages: list[Message],
        *,
        tools: list[ToolDef] | None = None,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        guild_id: int | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        fallbacks: Sequence[str] | None = None,
    ) -> ChatResponse:
        """Run a completion, retrying on configured fallback providers."""
        primary = self.resolve(
            provider=provider, model=model, api_key=api_key, base_url=base_url, guild_id=guild_id
        )
        candidates: list[BaseProvider] = [primary]
        for fb in fallbacks or []:
            try:
                candidates.append(
                    self.resolve(provider=fb, model=None, guild_id=guild_id)
                )
            except ValueError as exc:
                log.warning("Fallback provider unavailable: %s", exc)

        last_error: Exception | None = None
        for inst in candidates:
            try:
                return await inst.complete(
                    messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model,
                )
            except ProviderError as exc:
                last_error = exc
                log.warning("Provider %s failed, trying next: %s", inst.name, exc)
        raise ProviderError(f"All providers failed: {last_error}")
