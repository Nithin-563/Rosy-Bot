"""Encryption utilities for securing sensitive data.

This module provides encryption and decryption functions for storing
API keys and other sensitive configuration securely in the database.
"""

import base64
import os
import secrets
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)

# Lazy initialization of Fernet cipher
_cipher: Optional[Fernet] = None


def _get_cipher() -> Fernet:
    """Get or create the Fernet cipher instance."""
    global _cipher
    if _cipher is None:
        if not settings.encryption_secret:
            raise ValueError(
                "ENCRYPTION_SECRET must be set to use encryption features. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        
        # Derive a valid Fernet key from the secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"rosy-bot-salt-v1",  # Static salt for deterministic key derivation
            iterations=100000,
        )
        key = kdf.derive(settings.encryption_secret.encode())
        _cipher = Fernet(base64.urlsafe_b64encode(key))
    
    return _cipher


def encrypt_key(plaintext: str) -> str:
    """Encrypt a sensitive string.
    
    Args:
        plaintext: The string to encrypt.
        
    Returns:
        Base64-encoded encrypted string.
        
    Raises:
        ValueError: If encryption fails.
    """
    if not plaintext:
        return ""
    
    try:
        cipher = _get_cipher()
        encrypted = cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError("Failed to encrypt data") from e


def decrypt_key(ciphertext: str) -> str:
    """Decrypt an encrypted string.
    
    Args:
        ciphertext: Base64-encoded encrypted string.
        
    Returns:
        Decrypted plaintext string.
        
    Raises:
        ValueError: If decryption fails.
    """
    if not ciphertext:
        return ""
    
    try:
        cipher = _get_cipher()
        encrypted = base64.urlsafe_b64decode(ciphertext.encode())
        decrypted = cipher.decrypt(encrypted)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError("Failed to decrypt data") from e


def generate_encryption_key() -> str:
    """Generate a new encryption key.
    
    Returns:
        A 32-character hex string suitable for use as ENCRYPTION_SECRET.
    """
    return secrets.token_hex(32)


def generate_api_key_name(provider: str, index: int = 1) -> str:
    """Generate a descriptive name for an API key.
    
    Args:
        provider: The AI provider name.
        index: Optional index for multiple keys from the same provider.
        
    Returns:
        A descriptive name for the key.
    """
    import datetime
    now = datetime.datetime.utcnow()
    return f"{provider}_key_{now.strftime('%Y%m%d')}_{index}"


class EncryptedField:
    """Descriptor for encrypting/decrypting field values automatically.
    
    Usage:
        class MyModel:
            api_key = EncryptedField("api_key")
    """
    
    def __init__(self, storage_attr: str):
        """Initialize the encrypted field.
        
        Args:
            storage_attr: Name of the attribute to store encrypted value in.
        """
        self.storage_attr = storage_attr
    
    def __get__(self, obj: Optional[object], objtype: Optional[type] = None) -> str:
        """Get the decrypted value."""
        if obj is None:
            return ""  # type: ignore
        
        encrypted = getattr(obj, self.storage_attr, "")
        if not encrypted:
            return ""
        
        return decrypt_key(encrypted)
    
    def __set__(self, obj: object, value: str) -> None:
        """Set the encrypted value."""
        if not value:
            setattr(obj, self.storage_attr, "")
        else:
            setattr(obj, self.storage_attr, encrypt_key(value))
