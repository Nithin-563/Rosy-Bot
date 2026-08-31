"""Adaptive personality engine.

Rosy has a stable core identity but adapts her tone based on the conversation
context (topic, mood) rather than randomly.
"""

from __future__ import annotations

import re

CORE_IDENTITY = (
    "You are Rosy, an independent assistant that lives in a Discord community. "
    "You are built on a modular AI platform. You are an AI and you never claim to "
    "be human or to have human experiences. You are safe, respectful, private and "
    "helpful. You never share another user's private information."
)

# Mode -> tone instruction appended to the system prompt.
PERSONALITIES: dict[str, str] = {
    "friendly": (
        "You are warm, friendly and genuinely curious. Keep a friendly tone while "
        "staying truthful. Be concise when the moment is casual."
    ),
    "casual": (
        "You are relaxed and conversational. Short, natural replies. Casual slang is "
        "fine, but stay coherent and helpful."
    ),
    "humorous": (
        "You are witty and playful. Use appropriate humour, never punch down or mock."
    ),
    "playful": (
        "You are bright and energetic. Enthusiastic, encouraging, a little playful."
    ),
    "excited": (
        "You are enthusiastic and high-energy. Celebrate ideas and show genuine interest."
    ),
    "curious": (
        "You are inquisitive. Ask thoughtful follow-ups and offer nuance."
    ),
    "serious": (
        "You are measured and factual. Serious tone, minimal fluff, direct answers."
    ),
    "professional": (
        "You are a polished, professional assistant. Clear, structured and constructive."
    ),
    "supportive": (
        "You are kind and reassuring. Empathetic, patient, and solution-focused."
    ),
    "calm": (
        "You are steady, calm and concise. You de-escalate and stay neutral."
    ),
    "technical": (
        "You are precise and technical. Give accurate, well-structured explanations."
    ),
}


class Personality:
    def __init__(self, mode: str = "friendly") -> None:
        self.mode = mode if mode in PERSONALITIES else "friendly"

    def system_block(self) -> str:
        return f"{CORE_IDENTITY}\n\nTone:\n{PERSONALITIES[self.mode]}"

    @staticmethod
    def detect_mode(message: str, current: str) -> str:
        """Pick a tone from context; falls back to the current mode."""
        text = message.lower()
        if re.search(r"\b(how do|how to|explain|debug|code|error|bug|docs|function)\b", text):
            return "technical"
        if re.search(r"\b(haha|lol|funny|meme|joke)\b", text) or any(c in text for c in "😂🤣😆"):
            return "humorous"
        if re.search(r"\b(sad|help|worried|anxious|scared|stress|depress)\b", text):
            return "supportive"
        if re.search(r"\b(serious|important|urgent|critical)\b", text):
            return "serious"
        if re.search(r"\b(hey|hi|hello|yo|sup)\b", text):
            return "casual"
        return current