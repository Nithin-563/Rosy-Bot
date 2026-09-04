"""Configuration tests."""

import pytest

from rosy.config import get_settings, PERSONALITY_MODES


def test_default_provider_prefers_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    get_settings.cache_clear()
    s = get_settings()
    assert s.default_provider == "openrouter"
    assert s.default_model == s.openrouter_model
    get_settings.cache_clear()


def test_personality_modes_are_valid():
    for mode in ("friendly", "casual", "technical", "serious", "professional"):
        assert mode in PERSONALITY_MODES
