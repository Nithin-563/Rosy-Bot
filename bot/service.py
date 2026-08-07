"""Bot service for managing bot lifecycle and health checks.

This module provides the BotService class that manages the bot's
lifecycle, including startup, shutdown, and health monitoring.
"""

import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)


class HealthCheckServer:
    """Simple health check server using FastAPI.
    
    This provides an HTTP endpoint for Railway and other deployment
    platforms to verify the bot is running.
    """
    
    def __init__(self, bot) -> None:
        """Initialize the health check server.
        
        Args:
            bot: The RosyBot instance.
        """
        self.bot = bot
        self.app = FastAPI(title="Rosy Bot Health Check")
        self.server: Optional[uvicorn.Server] = None
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Set up FastAPI routes."""
        
        @self.app.get("/health")
        async def health_check() -> JSONResponse:
            """Basic health check endpoint."""
            return JSONResponse({
                "status": "healthy",
                "bot_user": str(self.bot.user) if self.bot.user else None,
                "guilds": len(self.bot.guilds),
            })
        
        @self.app.get("/health/detailed")
        async def detailed_health() -> JSONResponse:
            """Detailed health check with more information."""
            return JSONResponse({
                "status": "healthy",
                "bot_user": str(self.bot.user) if self.bot.user else None,
                "bot_id": self.bot.user.id if self.bot.user else None,
                "guilds": len(self.bot.guilds),
                "uptime": self.bot.get_uptime(),
                "latency": {
                    "ws": round(self.bot.latency * 1000) if self.bot.latency else None,
                },
            })
        
        @self.app.get("/")
        async def root() -> JSONResponse:
            """Root endpoint."""
            return JSONResponse({
                "name": "Rosy Bot",
                "version": "1.0.0",
                "status": "running",
            })
    
    async def start(self) -> None:
        """Start the health check server."""
        if not settings.enable_health_check:
            logger.info("Health check server disabled")
            return
        
        config = uvicorn.Config(
            self.app,
            host=settings.health_host,
            port=settings.port,  # Uses Railway's PORT env var
            log_level="info",
        )
        self.server = uvicorn.Server(config)
        
        logger.info(
            f"Starting health check server on {settings.health_host}:{settings.health_port}"
        )
        
        # Run in background
        asyncio.create_task(self.server.serve())
    
    async def stop(self) -> None:
        """Stop the health check server."""
        if self.server:
            self.server.should_exit = True
            logger.info("Health check server stopped")


class BotService:
    """Service for managing the bot lifecycle.
    
    This class handles starting and stopping the bot, including
    initialization, health checks, and graceful shutdown.
    """
    
    def __init__(self, bot) -> None:
        """Initialize the bot service.
        
        Args:
            bot: The RosyBot instance.
        """
        self.bot = bot
        self.health_server = HealthCheckServer(bot)
        self._shutdown_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start the bot and all services (health check + Discord bot)."""
        logger.info("Starting Rosy Bot service...")
        
        # Start health check server FIRST
        await self.health_server.start()
        
        # Give health server a moment to start
        await asyncio.sleep(0.5)
        
        # Start the Discord bot
        async with self.bot:
            await self.bot.start(settings.discord_bot_token)
    
    async def start_bot(self) -> None:
        """Start only the bot (Discord connection). Health check should be started separately."""
        logger.info("Starting Discord bot...")
        
        # Start the Discord bot
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
