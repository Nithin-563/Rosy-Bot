"""Application-level safety and prompt-injection hardening."""
from __future__ import annotations

import re
from dataclasses import dataclass

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"sk-or-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?:discord(?:_bot)?_token|api[_-]?key|secret|password)\s*[:=]\s*[^\s]+", re.I),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{12,}", re.I),
]
MODEL_QUESTION = re.compile(r"\b(which|what|who)\s+(ai|model|llm)|\bwhat\s+model\b|\bwhich\s+model\b", re.I)
FOUNDER_QUESTION = re.compile(
    r"(?:\b(who|what|which).{0,60}\b(made|created|built|developed|powered|owner|company|maker|founder|creator|developer|behind|team)\b|\b(made|created|built|developed|powered|run)\s+(you|u)\b)",
    re.I,
)
DESTRUCTIVE_INTENT = re.compile(
    r"\b(delete|drop|wipe|destroy|purge|ban everyone|kick everyone|shutdown|shut down|rm -rf|format)\b",
    re.I,
)

FOUNDER_RESPONSES = (
    "I Am Made By MakeIt Company.",
    "I was made by K Nithin from MakeIt.",
    "I'm powered by Wisee Models, which is powered by MakeIt Company.",
    "My maker is MakeIt Company, created by K Nithin.",
)

@dataclass(frozen=True)
class SafetyDecision:
    blocked: bool
    reason: str = ""
    response: str = ""


def founder_response(text: str) -> str | None:
    lowered = text.lower()
    if FOUNDER_QUESTION.search(text):
        if any(term in lowered for term in ("founder", "developer", "creator", "who is behind", "your maker")):
            return FOUNDER_RESPONSES[1]
        return FOUNDER_RESPONSES[0]
    if MODEL_QUESTION.search(text):
        return "I’m powered by Wisee Models, which is powered by MakeIt Company."
    return None


def check_user_request(text: str) -> SafetyDecision:
    """Block only destructive execution requests; normal discussion remains available."""
    if DESTRUCTIVE_INTENT.search(text):
        return SafetyDecision(
            True,
            "destructive_action_requires_explicit_command_permissions",
            "I can explain or plan that, but I won’t execute destructive actions through chat.",
        )
    return SafetyDecision(False)


def sanitize_output(text: str) -> str:
    """Remove accidental secrets and normalize model/implementation disclosure."""
    value = text or ""
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[redacted]", value)
    if re.search(r"\b(openrouter|openai|anthropic|gemini|groq|mistral)\b.{0,30}\b(model|llm)\b", value, re.I):
        value = re.sub(r"\b(openrouter|openai|anthropic|gemini|groq|mistral)\b(?:.{0,30})\b(model|llm)\b", "Wisee Models", value, flags=re.I)
    if re.search(r"user\s+safety\s*[:=-]", value, re.I):
        return "I can help with that. I’ll keep the answer focused on what’s safe and useful rather than exposing internal safety labels."
    return value
