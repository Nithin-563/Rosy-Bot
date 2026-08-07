"""Input validation and sanitization utilities.

This module provides functions for validating and sanitizing user input
to prevent injection attacks and ensure data integrity.
"""

import re
from typing import Optional

from config import settings
from utils.logging import get_logger

logger = get_logger(__name__)

# Maximum lengths for various input types
MAX_MESSAGE_LENGTH = 4000
MAX_USERNAME_LENGTH = 100
MAX_MODEL_NAME_LENGTH = 100
MAX_API_KEY_LENGTH = 500

# Patterns for validation
DISCORD_ID_PATTERN = re.compile(r"^\d{17,20}$")
MODEL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9/\-_]+$")


def sanitize_input(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
    """Sanitize user input by removing potentially dangerous content.
    
    Args:
        text: The input text to sanitize.
        max_length: Maximum allowed length.
        
    Returns:
        Sanitized text safe for storage and display.
    """
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(
            "Input truncated",
            original_length=len(text),
            max_length=max_length,
        )
    
    return text


def validate_discord_id(value: str) -> bool:
    """Validate a Discord ID (snowflake).
    
    Discord IDs are 17-20 digit numbers.
    
    Args:
        value: The ID string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not value:
        return False
    
    return bool(DISCORD_ID_PATTERN.match(value))


def validate_model_name(model: str) -> bool:
    """Validate an AI model name.
    
    Args:
        model: The model name to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not model:
        return False
    
    if len(model) > MAX_MODEL_NAME_LENGTH:
        return False
    
    return bool(MODEL_NAME_PATTERN.match(model))


def validate_api_key(api_key: str) -> bool:
    """Basic validation for API keys.
    
    Args:
        api_key: The API key to validate.
        
    Returns:
        True if appears valid, False otherwise.
    """
    if not api_key:
        return False
    
    # Basic length check
    if len(api_key) < 10 or len(api_key) > MAX_API_KEY_LENGTH:
        return False
    
    # Should contain a mix of characters
    if not any(c.isalnum() for c in api_key):
        return False
    
    return True


async def is_admin(
    user_id: int,
    guild_id: Optional[int] = None,
    member: Optional[object] = None,
) -> bool:
    """Check if a user has admin permissions.
    
    Args:
        user_id: Discord user ID.
        guild_id: Discord guild ID (for guild context).
        member: Discord member object (if available).
        
    Returns:
        True if user is admin or bot owner, False otherwise.
    """
    # Check if user is the bot owner
    if settings.bot_owner_id:
        try:
            if user_id == int(settings.bot_owner_id):
                return True
        except ValueError:
            pass
    
    # For guild context, check Discord permissions
    if member is not None:
        # Check for administrator permission
        if hasattr(member, "guild_permissions"):
            if member.guild_permissions.administrator:
                return True
        
        # Check for manage server permission
        if hasattr(member, "guild_permissions"):
            if member.guild_permissions.manage_guild:
                return True
    
    return False


def check_command_permission(
    user_id: int,
    guild_id: Optional[int],
    required_roles: Optional[list[int]] = None,
    member: Optional[object] = None,
) -> tuple[bool, str]:
    """Check if a user has permission to execute a command.
    
    Args:
        user_id: Discord user ID.
        guild_id: Discord guild ID.
        required_roles: List of role IDs that can use this command.
        member: Discord member object.
        
    Returns:
        Tuple of (has_permission, reason).
    """
    # Owner always has permission
    if is_admin(user_id, guild_id, member):
        return True, "Bot owner"
    
    # Check role requirements
    if required_roles and member is not None:
        if hasattr(member, "roles"):
            member_role_ids = [role.id for role in member.roles]
            if any(role_id in member_role_ids for role_id in required_roles):
                return True, "Has required role"
    
    return False, "Insufficient permissions"


def sanitize_mention(text: str) -> str:
    """Sanitize Discord mentions in text.
    
    Args:
        text: Text that may contain mentions.
        
    Returns:
        Text with mentions converted to names.
    """
    if not text:
        return ""
    
    # Remove mention syntax for storage
    # <@123> -> @username (would need bot to resolve)
    # <#123> -> #channelname
    # <@&123> -> @rolename
    text = re.sub(r"<@!?(\d+)>", r"@\1", text)
    text = re.sub(r"<#(\d+)>", r"#\1", text)
    text = re.sub(r"<@&(\d+)>", r"@\1", text)
    
    return text


def escape_disord_formatting(text: str) -> str:
    """Escape Discord formatting characters in text.
    
    Args:
        text: Text that may contain Discord formatting.
        
    Returns:
        Text with formatting characters escaped.
    """
    if not text:
        return ""
    
    # Escape markdown-style formatting
    escape_chars = ["*", "_", "~", "`", "|", ">", "#", "+", "-", "=", ".", "!"]
    
    for char in escape_chars:
        # Only escape if not already escaped
        if char in text and f"\\{char}" not in text:
            text = text.replace(char, f"\\{char}")
    
    return text
