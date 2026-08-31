"""Plugin framework placeholder.

Future plugins register here. The core already supports per-guild plugin
configuration via the `PluginConfig` table and the `PluginRegistry` pattern
used by tools. Extend without rewriting the core.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("rosy.plugins")


class Plugin:
    name: str = ""
    description: str = ""

    async def on_load(self, bot) -> None:  # pragma: no cover - extension point
        pass

    async def on_unload(self, bot) -> None:  # pragma: no cover - extension point
        pass


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.name] = plugin
        logger.info("Registered plugin: %s", plugin.name)

    async def load_all(self, bot) -> None:
        for plugin in self._plugins.values():
            try:
                await plugin.on_load(bot)
            except Exception:
                logger.exception("Failed to load plugin %s", plugin.name)


def build_default_registry() -> PluginRegistry:
    return PluginRegistry()