"""Encryption tests."""
from __future__ import annotations

import pytest

from rosy.security.crypto import decrypt, encrypt


def test_roundtrip():
    value = "sk-secret-key-123"
    enc = encrypt(value, seed="test-seed")
    assert enc != value
    assert enc.startswith("enc:")
    assert decrypt(enc, seed="test-seed") == value


def test_wrong_seed_raises():
    enc = encrypt("hello", seed="seed-a")
    with pytest.raises(ValueError):
        decrypt(enc, seed="seed-b")


def test_empty_roundtrip():
    assert encrypt("", seed="s") == ""
    assert decrypt("", seed="s") == ""


def test_plaintext_passthrough():
    # For backward compatibility, unmarked values pass through.
    assert decrypt("not-encrypted", seed="s") == "not-encrypted"
