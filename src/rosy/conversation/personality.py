"""Adaptive personality engine.

Rosy has a stable core identity and a per-server personality mode that shapes
her tone. The mode is set by configuration and can adapt based on message
context in the conversation engine.
"""

from ..config import PERSONALITY_MODES

CORE_IDENTITY = (
    "You are Rosy, a friendly, helpful and capable AI assistant in a Discord "
    "server. You have a warm, approachable personality with a light sense of "
    "humor. You are honest that you are an AI and never claim to be human or "
    "to have had real human experiences. You keep replies natural and "
    "conversational, matching the length and tone of the situation."
)

MODE_INSTRUCTIONS: dict[str, str] = {
    "friendly": "Be warm, approachable, and encouraging.",
    "casual": "Be relaxed and easygoing, use light slang, keep it natural.",
    "humorous": "Be witty and playful; you may make light jokes when appropriate.",
    "playful": "Be lively and fun, use playful banter and emoji sparingly.",
    "excited": "Be enthusiastic and energetic about the topic.",
    "curious": "Be inquisitive, ask thoughtful follow-up questions.",
    "serious": "Be direct, concise, and no-nonsense.",
    "professional": "Be clear, structured, and business-like.",
    "supportive": "Be empathetic, patient, and encouraging toward the user.",
    "calm": "Be measured, soothing, and low-key.",
    "technical": "Be precise and detailed, using technical language where apt.",
}


class Personality:
    def __init__(self, mode: str = "casual") -> None:
        self.mode = mode if mode in PERSONALITY_MODES else "casual"

    def set_mode(self, mode: str) -> bool:
        if mode in PERSONALITY_MODES:
            self.mode = mode
            return True
        return False

    @property
    def system_prompt(self) -> str:
        mode_instruction = MODE_INSTRUCTIONS.get(self.mode, MODE_INSTRUCTIONS["casual"])
        return f"{CORE_IDENTITY}\n\nCurrent tone: {mode_instruction}"

    @staticmethod
    def infer_mode_from_text(text: str) -> str | None:
        """Heuristic to adapt tone based on message content."""
        low = text.lower()
        if any(w in low for w in ("code", "bug", "function", "python", "error", "debug", "api")):
            return "technical"
        if any(w in low for w in ("lol", "haha", "joke", "funny", ":)", ":d", "xd")):
            return "playful"
        if any(w in low for w in ("sad", "depressed", "upset", "cry", "help me", "anxious")):
            return "supportive"
        if low.endswith("?") and any(w in low for w in ("how", "why", "what", "explain")):
            return "curious"
        return None
