"""Encryption helpers for stored credentials.

API keys are never stored in plaintext. We use Fernet (symmetric) encryption
with a key derived from the configured ENCRYPTION_KEY. A missing key yields an
opaque error rather than storing plaintext, so misconfiguration is loud.
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("rosy.encryption")

_fernet: Optional[Fernet] = None
_disabled = False  # True only in tests where no key is configured.


def _build_fernet(key_material: str) -> Fernet:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"rosy-encryption-v1",
        iterations=200_000,
    )
    derived = kdf.derive(key_material.encode("utf-8"))
    key = base64.urlsafe_b64encode(derived)
    return Fernet(key)


def configure_encryption(key_material: str | None) -> None:
    """Configure the global Fernet instance from the ENCRYPTION_KEY."""
    global _fernet, _disabled
    if not key_material:
        _fernet = None
        _disabled = False
        return
    _fernet = _build_fernet(key_material)
    _disabled = False


def set_encryption_disabled(flag: bool) -> None:
    """Test hook: disable encryption so unit tests can run without a key."""
    global _disabled
    _disabled = flag


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext secret. Returns a string safe to store in a column."""
    if _disabled:
        return plaintext
    if _fernet is None:
        raise RuntimeError(
            "ENCRYPTION_KEY is not configured. Set it to safely store credentials."
        )
    token = _fernet.encrypt(plaintext.encode("utf-8"))
    return "enc:" + token.decode("utf-8")


def decrypt(stored: str) -> str:
    """Decrypt a value previously produced by :func:`encrypt`."""
    if _disabled:
        return stored
    if _fernet is None:
        raise RuntimeError(
            "ENCRYPTION_KEY is not configured; cannot decrypt stored credentials."
        )
    if not stored.startswith("enc:"):
        raise ValueError("Stored value is not an encrypted credential.")
    try:
        token = stored[4:]
        return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:  # pragma: no cover - depends on key state
        raise ValueError("Failed to decrypt credential (wrong ENCRYPTION_KEY?).") from exc
