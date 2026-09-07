"""Rosy entry point.

Usage:
    rosy                          # run the bot using .env / environment variables
    rosy --dev-migrate            # create schema and exit (for local quickstart)
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

log = logging.getLogger(__name__)


async def _dev_migrate() -> None:
    from rosy.bot import build_bot

    bot = build_bot()
    from rosy.db.models import Base
    async with bot.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await bot.engine.dispose()
    print("Schema created. You can now run `rosy`.")


async def _run() -> None:
    from rosy.bot import build_bot
    from rosy.config import get_settings
    from rosy.logging_conf import setup_logging

    settings = get_settings()
    setup_logging(settings.log_level, settings.log_json)
    if not settings.discord_token:
        log.error("DISCORD_TOKEN is not set. Add it to your environment or .env file.")
        sys.exit(2)

    bot = build_bot(settings=settings)
    try:
        await bot.start(settings.discord_token)
    except KeyboardInterrupt:
        await bot.close()
    except Exception:  # noqa: BLE001
        log.exception("Fatal startup/runtime error")
        await bot.close()
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(prog="rosy", description="Rosy AI Discord bot")
    parser.add_argument("--dev-migrate", action="store_true", help="Create the DB schema and exit.")
    args = parser.parse_args()

    if args.dev_migrate:
        asyncio.run(_dev_migrate())
        return
    asyncio.run(_run())


if __name__ == "__main__":
    main()
