"""Security helpers.

At-rest encryption for stored provider API keys using Fernet (cryptography).
Secrets are never logged and never returned in plaintext by default.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("rosy.security")

_fernet: Fernet | None = None


def _derive_key(raw: str, salt: str) -> bytes:
    digest = hashlib.pbkdf2_hmac(
        "sha256", raw.encode("utf-8"), salt.encode("utf-8"), iterations=200_000
    )
    return base64.urlsafe_b64encode(digest)


def init_encryption(secret: str, salt: str) -> None:
    """Initialise the global encryptor. Call once at startup.

    Provide a stable secret (env: ROSY_ENCRYPTION_KEY) so stored secrets
    survive restarts. If empty, an ephemeral random key is used.
    """
    global _fernet
    if secret:
        _fernet = Fernet(_derive_key(secret, salt))
    else:
        random_key = Fernet.generate_key()
        _fernet = Fernet(random_key)
        logger.warning("No encryption key configured; secrets will not persist across restarts.")


def encrypt(plaintext: str) -> str:
    if _fernet is None:
        raise RuntimeError("Encryption not initialised.")
    token = _fernet.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt(ciphertext: str) -> str:
    if _fernet is None:
        raise RuntimeError("Encryption not initialised.")
    try:
        return _fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:  # pragma: no cover - defensive
        raise ValueError("Could not decrypt stored secret (key changed?).") from exc


def generate_token(bytes_: int = 32) -> str:
    return secrets.token_urlsafe(bytes_)


def redact(value: str, keep: int = 4) -> str:
    """Return a redacted view of a sensitive string (e.g. API key)."""
    if not value:
        return ""
    if len(value) <= keep + 4:
        return "***"
    return value[:keep] + "..." + value[-2:]