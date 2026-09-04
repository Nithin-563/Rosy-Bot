"""Encrypted credentials and per-guild AI provider configuration."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from rosy.db.base import Base, SurrogatePK, TimestampMixin


class Credential(TimestampMixin, Base):
    """Encrypted API key/token stored for a provider scope.

    scope: "global" (provider-level default) | "guild" (per-server override)
    Stored value is always ciphertext produced by rosy.security.crypto.encrypt.
    """

    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(16), default="global")  # global|guild
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)  # openrouter|openai|...
    name: Mapped[str] = mapped_column(String(64), default="api_key")
    encrypted_value: Mapped[str] = mapped_column(Text)


class ProviderConfig(TimestampMixin, Base):
    """Per-guild provider override (which provider/model/endpoint to use)."""

    __tablename__ = "provider_configs"

    id: Mapped[int] = mapped_column(SurrogatePK, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), default="")
    model: Mapped[str] = mapped_column(String(120), default="")
    base_url: Mapped[str] = mapped_column(String(255), default="")
