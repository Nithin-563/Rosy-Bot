"""Symmetric encryption for stored credentials.

Keys are never hard-coded. The Fernet key is derived from the `ENCRYPTION_KEY`
environment variable via a stable SHA-256 hash so any reasonably strong secret
string can be used as the seed.
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from rosy.config import get_settings

_MARKER = "enc:"


def _build_fernet(seed: str | None = None) -> Fernet:
    secret = seed or get_settings().encryption_key
    if not secret:
        raise ValueError(
            "ENCRYPTION_KEY is not configured. Set it to a strong random string."
        )
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt(plaintext: str, seed: str | None = None) -> str:
    """Encrypt `plaintext`, prefixing the result with a marker."""
    if not plaintext:
        return ""
    token = _build_fernet(seed).encrypt(plaintext.encode("utf-8"))
    return _MARKER + token.decode("utf-8")


def decrypt(value: str, seed: str | None = None) -> str:
    """Decrypt a value produced by :func:`encrypt`.

    Raises ValueError on wrong key or malformed input. Returns empty string for
    empty input.
    """
    if not value:
        return ""
    if not value.startswith(_MARKER):
        # Legacy / plaintext value — refuse to treat as ciphertext silently.
        return value
    try:
        token = value[len(_MARKER) :].encode("utf-8")
        return _build_fernet(seed).decrypt(token).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Cannot decrypt credential: invalid key or tampered value.") from exc


def encrypt_bytes(raw: bytes, seed: str | None = None) -> str:
    return _MARKER + _build_fernet(seed).encrypt(raw).decode("utf-8")


def decrypt_bytes(value: str, seed: str | None = None) -> bytes:
    token = value[len(_MARKER) :].encode("utf-8")
    return _build_fernet(seed).decrypt(token)
