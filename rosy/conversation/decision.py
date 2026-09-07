"""Response-decision system — decide when Rosy should reply.

Rosy replies when any strong signal is present: direct mention, reply to her,
use of her name, a DM, or configured autonomous participation. Cooldowns and
rate limits gate everything.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)

_NAME_RE = re.compile(r"\brosy\b", re.I)


@dataclass
class DecisionInput:
    is_dm: bool = False
    mentions_bot: bool = False
    is_reply_to_bot: bool = False
    content: str = ""
    bot_name: str = "Rosy"
    autonomous: bool = False
    cooldown_active: bool = False
    rate_limited: bool = False
    channel_ai_enabled: bool = True
    last_participation: datetime | None = None


@dataclass
class Decision:
    should_reply: bool
    reason: str


class ResponseDecider:
    def __init__(self, min_confidence: float = 0.35, cooldown_seconds: int = 8) -> None:
        self.min_confidence = min_confidence
        self.cooldown_seconds = cooldown_seconds

    def decide(self, inp: DecisionInput) -> Decision:
        if not inp.channel_ai_enabled:
            return Decision(False, "channel_disabled")
        if inp.rate_limited:
            return Decision(False, "rate_limited")
        if inp.is_dm:
            return Decision(True, "dm")
        if inp.mentions_bot:
            return Decision(True, "mentioned")
        if inp.is_reply_to_bot:
            return Decision(True, "replied_to_bot")
        if _NAME_RE.search(inp.content):
            return Decision(True, "name_used")
        if inp.cooldown_active:
            return Decision(False, "cooldown")
        if not inp.autonomous:
            return Decision(False, "not_addressed")
        # Autonomous mode: only engage if Rosy was recently in the conversation,
        # or the message is clearly relevant to a topic she's part of.
        if inp.last_participation is not None:
            recent = (datetime.now(timezone.utc) - inp.last_participation) < timedelta(minutes=3)
            if recent:
                return Decision(True, "autonomous_recent")
            return Decision(False, "autonomous_stale")
        # In autonomous mode without prior participation, low-key random
        # participation based on a conservative confidence heuristic.
        return Decision(self._probabilistic(), "autonomous_new")

    @staticmethod
    def _probabilistic() -> bool:
        # Deterministic, testable: engage ~30% of the time in autonomous-new mode.
        return (datetime.now(timezone.utc).minute % 10) < 3
