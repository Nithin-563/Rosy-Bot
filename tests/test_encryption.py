"""Encryption round-trip and failure tests."""

import pytest

from rosy.db import encryption


def test_roundtrip():
    encryption.configure_encryption("a-secret-key-material")
    enc = encryption.encrypt("sk-super-secret")
    assert enc.startswith("enc:")
    assert encryption.decrypt(enc) == "sk-super-secret"
    assert "sk-super-secret" not in enc


def test_missing_key_raises():
    encryption.configure_encryption(None)
    encryption.set_encryption_disabled(False)
    with pytest.raises(RuntimeError):
        encryption.encrypt("anything")


def test_wrong_key_fails():
    encryption.configure_encryption("key-one")
    enc = encryption.encrypt("data")
    encryption.configure_encryption("key-two")
    with pytest.raises(ValueError):
        encryption.decrypt(enc)
