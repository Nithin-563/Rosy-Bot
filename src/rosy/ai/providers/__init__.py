"""Concrete provider implementations.

All providers here speak the OpenAI-compatible chat completions protocol, which
OpenRouter, OpenAI, Groq, Mistral, and compatible endpoints support. Gemini and
Anthropic also expose OpenAI-compatible endpoints, so we reuse
:class:`OpenAICompatProvider` with the correct base URL.
"""

from .http import OpenAICompatProvider, ProviderConfig

PROVIDER_CONFIGS: dict[str, ProviderConfig] = {
    "openrouter": ProviderConfig(
        base_url="https://openrouter.ai/api/v1",
        default_model="openai/gpt-4o-mini",
    ),
    "openai": ProviderConfig(
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
    ),
    "gemini": ProviderConfig(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="gemini-1.5-flash",
    ),
    "anthropic": ProviderConfig(
        base_url="https://api.anthropic.com/v1",
        default_model="claude-3-5-haiku-latest",
    ),
    "groq": ProviderConfig(
        base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.1-8b-instant",
    ),
    "mistral": ProviderConfig(
        base_url="https://api.mistral.ai/v1",
        default_model="mistral-small-latest",
    ),
}

__all__ = ["OpenAICompatProvider", "PROVIDER_CONFIGS"]
