"""Config, security, and rate-limit unit tests."""

from __future__ import annotations

from rosy.config import Settings
from rosy.core import RateLimiter, decrypt, encrypt, redact


def test_settings_env_prefix():
    import os

    os.environ["ROS_DISCORD_TOKEN"] = "abc"
    os.environ["ROS_DEFAULT_MODEL"] = "custom/model"
    s = Settings(_env_file=None)
    assert s.discord_token == "abc"
    assert s.default_model == "custom/model"
    del os.environ["ROS_DISCORD_TOKEN"]
    del os.environ["ROS_DEFAULT_MODEL"]


def test_settings_accepts_platform_env_aliases(monkeypatch):
    monkeypatch.delenv("ROS_DISCORD_TOKEN", raising=False)
    monkeypatch.delenv("ROS_HEALTH_PORT", raising=False)
    monkeypatch.setenv("DISCORD_TOKEN", "platform-token")
    monkeypatch.setenv("PORT", "9000")

    s = Settings(_env_file=None)

    assert s.discord_token == "platform-token"
    assert s.health_port == 9000


def test_settings_normalizes_postgres_database_urls(monkeypatch):
    monkeypatch.setenv("ROS_DISCORD_TOKEN", "abc")
    monkeypatch.setenv("ROS_DATABASE_URL", "postgresql://user:pass@host:5432/db")

    s = Settings(_env_file=None)

    assert s.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


def test_settings_normalizes_railway_database_url_fallback(monkeypatch):
    monkeypatch.setenv("ROS_DISCORD_TOKEN", "abc")
    monkeypatch.delenv("ROS_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host:5432/db")

    s = Settings(_env_file=None)

    assert s.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


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