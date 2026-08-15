#!/usr/bin/env python3
"""Main entry point for Rosy Discord Bot.

This module provides the main() function that initializes and starts the bot.
"""

import asyncio
import sys

import discord

from bot.client import RosyBot
from bot.service import BotService
from config import settings
from database.session import init_db, close_db
from events import setup_events
from utils.logging import setup_logging, get_logger

logger = None


def validate_environment() -> None:
    """Validate required environment variables and exit if missing."""
    settings.validate_required_or_exit()
    
    token = settings.discord_bot_token.strip()
    if len(token) < 50:
        print(f"[WARN] Discord bot token looks unusually short ({len(token)} chars).")
        print("[WARN] Verify DISCORD_BOT_TOKEN is set correctly in Railway Variables.")
    else:
        print("[OK] Discord bot token format looks valid.")


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
    
    # Create bot instance
    bot = RosyBot()
    
    # Setup event handlers
    setup_events(bot)
    
    # Create service
    service = BotService(bot)
    
    try:
        # Start health check server FIRST - so Railway health check can succeed immediately
        print("Starting health check server...")
        logger.info("Starting health check server...")
        await service.health_server.start()
        print("Health check server started")
        logger.info("Health check server started")
        
        # Give health server a moment to bind to the port
        await asyncio.sleep(1)
        
        # Initialize database AFTER health server is up
        print("Initializing database...")
        logger.info("Initializing database...")
        try:
            await init_db()
            service.health_server.update_status("database", "ok")
            print("Database initialized successfully")
            logger.info("Database initialized successfully")
        except Exception as e:
            service.health_server.update_status("database", f"error: {e}")
            print(f"\nDatabase connection failed: {e}")
            print("Please check your DATABASE_URL in environment variables")
            logger.error(f"Failed to initialize database: {e}")
            # Stop health server before exiting
            await service.health_server.stop()
            sys.exit(1)
        
        # Validate config after database is ready
        validate_environment()
        
        # Print startup summary
        print("=" * 60)
        print("Startup Summary:")
        print(f"  Database: {'Connected' if settings.database_url else 'Not configured'}")
        print(f"  Discord Token: {'Set' if settings.discord_bot_token else 'MISSING'}")
        print(f"  OpenRouter Key: {'Set' if settings.openrouter_api_key else 'MISSING'}")
        print(f"  Encryption Secret: {'Set' if settings.encryption_secret else 'Using default (not recommended)'}")
        print(f"  Health Port: {settings.port}")
        print("=" * 60)
        logger.info("Startup configuration validated")
        
        print("Starting Discord bot connection...")
        logger.info("Starting Discord bot connection...")
        
        # Start the Discord bot (this will block)
        await service.start_bot()
        service.health_server.update_status("discord", "ok")
        service.health_server.update_status("overall", "ok")
        
    except KeyboardInterrupt:
        print("\nReceived shutdown signal")
        logger.info("Received shutdown signal")
    except SystemExit:
        raise
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
