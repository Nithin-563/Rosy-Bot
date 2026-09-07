"""Simple in-memory token-bucket rate limiter.

Used to throttle commands and AI responses without blocking the event loop.
"""

from __future__ import annotations

import time
from threading import Lock


class TokenBucket:
    def __init__(self, rate_per_minute: int) -> None:
        self.capacity = rate_per_minute
        self.rate = rate_per_minute / 60.0  # tokens per second
        self.tokens = float(rate_per_minute)
        self.updated = time.monotonic()
        self._lock = Lock()

    def consume(self, n: int = 1) -> bool:
        with self._lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
            self.updated = now
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False


class RateLimiter:
    """Per-key token buckets with a default bucket for unknown keys."""

    def __init__(self, default_rate_per_minute: int = 10) -> None:
        self.default_rate = default_rate_per_minute
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = Lock()

    def _bucket(self, key: str, rate: int | None = None) -> TokenBucket:
        with self._lock:
            b = self._buckets.get(key)
            if b is None:
                b = TokenBucket(rate or self.default_rate)
                self._buckets[key] = b
            return b

    def allow(self, key: str, n: int = 1, rate: int | None = None) -> bool:
        return self._bucket(key, rate).consume(n)

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()