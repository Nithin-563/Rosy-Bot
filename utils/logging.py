"""Structured logging configuration for Rosy Discord Bot.

This module provides centralized logging setup using structlog for
structured, machine-parseable logs with both console and JSON output.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from config import settings


def setup_logging() -> None:
    """Configure structured logging based on settings."""
    log_level = getattr(logging, settings.log_level, logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Determine processors based on output format
    if settings.log_format == "json":
        processors: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name, typically __name__ of the module.
        
    Returns:
        A structured logger instance.
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to provide logging capability to any class."""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get a logger for this class."""
        return get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )


def log_command_usage(
    logger: structlog.stdlib.BoundLogger,
    command_name: str,
    user_id: int,
    guild_id: int | None = None,
    channel_id: int | None = None,
    **kwargs: Any,
) -> None:
    """Log command usage with structured data.
    
    Args:
        logger: Logger instance.
        command_name: Name of the command.
        user_id: Discord user ID who invoked the command.
        guild_id: Discord guild ID where command was invoked.
        channel_id: Discord channel ID where command was invoked.
        **kwargs: Additional context to log.
    """
    logger.info(
        "Command executed",
        command=command_name,
        user_id=user_id,
        guild_id=guild_id,
        channel_id=channel_id,
        **kwargs,
    )


def log_ai_request(
    logger: structlog.stdlib.BoundLogger,
    model: str,
    message_count: int,
    guild_id: int | None = None,
    user_id: int | None = None,
    **kwargs: Any,
) -> None:
    """Log an AI API request.
    
    Args:
        logger: Logger instance.
        model: AI model being used.
        message_count: Number of messages in the request.
        guild_id: Discord guild ID.
        user_id: Discord user ID.
        **kwargs: Additional context to log.
    """
    logger.debug(
        "AI request",
        model=model,
        message_count=message_count,
        guild_id=guild_id,
        user_id=user_id,
        **kwargs,
    )


def log_database_event(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    table: str,
    guild_id: int | None = None,
    user_id: int | None = None,
    **kwargs: Any,
) -> None:
    """Log a database operation.
    
    Args:
        logger: Logger instance.
        operation: Type of operation (INSERT, UPDATE, DELETE, SELECT).
        table: Database table name.
        guild_id: Discord guild ID.
        user_id: Discord user ID.
        **kwargs: Additional context to log.
    """
    logger.debug(
        "Database operation",
        operation=operation,
        table=table,
        guild_id=guild_id,
        user_id=user_id,
        **kwargs,
    )
