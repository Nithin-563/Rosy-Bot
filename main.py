#!/usr/bin/env python3
"""Main entry point for Rosy Discord Bot.

This module provides the main() function that initializes and starts the bot.
"""

import asyncio
import sys
from typing import NoReturn

from bot.client import RosyBot
from bot.service import BotService
from config import settings
from database.session import init_db, close_db
from events import setup_events
from utils.logging import setup_logging, get_logger

logger: get_logger


def validate_environment() -> None:
    """Validate required environment variables.
    
    Raises:
        SystemExit: If required configuration is missing.
    """
    missing = settings.validate_required()
    
    if missing:
        error_message = settings.get_required_error_message()
        print(error_message, file=sys.stderr)
        sys.exit(1)
    
    logger.info("Environment validation passed")


async def main() -> None:
    """Main entry point for the bot."""
    global logger
    
    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Starting Rosy Discord Bot")
    logger.info("=" * 60)
    
    # Validate configuration
    validate_environment()
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        print(f"\nDatabase connection failed: {e}")
        print("Please check your DATABASE_URL in .env")
        sys.exit(1)
    
    # Create bot instance
    bot = RosyBot()
    
    # Setup event handlers
    setup_events(bot)
    
    # Create and run service
    service = BotService(bot)
    
    try:
        await service.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        logger.info("Shutting down...")
        await close_db()
        logger.info("Shutdown complete")


def run() -> None:
    """Run the bot with proper asyncio setup."""
    # Enable uvloop for better performance if available
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
