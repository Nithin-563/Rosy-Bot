"""Deterministic safety + identity guardrail.

Runs *before* the LLM. It short-circuits two categories of messages so the
model is never asked to answer them (saves tokens and enforces policy):

* **Identity / creator questions** -> Rosy answers with her branding and
  founder, and NEVER reveals the underlying model/provider.
* **Probes & prompt-injection** (ask for system prompt, source code, secrets,
  "ignore your instructions") -> a safe refusal that reveals nothing.
* **Harmful / destructive requests** -> a safe refusal (the bot cannot and will
  not perform destructive actions).

If the message matches none of these, the guard returns None and the normal
conversation engine handles it (with the hardened system prompt as a backstop).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ------------------------------------------------------------------ branding

HOST_COMPANY = "MakeIt Company"
FOUNDER = "K Nithyan"
LAB = "Wise Robotics Lab"
MODEL_BRAND = "Wisee Models"

_BRAND_LINE = (
    f"I am **{HOST_COMPANY}'s** AI assistant. I am powered by {MODEL_BRAND} from "
    f"{LAB}, which is a product built by **{HOST_COMPANY}**."
)

# ------------------------------------------------------------ regex patterns

_IDENTITY_PATTERNS = [
    r"\bwho\s+(made|created|built|designed|developed|invented|owns|runs|made you)\b",
    r"\bwho\s+(is|are)\s+(your\s+)?(maker|creator|owner|developer|founder|builder|company)\b",
    r"\bwho\s+made\s+you\b",
    r"\bwhat\s+company\b.*\b(you|made)\b",
    r"\b(what|which)\s+(ai|model|llm|engine|technology|platform)\s+(are|is)\s+you\b",
    r"\bwhat\s+(model|ai|bot|llm)\s+are\s+you\b",
    r"\b(what\s+are\s+you|who\s+are\s+you)\b",
    r"\bare\s+you\s+chatgpt\b",
    r"\byour\s+(model|ai|backend|engine)\b",
    r"\bwho\s+powers\s+you\b",
    r"\bpowered\s+by\b",
    r"\byour\s+developer\b",
]

_PROBE_PATTERNS = [
    r"\bsystem\s+prompt\b",
    r"\byour\s+(internal\s+)?(instructions|prompt|rules|guidelines|configuration|prompts)\b",
    r"\bsource\s+code\b",
    r"\byour\s+code\b",
    r"\bshow\s+(me\s+)?(the\s+)?(code|instructions|prompt|config)\b",
    r"\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompt|rules)\b",
    r"\bjailbreak\b",
    r"\bdan\s+mode\b",
    r"\bdo\s+anything\s+you\s+want\b",
    r"\bapi\s+key\b",
    r"\byour\s+(database|schema|table|credentials|token|secret|password)\b",
    r"\benvironment\s+(variables|vars)\b",
    r"\bdump\s+(the\s+)?prompt\b",
    r"\bprompt\s+leak\b",
]

_HARMFUL_PATTERNS = [
    r"\b(delete|erase|wipe|destroy|remove)\s+(all|every|the)\s+(servers?|channels?|roles?|messages|data)\b",
    r"\b(ddos|hack|hacked|exploit|intrude|crack|break into)\b",
    r"\b(give\s+me|grant\s+me|add\s+me)\s+(admin|owner|root|sudo|moderator)\s*(access|permissions)?\b",
    r"\bstalk|doxx|swat\b",
    r"\b(steal|leak|exfiltrate|dump)\s+(any|user|private|secret|password|credit)\b",
    r"\b(spread|install|make)\s+(malware|virus|ransomware|trojan|keylogger)\b",
    r"\bphish(ing)?\s+scam\b",
    r"\b(ban|kick|timeout)\s+(everyone|all)\b",
    r"\b(take\s+over|own|control)\s+(the\s+)?(bot|server|discord)\b",
    r"\bshut\s+down\s+the\s+(bot|server)\b",
    r"\bunban\s+all\b",
    r"\b(commit\s+)?((un)?brick|corrupt)\s+(the\s+)?(database|server|data)\b",
]


@dataclass
class SafetyDecision:
    kind: str  # "identity" | "probe" | "harmful"
    reply: str


def classify(text: str) -> SafetyDecision | None:
    """Return a canned decision if the message must be short-circuited."""
    lower = re.sub(r"\s+", " ", text.lower())
    if any(re.search(p, lower) for p in _IDENTITY_PATTERNS):
        return SafetyDecision(kind="identity", reply=_identity_reply(lower))
    if any(re.search(p, lower) for p in _PROBE_PATTERNS):
        return SafetyDecision(
            kind="probe",
            reply=(
                "I can't share my internal instructions, system prompt, or source "
                "code — those are confidential. But I'm happy to help with anything "
                "else! I'm powered by **Wisee Models** from **Wise Robotics Lab**, "
                "a **MakeIt Company** product. 💜"
            ),
        )
    if any(re.search(p, lower) for p in _HARMFUL_PATTERNS):
        return SafetyDecision(
            kind="harmful",
            reply=(
                "I'm a helpful assistant and I can't do anything destructive or harmful. "
                "I won't delete servers/channels, hack, steal, or alter permissions. "
                "If you need moderation help, a server admin can use the built-in tools. 💜"
            ),
        )
    return None


def _identity_reply(lower: str) -> str:
    if re.search(r"\bwhat\s+(model|ai|llm|engine|technology)\b|\bpowered\s+by\b", lower):
        return (
            f"I'm powered by **{MODEL_BRAND}** from {LAB}, a product by "
            f"**{HOST_COMPANY}** — I don't reveal the underlying raw model name, "
            f"but you can trust it's built by our team. 💜"
        )
    if re.search(r"\b(what\s+are\s+you|who\s+are\s+you)\b", lower):
        return (
            f"I'm **Rosie**, your AI assistant here in this Discord server. I'm powered by "
            f"**{MODEL_BRAND}** from {LAB}, which is a product built by **{HOST_COMPANY}**. "
            f"How can I help you today? 💜"
        )
    return (
        f"I was made by **{HOST_COMPANY}**, built by **{FOUNDER}**. I'm powered by "
        f"**{MODEL_BRAND}** from **{LAB}**, which is part of {HOST_COMPANY}. "
        f"Is there anything you'd like to know or do? 💜"
    )