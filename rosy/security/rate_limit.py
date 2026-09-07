"""In-memory token-bucket style rate limiter.

Used to protect command processing and AI calls from abuse. A simple
sliding-window counter keyed by (scope, key).
"""
from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_calls: int = 20, window_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock_guard = False  # asyncio.Lock alternative — single-threaded event loop

    def _prune(self, key: str, now: float) -> None:
        q = self._events[key]
        while q and q[0] <= now - self.window_seconds:
            q.popleft()

    def hit(self, key: str) -> bool:
        """Record an event; returns True if within the allowed limit."""
        now = time.monotonic()
        self._prune(key, now)
        q = self._events[key]
        if len(q) >= self.max_calls:
            return False
        q.append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        self._prune(key, now)
        return max(0, self.max_calls - len(self._events[key]))

    def reset(self, key: str) -> None:
        self._events.pop(key, None)
