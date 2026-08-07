#!/usr/bin/env python3
"""Main entry point for Rosy Discord Bot.

This module provides the main() function that initializes and starts the bot.
"""

import asyncio
import sys

from bot.client import RosyBot
from bot.service import BotService
from config import settings
from database.session import init_db, close_db
from events import setup_events
from utils.logging import setup_logging, get_logger

logger = None


def validate_environment() -> None:
    """Validate required environment variables.
    
    Only exits if database URL is missing (critical). Other vars are warned.
    """
    missing = settings.validate_required()
    
    if missing:
        logger.warning(
            f"Missing environment variables: {', '.join(missing)}. "
            "Bot may not function properly without these."
        )


async def main() -> None:
    """Main entry point for the bot."""
    global logger
    
    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)
    
    print("=" * 60)
    print("Starting Rosy Discord Bot")
    print("=" * 60)
    logger.info("Starting Rosy Discord Bot")
    
    # Initialize database
    print("Initializing database...")
    logger.info("Initializing database...")
    try:
        await init_db()
        print("Database initialized successfully")
        logger.info("Database initialized successfully")
    except Exception as e:
        print(f"\nDatabase connection failed: {e}")
        print("Please check your DATABASE_URL in .env")
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # Create bot instance
    bot = RosyBot()
    
    # Setup event handlers
    setup_events(bot)
    
    # Create service
    service = BotService(bot)
    
    # Start health check server FIRST - so Railway health check can succeed
    print("Starting health check server...")
    logger.info("Starting health check server...")
    await service.health_server.start()
    print("Health check server started")
    logger.info("Health check server started")
    
    # Give health server time to be ready
    await asyncio.sleep(2)
    
    # Validate config AFTER health check is running
    validate_environment()
    
    print("Starting Discord bot connection...")
    logger.info("Starting Discord bot connection...")
    
    try:
        # Start the Discord bot (this will block)
        await service.start_bot()
    except KeyboardInterrupt:
        print("Received shutdown signal")
        logger.info("Received shutdown signal")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        print("Shutting down...")
        logger.info("Shutting down...")
        await service.stop()
        await close_db()
        print("Shutdown complete")
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
