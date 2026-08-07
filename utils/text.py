"""Text processing utilities for Rosy Discord Bot.

This module provides functions for formatting, truncating, and
manipulating text for Discord messages.
"""

import re
from typing import Optional


def truncate_text(
    text: str,
    max_length: int = 4000,
    suffix: str = "...",
) -> str:
    """Truncate text to a maximum length.
    
    Args:
        text: Text to truncate.
        max_length: Maximum length including suffix.
        suffix: String to append when truncating.
        
    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    
    truncated_length = max_length - len(suffix)
    return text[:truncated_length] + suffix


def format_code_block(
    content: str,
    language: Optional[str] = None,
    max_length: int = 4000,
) -> str:
    """Format content in a Discord code block.
    
    Args:
        content: Content to format.
        language: Optional language identifier.
        max_length: Maximum total length.
        
    Returns:
        Formatted code block.
    """
    prefix = f"```{language or ''}\n"
    suffix = "```"
    available_length = max_length - len(prefix) - len(suffix)
    
    if len(content) > available_length:
        content = truncate_text(content, available_length)
    
    return f"{prefix}{content}{suffix}"


def escape_markdown(text: str) -> str:
    """Escape Discord markdown characters.
    
    Args:
        text: Text to escape.
        
    Returns:
        Escaped text.
    """
    # Characters that need escaping in Discord markdown
    escape_pairs = [
        ("\\", "\\\\"),  # Backslash must be first
        ("*", "\\*"),
        ("_", "\\_"),
        ("~", "\\~"),
        ("|", "\\|"),
        ("`", "\\`"),
        (">", "\\>"),
        ("#", "\\#"),
        ("+", "\\+"),
        ("-", "\\-"),
        ("=", "\\="),
        (".", "\\."),
        ("!", "\\!"),
        ("(", "\\("),
        (")", "\\)"),
    ]
    
    for char, escaped in escape_pairs:
        text = text.replace(char, escaped)
    
    return text


def remove_code_blocks(text: str) -> str:
    """Remove Discord code blocks from text.
    
    Args:
        text: Text that may contain code blocks.
        
    Returns:
        Text with code blocks removed.
    """
    # Remove fenced code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    
    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    
    return text.strip()


def extract_code_language(code_block: str) -> Optional[str]:
    """Extract the language identifier from a code block.
    
    Args:
        code_block: A Discord code block string.
        
    Returns:
        Language identifier or None.
    """
    match = re.match(r"```(\w*)\n", code_block)
    if match:
        return match.group(1) or None
    return None


def extract_code_content(code_block: str) -> str:
    """Extract the content from a code block.
    
    Args:
        code_block: A Discord code block string.
        
    Returns:
        The code content without the code block syntax.
    """
    # Remove the opening fence with optional language
    content = re.sub(r"```\w*\n?", "", code_block)
    
    # Remove the closing fence
    content = re.sub(r"```$", "", content)
    
    return content.strip()


def clean_whitespace(text: str) -> str:
    """Clean up excessive whitespace in text.
    
    Args:
        text: Text to clean.
        
    Returns:
        Text with normalized whitespace.
    """
    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)
    
    # Replace multiple newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Trim each line
    lines = [line.strip() for line in text.split("\n")]
    
    return "\n".join(lines)


def pluralize(
    word: str,
    count: int,
    plural_form: Optional[str] = None,
) -> str:
    """Pluralize a word based on count.
    
    Args:
        word: Singular form of the word.
        count: Number to check.
        plural_form: Optional explicit plural form.
        
    Returns:
        Singular or plural word based on count.
    """
    if count == 1:
        return word
    
    if plural_form:
        return plural_form
    
    # Basic English pluralization rules
    if word.endswith("y") and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    elif word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    else:
        return word + "s"


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted duration string.
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f}h"
    
    days = hours / 24
    return f"{days:.1f}d"


def format_number(num: int) -> str:
    """Format a number with thousand separators.
    
    Args:
        num: Number to format.
        
    Returns:
        Formatted number string.
    """
    return f"{num:,}"


def create_progress_bar(
    current: float,
    maximum: float,
    width: int = 20,
    filled_char: str = "█",
    empty_char: str = "░",
) -> str:
    """Create a text-based progress bar.
    
    Args:
        current: Current progress value.
        maximum: Maximum progress value.
        width: Width of the bar in characters.
        filled_char: Character for filled portion.
        empty_char: Character for empty portion.
        
    Returns:
        Progress bar string.
    """
    if maximum == 0:
        percentage = 0
    else:
        percentage = min(current / maximum, 1.0)
    
    filled_width = int(width * percentage)
    empty_width = width - filled_width
    
    return f"[{filled_char * filled_width}{empty_char * empty_width}]"


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text.
    
    Args:
        text: Text to search.
        
    Returns:
        List of URLs found.
    """
    url_pattern = re.compile(
        r"https?://"
        r"(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
        r"(?:/[^\s]*)?"
    )
    
    return url_pattern.findall(text)


def mask_sensitive_content(text: str) -> str:
    """Mask potentially sensitive content in text.
    
    Args:
        text: Text to mask.
        
    Returns:
        Text with sensitive content masked.
    """
    # Mask API keys (common patterns)
    patterns = [
        # Generic API key pattern
        (r"[a-zA-Z0-9]{20,64}", lambda m: m.group(0)[:4] + "*" * (len(m.group(0)) - 8) + m.group(0)[-4:]),
        # URLs with credentials
        (r"://[^:]+:[^@]+@", "://***:***@"),
        # Bearer tokens
        (r"Bearer [a-zA-Z0-9\-_]+", "Bearer ***"),
    ]
    
    for pattern, replacement in patterns:
        if callable(replacement):
            text = re.sub(pattern, replacement, text)
        else:
            text = re.sub(pattern, replacement, text)
    
    return text
