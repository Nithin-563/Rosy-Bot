"""Cog registry. Cogs are optional-safe: loading must never crash the bot."""
from __future__ import annotations

import logging
import importlib

log = logging.getLogger(__name__)


def _load(name: str):
    try:
        return importlib.import_module(f"rosy.cogs.{name}")
    except Exception:  # noqa: BLE001
        log.exception("Cog module %s failed to import; skipping.", name)
        return None


def _cog_classes():
    order = [
        "core",
        "conversation",
        "memory_cog",
        "reminders_cog",
        "games_cog",
        "custom_commands_cog",
        "moderation_cog",
        "admin_cog",
        "music_cog",
        "voice_cog",
        "files_cog",
    ]
    classes = []
    for name in order:
        mod = _load(name)
        if mod is None:
            continue
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and obj.__module__ == mod.__name__ and obj.__name__ != "Cog":
                classes.append(obj)
    return classes


CORE_COGS = _cog_classes()
