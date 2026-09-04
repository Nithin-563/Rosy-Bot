"""Rosy entry point.

Run with:  `rosy`  or  `python -m rosy.main`
"""

import asyncio
import logging
import os

from .bot.rosy_bot import RosyBot
from .config import get_settings
from .logging_config import setup_logging

logger = logging.getLogger("rosy.main")


async def _run_migrations() -> None:
    """Apply Alembic migrations on startup (skippable).

    Runs `alembic upgrade head` against the configured DATABASE_URL. A failure
    is fatal in production (schema must exist) unless explicitly skipped.
    """
    if os.environ.get("ROS_SKIP_MIGRATIONS", "").lower() in ("1", "true", "yes"):
        logger.info("Skipping database migrations (ROS_SKIP_MIGRATIONS set).")
        return
    proc = await asyncio.create_subprocess_exec(
        "alembic", "upgrade", "head",
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    rc = await proc.wait()
    if rc != 0:
        raise SystemExit(f"Database migrations failed with exit code {rc}.")


async def _amain() -> None:
    settings = get_settings()
    if not settings.discord_token:
        raise SystemExit(
            "DISCORD_TOKEN is not set. Add it to your environment before starting."
        )

    await _run_migrations()

    bot = RosyBot()
    logger.info("Starting Rosy (provider=%s, model=%s)", settings.default_provider, settings.default_model)
    try:
        await bot.start(settings.discord_token)
    except KeyboardInterrupt:
        await bot.close()


def run() -> None:
    setup_logging()
    asyncio.run(_amain())


if __name__ == "__main__":
    run()
