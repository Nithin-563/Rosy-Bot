"""Rate limiter tests."""
from __future__ import annotations

import time

from rosy.security.rate_limit import RateLimiter


def test_hit_within_limit():
    rl = RateLimiter(max_calls=3, window_seconds=60)
    assert rl.hit("k") is True
    assert rl.hit("k") is True
    assert rl.hit("k") is True
    assert rl.hit("k") is False  # exceeded


def test_remaining_and_reset():
    rl = RateLimiter(max_calls=3, window_seconds=60)
    rl.hit("k")
    assert rl.remaining("k") == 2
    rl.reset("k")
    assert rl.remaining("k") == 3


def test_window_expiry():
    rl = RateLimiter(max_calls=1, window_seconds=1)
    assert rl.hit("k") is True
    time.sleep(1.1)
    assert rl.hit("k") is True  # window passed


def test_keys_are_independent():
    rl = RateLimiter(max_calls=1, window_seconds=60)
    assert rl.hit("a") is True
    assert rl.hit("b") is True
