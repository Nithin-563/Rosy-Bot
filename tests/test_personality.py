"""Personality engine tests."""
from __future__ import annotations

from rosy.personality.manager import PersonalityManager, PERSONALITY_MODES


def test_valid_modes():
    assert "friendly" in PERSONALITY_MODES
    assert "technical" in PERSONALITY_MODES
    assert len(PERSONALITY_MODES) >= 11


def test_default_mode_fallback():
    pm = PersonalityManager(default_mode="invalid-mode")
    assert pm.default_mode == "friendly"


def test_system_prompt_identity():
    pm = PersonalityManager()
    sp = pm.system_prompt("technical")
    assert "Rosy" in sp
    assert "AI" in sp or "artificial intelligence" in sp.lower()


def test_suggest_mode():
    pm = PersonalityManager()
    # Help/support cues take priority over technical cues.
    assert pm.suggest_mode("help me fix this error in python") == "supportive"
    assert pm.suggest_mode("lol that's so funny") == "humorous"
    assert pm.suggest_mode("what's a good way to deploy a python api") == "technical"


def test_effective_mode():
    pm = PersonalityManager()
    assert pm.effective_mode("professional", "how do i deploy this code") == "supportive"
    assert pm.effective_mode("professional", "casual chit chat") == "professional"
