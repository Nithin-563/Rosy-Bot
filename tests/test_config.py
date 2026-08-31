"""Config, security, and rate-limit unit tests."""

from __future__ import annotations

import pytest

from rosy.config import Settings
from rosy.core import encrypt, decrypt, redact, RateLimiter


def test_settings_env_prefix():
    import os

    os.environ["ROS_DISCORD_TOKEN"] = "abc"
    os.environ["ROS_DEFAULT_MODEL"] = "custom/model"
    s = Settings(_env_file=None)
    assert s.discord_token == "abc"
    assert s.default_model == "custom/model"
    del os.environ["ROS_DISCORD_TOKEN"]
    del os.environ["ROS_DEFAULT_MODEL"]


def test_security_roundtrip():
    secret = "sk-or-v1-super-secret-key"
    cipher = encrypt(secret)
    assert cipher != secret
    assert decrypt(cipher) == secret


def test_redact():
    assert redact("") == ""
    assert redact("abcd") == "***"
    assert redact("sk-or-v1-1234567890abcdef").startswith("sk-o")


def test_rate_limiter():
    limiter = RateLimiter(default_rate_per_minute=2)
    key = "user:1"
    assert limiter.allow(key) is True
    assert limiter.allow(key) is True
    # bucket exhausted until refill
    assert limiter.allow(key) is False