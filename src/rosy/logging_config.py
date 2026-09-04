"""Structured logging setup for Rosy.

Uses Python's standard logging with a consistent JSON-ish or readable format.
Message contents are intentionally NOT logged to respect privacy.
"""

import logging
import sys

from .config import get_settings

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: str | None = None) -> None:
    settings = get_settings()
    lvl = (level or settings.log_level or "INFO").upper()
    root = logging.getLogger()
    root.setLevel(lvl)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT))
    root.handlers.clear()
    root.addHandler(handler)

    # Keep discord.py's noisy gateway logging at a sane level.
    logging.getLogger("discord.gateway").setLevel(logging.INFO)
    logging.getLogger("discord.client").setLevel(logging.WARNING)
