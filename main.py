#!/usr/bin/env python3
"""Main entry point for Rosy Discord Bot.

This module provides the main() function that initializes and starts the bot.
"""

import asyncio
import sys

import discord
from sqlalchemy import text

from bot.client import RosyBot
from bot.service import BotService
from config import settings
from database.session import close_db, engine
from events import setup_events
from utils.logging import setup_logging, get_logger

logger = None


async def initialize_database(service: BotService) -> None:
    """Initialize database with retries in the background.
    
    This runs after the bot is online so Railway health checks pass
    and the bot is visible in Discord even if the database is slow to start.
    """
    from database.session import init_db
    import traceback
    
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[DB] Initializing database (attempt {attempt}/{max_retries})...")
            logger.info(f"Initializing database (attempt {attempt}/{max_retries})...")
            await init_db()
            service.health_server.update_status("database", "ok")
            print("[DB] Database initialized successfully")
            logger.info("Database initialized successfully")
            return
        except Exception as e:
            service.health_server.update_status("database", f"error: {e}")
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"[DB] Attempt {attempt} failed: {error_type}: {error_msg}")
            logger.error(f"Database initialization attempt {attempt} failed: {error_type}: {error_msg}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            
            if attempt < max_retries:
                print(f"[DB] Retrying in {retry_delay}s...")
                logger.info(f"Retrying database connection in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # Cap at 60s
            else:
                print("[DB] All database connection attempts failed!")
                print("[DB] Bot will continue without database (some features may not work)")
                logger.error("Database initialization failed after all retries")


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
    
    # Validate required environment variables FIRST
    missing = []
    if not settings.discord_bot_token or not settings.discord_bot_token.strip():
        missing.append("DISCORD_BOT_TOKEN")
    if not settings.openrouter_api_key or not settings.openrouter_api_key.strip():
        missing.append("OPENROUTER_API_KEY")
    
    if missing:
        print("=" * 60)
        print("ERROR: Missing Required Configuration")
        print("=" * 60)
        for var in missing:
            print(f"  - {var}")
        print()
        print("Please set these variables in Railway Dashboard → Variables")
        print("See .env.example for reference.")
        print("=" * 60)
        raise SystemExit(1)
    
    # Create bot instance
    bot = RosyBot()
    
    # Setup event handlers
    setup_events(bot)
    
    # Create service
    service = BotService(bot)
    
    try:
        # Start health check server FIRST - so Railway health check passes immediately
        print("Starting health check server...")
        logger.info("Starting health check server...")
        await service.health_server.start()
        print("Health check server started")
        logger.info("Health check server started")
        
        # Give health server a moment to bind
        await asyncio.sleep(1)
        
        # Print startup config
        print("=" * 60)
        print("Startup Configuration:")
        
        # Mask password in database URL for logging
        db_url = settings.database_url
        if "@" in db_url:
            parts = db_url.split("@")
            masked_url = parts[0].split("://")[0] + "://***@" + parts[1]
            print(f"  Database URL: {masked_url}")
        else:
            print(f"  Database URL: {db_url}")
        
        print(f"  Discord Token: {'Set' if settings.discord_bot_token else 'MISSING'}")
        print(f"  OpenRouter Key: {'Set' if settings.openrouter_api_key else 'MISSING'}")
        print(f"  Health Port: {settings.port}")
        print("=" * 60)
        logger.info(
            "Startup configuration validated",
            database_url=masked_url if "@" in db_url else db_url,
            discord_token_set=bool(settings.discord_bot_token),
            openrouter_key_set=bool(settings.openrouter_api_key),
            health_port=settings.port,
        )
        
        # Quick DB connectivity test before launching bot
        print("[DB] Testing database connectivity...")
        logger.info("Testing database connectivity...")
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print("[DB] Database connectivity test passed")
            logger.info("Database connectivity test passed")
        except Exception as e:
            print(f"[DB] Connectivity test failed: {type(e).__name__}: {e}")
            logger.error(f"Database connectivity test failed: {type(e).__name__}: {e}")
        
        # Start Discord bot FIRST - so it comes online immediately
        print("Starting Discord bot connection...")
        logger.info("Starting Discord bot connection...")
        
        # Create background task for database initialization
        db_task = asyncio.create_task(initialize_database(service))
        
        # Start the Discord bot (this will block)
        await service.start_bot()
        
    except KeyboardInterrupt:
        print("\nReceived shutdown signal")
        logger.info("Received shutdown signal")
    except discord.LoginFailure as e:
        print(f"\n[DISCORD] Login failed: {e}")
        print("[DISCORD] Check that DISCORD_BOT_TOKEN is valid in Railway Variables.")
        logger.error(f"Discord login failed: {e}")
        raise
    except Exception as e:
        print(f"\n[FATAL] Error during startup: {e}")
        logger.error(f"Fatal error during startup: {e}", exc_info=True)
        raise
    finally:
        print("Shutting down...")
        logger.info("Shutting down...")
        try:
            await service.stop()
            await close_db()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
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
    except SystemExit:
        raise
    except Exception as e:
        # Last-resort crash logger so Railway shows the real error
        print(f"[FATAL] Unhandled error: {e}", flush=True)
        try:
            import traceback
            traceback.print_exc()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    run()
