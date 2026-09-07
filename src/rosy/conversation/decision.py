"""Response-decision system.

Determines whether Rosy should respond to a message, considering mentions,
replies, name usage, autonomous participation, cooldown, and spam prevention.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

BOW_NAMES = ("rosy",)


@dataclass
class DecisionInput:
    bot_id: int
    author_id: int
    content: str
    mentions_me: bool = False
    is_reply_to_me: bool = False
    is_dm: bool = False
    is_bot: bool = False
    autonomous_enabled: bool = True
    autonomous_probability: float = 0.15
    cooldown_seconds: float = 120.0
    last_response_at: float = 0.0
    in_participating_channel: bool = True

    @property
    def cooldown_active(self) -> bool:
        return (time.monotonic() - self.last_response_at) < self.cooldown_seconds


@dataclass
class Decision:
    should: bool
    reason: str
    should_type: bool = False


class DecisionEngine:
    def __init__(self) -> None:
        pass

    def should_respond(self, inp: DecisionInput) -> Decision:
        if inp.is_bot or inp.author_id == inp.bot_id:
            return Decision(False, "bot_author")
        if inp.is_dm:
            return Decision(True, "dm", should_type=True)
        lower = inp.content.lower()
        if inp.mentions_me:
            return Decision(True, "mention", should_type=True)
        if inp.is_reply_to_me:
            return Decision(True, "reply", should_type=True)
        if any(name in lower for name in BOW_NAMES):
            return Decision(True, "name_usage", should_type=True)
        if not inp.autonomous_enabled or not inp.in_participating_channel:
            return Decision(False, "autonomous_disabled")
        if inp.cooldown_active:
            return Decision(False, "cooldown")
        if random.random() <= inp.autonomous_probability:
            return Decision(True, "autonomous", should_type=True)
        return Decision(False, "not_relevant")