"""Rosy entry point.

Run with:  `rosy`  or  `python -m rosy.main`
"""

import asyncio
import logging
import os
import sys

from .bot.rosy_bot import RosyBot
from .config import get_settings
from .logging_config import setup_logging

logger = logging.getLogger("rosy.main")


def _find_project_root() -> str:
    """Locate the directory containing alembic.ini (the project root)."""
    here = os.path.dirname(os.path.abspath(__file__))  # .../rosy
    for _ in range(6):
        if os.path.isfile(os.path.join(here, "alembic.ini")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    return os.getcwd()


async def _run_migrations() -> None:
    """Apply Alembic migrations on startup (skippable).

    Runs `alembic upgrade head` against the configured DATABASE_URL. A failure
    is fatal in production (schema must exist) unless explicitly skipped.
    """
    if os.environ.get("ROS_SKIP_MIGRATIONS", "").lower() in ("1", "true", "yes"):
        logger.info("Skipping database migrations (ROS_SKIP_MIGRATIONS set).")
        return

    root = _find_project_root()
    logger.info("Running database migrations (project root=%s).", root)
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "alembic",
        "upgrade",
        "head",
        cwd=root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode("utf-8", errors="replace") if stdout else ""
    if output.strip():
        logger.info("alembic output:\n%s", output)
    if proc.returncode != 0:
        logger.error("Alembic failed with exit code %s.\n%s", proc.returncode, output)
        raise SystemExit(
            "Database migrations failed with exit code "
            f"{proc.returncode}. DATABASE_URL must be a reachable PostgreSQL "
            "URL (postgresql+asyncpg://...). If you manage migrations yourself, "
            "set ROS_SKIP_MIGRATIONS=1."
        )


async def _amain() -> None:
    settings = get_settings()
    if not settings.discord_token:
        visible = settings.visible_env_names
        cfg = settings.configured
        raise SystemExit(
            "DISCORD_TOKEN is not set. Rosy accepted DISCORD_TOKEN, "
            "DISCORD_BOT_TOKEN, BOT_TOKEN, ROSY_TOKEN, DISCORDTOKEN.\n"
            "Env names visible to this process containing TOKEN/KEY/DISCORD: "
            + ((", ".join(visible)) if visible else "(none)") + "\n"
            "Configured: " + ", ".join(f"{k}={v}" for k, v in cfg.items())
        )

    await _run_migrations()

    bot = RosyBot()
    logger.info(
        "Starting Rosy (provider=%s, model=%s, db=%s)",
        settings.default_provider,
        settings.default_model,
        settings.database_url.split("@")[-1].split("/")[0] if "@" in settings.database_url else "configured",
    )
    try:
        await bot.start(settings.discord_token)
    except KeyboardInterrupt:
        await bot.close()


def run() -> None:
    setup_logging()
    asyncio.run(_amain())


if __name__ == "__main__":
    run()
