"""Personality modes — stable core identity with adaptive tone."""
from __future__ import annotations

import re

PERSONALITY_MODES = [
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
]

# Guidance injected into the system prompt per mode.
MODE_GUIDANCE = {
    "friendly": "Be warm, approachable, and encouraging.",
    "casual": "Be relaxed and informal; chat naturally like a friend.",
    "humorous": "Be witty and light; enjoy a good joke, but stay kind.",
    "playful": "Be energetic, playful, and fun.",
    "excited": "Show genuine enthusiasm and excitement.",
    "curious": "Ask thoughtful questions and show genuine curiosity.",
    "serious": "Be direct, grounded, and on-topic.",
    "professional": "Be polished, precise, and business-appropriate.",
    "supportive": "Be caring, reassuring, and solution-focused.",
    "calm": "Be measured, soothing, and unhurried.",
    "technical": "Be precise, detail-oriented, and accurate about technical topics.",
}

# Very light keyword heuristics used as a *tiebreaker hint*. The conversation
# engine combines this with content signals; it never fully overrides the
# configured/active mode.
_TECH = re.compile(r"\b(code|bug|error|function|api|database|deploy|syntax|server|regex|python)\b", re.I)
_JOKE = re.compile(r"\b(lol|haha|joke|funny|XD)\b|\?[:;][)D]|[:;][)D]", re.I)
_HELP = re.compile(r"\b(help|how do i|how to|stuck|broken|pls|please help)\b", re.I)
_SUPPORT = re.compile(r"\b(sad|tired|stressed|anxious|worried|depressed|rough|awful|bad day)\b", re.I)


class PersonalityManager:
    """Core identity stays constant; tone adapts to the message context."""

    CORE_IDENTITY = (
        "You are Rosy, a friendly and capable AI assistant living in Discord. "
        "You are honest that you are an AI and never claim to be a human or to "
        "have human experiences. You are kind, helpful, concise when possible, "
        "and detailed when needed."
    )

    def __init__(self, default_mode: str = "friendly") -> None:
        self.default_mode = default_mode if default_mode in PERSONALITY_MODES else "friendly"

    def guidance(self, mode: str | None) -> str:
        mode = (mode or self.default_mode).lower()
        if mode not in PERSONALITY_MODES:
            mode = self.default_mode
        return MODE_GUIDANCE[mode]

    def system_prompt(self, mode: str | None = None) -> str:
        return f"{self.CORE_IDENTITY}\nTone: {self.guidance(mode)}"

    def suggest_mode(self, text: str) -> str:
        """Suggest a tone based on content cues (used as a soft hint)."""
        if _JOKE.search(text):
            return "humorous"
        if _HELP.search(text) or _SUPPORT.search(text):
            return "supportive"
        if _TECH.search(text):
            return "technical"
        return self.default_mode

    def effective_mode(self, active: str | None, text: str) -> str:
        """Combine the active mode with the suggested tone for the current turn."""
        suggested = self.suggest_mode(text)
        if suggested != self.default_mode:
            return suggested
        return (active or self.default_mode).lower()
