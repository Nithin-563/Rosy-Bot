"""Bot service for managing bot lifecycle and health checks.

This module provides the BotService class that manages the bot's
lifecycle, including startup, shutdown, and health monitoring.
"""

import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)


class SimpleHealthHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""
    
    bot = None
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            response = {"status": "healthy"}
            if SimpleHealthHandler.bot and SimpleHealthHandler.bot.user:
                response["bot_user"] = str(SimpleHealthHandler.bot.user)
                response["guilds"] = len(SimpleHealthHandler.bot.guilds)
            else:
                response["bot_user"] = None
                response["guilds"] = 0
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class HealthCheckServer:
    """Minimal health check server using stdlib http.server."""
    
    def __init__(self, bot) -> None:
        """Initialize the health check server."""
        self.bot = bot
        SimpleHealthHandler.bot = bot
        self.server: Optional[HTTPServer] = None
    
    async def start(self) -> None:
        """Start the health check server in a thread."""
        import os
        
        port = int(os.environ.get("PORT", settings.health_port))
        
        try:
            self.server = HTTPServer(("0.0.0.0", port), SimpleHealthHandler)
            
            # Run in background thread
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.server.serve_forever)
            
            logger.info(f"Health check server started on 0.0.0.0:{port}")
        except Exception as e:
            logger.error(f"Failed to start health check server: {e}")
    
    async def stop(self) -> None:
        """Stop the health check server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Health check server stopped")


class BotService:
    """Service for managing the bot lifecycle."""
    
    def __init__(self, bot) -> None:
        """Initialize the bot service."""
        self.bot = bot
        self.health_server = HealthCheckServer(bot)
        self._shutdown_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start the bot and all services."""
        logger.info("Starting Rosy Bot service...")
        
        # Start health check server
        await self.health_server.start()
        
        # Give health server a moment to start
        await asyncio.sleep(0.5)
        
        # Start the Discord bot
        async with self.bot:
            await self.bot.start(settings.discord_bot_token)
    
    async def start_bot(self) -> None:
        """Start only the Discord bot."""
        logger.info("Starting Discord bot...")
        async with self.bot:
            await self.bot.start(settings.discord_bot_token)
    
    async def stop(self) -> None:
        """Stop the bot and all services."""
        logger.info("Stopping Rosy Bot service...")
        
        # Stop health check server
        await self.health_server.stop()
        
        # Close bot
        await self.bot.close()
        
        # Signal shutdown complete
        self._shutdown_event.set()
    
    async def run(self) -> None:
        """Run the bot service with graceful shutdown handling."""
        try:
            await self.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            await self.stop()
    
    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()
