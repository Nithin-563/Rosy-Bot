"""Rosy entrypoint.

Usage:
    python -m rosy.main

Starts the bot. Also serves a lightweight HTTP health check on the configured
port (used by Railway for liveness).
"""

from __future__ import annotations

import asyncio
import logging

from rosy.bot import build_bot
from rosy.config import get_settings

logger = logging.getLogger("rosy.main")


async def _health_server(host: str, port: int) -> None:
    """Tiny aiohttp-less health endpoint using asyncio streams."""
    import asyncio as _a

    async def handle(reader, writer):
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nok")
        await writer.drain()
        writer.close()

    server = await _a.start_server(handle, host, port)
    logger.info("Health server listening on %s:%s", host, port)
    async with server:
        await server.serve_forever()


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    bot = build_bot(settings)

    health_task = asyncio.create_task(
        _health_server(settings.health_bind_host, settings.health_port)
    )
    try:
        await bot.start(settings.discord_token)
    finally:
        health_task.cancel()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())