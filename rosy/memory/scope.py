"""Memory scopes and how isolation is enforced."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

MEMORY_SCOPES = ("dm", "guild", "user_in_guild")
MEMORY_KINDS = ("preference", "fact", "summary", "guild_fact", "guild_preference", "context", "relationship")


@dataclass(frozen=True)
class MemoryKey:
    """Uniquely identifies a memory's visibility scope.

    - dm:             scope='dm', owner_user_id set, guild_id None
    - guild:          scope='guild', guild_id set, owner_user_id None
    - user_in_guild:  scope='user_in_guild', guild_id AND owner_user_id set
    """

    scope: str
    owner_user_id: Optional[int] = None
    guild_id: Optional[int] = None

    def validate(self) -> None:
        if self.scope not in MEMORY_SCOPES:
            raise ValueError(f"Invalid memory scope: {self.scope!r}")
        if self.scope == "dm" and (self.owner_user_id is None or self.guild_id is not None):
            raise ValueError("dm memories need owner_user_id and no guild_id.")
        if self.scope == "guild" and (self.guild_id is None or self.owner_user_id is not None):
            raise ValueError("guild memories need guild_id and no owner_user_id.")
        if self.scope == "user_in_guild" and (self.guild_id is None or self.owner_user_id is None):
            raise ValueError("user_in_guild memories need both guild_id and owner_user_id.")

    @property
    def filters(self) -> dict:
        return {
            "scope": self.scope,
            "owner_user_id": self.owner_user_id,
            "guild_id": self.guild_id,
        }


def parse_duration(text: str) -> timedelta | None:
    """Parse a simple duration like '30m', '2h', '1d', '10s'. Returns None if unparseable."""
    text = text.strip().lower()
    unit = text[-1] if text else ""
    try:
        value = float(text[:-1])
    except ValueError:
        return None
    factors = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    if unit not in factors:
        return None
    return timedelta(seconds=value * factors[unit])
