"""Rosy entrypoint.

Usage:
    python -m rosy.main

Starts a lightweight HTTP health server first (so Railway's health check always
has something to answer), then connects the Discord bot. Any startup failure is
logged in plain text and the process exits non-zero so Railway retries.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from rosy.config import get_settings

logger = logging.getLogger("rosy.main")


async def _health_server(host: str, port: int, ready: "asyncio.Event") -> None:
    """Tiny aiohttp-less health endpoint using asyncio streams."""
    import asyncio as _a

    async def handle(reader, writer):
        if ready.is_set():
            body = b"ok"
            status = b"HTTP/1.1 200 OK"
        else:
            body = b"starting"
            status = b"HTTP/1.1 503 Service Unavailable"
        writer.write(status + b"\r\nContent-Type: text/plain\r\nContent-Length: " +
                     str(len(body)).encode() + b"\r\n\r\n" + body)
        await writer.drain()
        writer.close()

    server = await _a.start_server(handle, host, port)
    logger.info("Health server listening on %s:%s", host, port)
    async with server:
        await server.serve_forever()


def main() -> int:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    ready = asyncio.Event()
    health_task = None

    async def _run() -> int:
        nonlocal health_task
        from rosy.bot import build_bot

        bot = build_bot(settings)
        health_task = asyncio.create_task(
            _health_server(settings.health_bind_host, settings.health_port, ready)
        )
        # Brief pause so the health server is listening before we connect.
        await asyncio.sleep(0.2)

        # Give the bot access to the health 'ready' event. Command syncing and
        # the online log live in RosyBot.on_ready (we must NOT override on_ready
        # here, or slash commands would never be registered).
        bot.ready_event = ready

        try:
            await bot.start(settings.discord_token)  # blocks while running
        except Exception as exc:  # noqa: BLE001 - top-level guard
            logger.error("ROSY STARTUP FAILED: %s", exc)
            logger.error("Full error: %r", exc)
            return 1
        finally:
            ready.set()
            if health_task is not None:
                health_task.cancel()
            try:
                await bot.close()
            except Exception:  # noqa: BLE001
                pass
        return 0

    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())