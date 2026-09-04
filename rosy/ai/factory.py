"""Provider factory — builds provider instances from configuration."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from rosy.ai.anthropic import AnthropicProvider
from rosy.ai.base import BaseProvider
from rosy.ai.openai_compat import OpenAICompatProvider
from rosy.config import get_settings

log = logging.getLogger(__name__)


@dataclass
class ProviderRegistry:
    """Holds live provider instances and builds them from env/config."""

    settings_holder: object = field(default_factory=get_settings)

    def build(self, name: str, *, api_key: str | None = None,
              base_url: str | None = None, model: str | None = None) -> BaseProvider:
        s = get_settings()
        name = (name or s.default_provider_name).lower()
        providers = {
            "openrouter": lambda: OpenAICompatProvider(
                api_key or s.openrouter_api_key,
                base_url or s.openrouter_base_url,
                model or s.openrouter_default_model,
                provider_name="openrouter",
            ),
            "openai": lambda: OpenAICompatProvider(
                api_key or s.openai_api_key,
                base_url or "https://api.openai.com/v1",
                model or s.openai_model,
                provider_name="openai",
            ),
            "groq": lambda: OpenAICompatProvider(
                api_key or s.groq_api_key,
                base_url or "https://api.groq.com/openai/v1",
                model or s.groq_model,
                provider_name="groq",
            ),
            "mistral": lambda: OpenAICompatProvider(
                api_key or s.mistral_api_key,
                base_url or "https://api.mistral.ai/v1",
                model or s.mistral_model,
                provider_name="mistral",
            ),
            "gemini": lambda: OpenAICompatProvider(
                api_key or s.gemini_api_key,
                base_url or "https://generativelanguage.googleapis.com/v1beta/openai",
                model or s.gemini_model,
                provider_name="gemini",
            ),
            "anthropic": lambda: AnthropicProvider(
                api_key or s.anthropic_api_key,
                base_url or None,
                model or s.anthropic_model,
            ),
        }
        factory = providers.get(name)
        if factory is None:
            raise ValueError(f"Unknown AI provider: {name!r}")
        provider = factory()
        log.info("Built provider %s (model=%s)", provider.name, provider.model)
        return provider

    def default(self) -> BaseProvider:
        return self.build(get_settings().default_provider_name)
