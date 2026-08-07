"""Tests for Rosy Discord Bot.

This module provides basic tests to verify the bot components work correctly.
"""

import pytest

from config import settings
from database import Base, Guild, User, Conversation, Message, Memory
from providers import (
    OpenRouterProvider,
    ProviderFactory,
    AIProviderType,
    AIRequest,
    Message as AIMessage,
)
from memory import MemoryManager, ConversationContext, ContextBuilder
from services import AIService, PersonalityService
from bot import RosyBot, BotService
from utils.text import truncate_text, format_code_block, escape_markdown
from utils.encryption import encrypt_key, decrypt_key, generate_encryption_key
from utils.validation import sanitize_input, validate_discord_id


class TestConfig:
    """Test configuration module."""
    
    def test_settings_load(self):
        """Test that settings can be loaded."""
        assert settings is not None
    
    def test_database_url_has_asyncpg(self):
        """Test that database URL uses asyncpg."""
        assert "asyncpg" in settings.database_url


class TestProviders:
    """Test AI providers."""
    
    def test_provider_factory(self):
        """Test provider factory creates OpenRouter provider."""
        provider = ProviderFactory.get_default()
        assert isinstance(provider, OpenRouterProvider)
    
    def test_provider_type(self):
        """Test provider type is OpenRouter."""
        provider = ProviderFactory.get_default()
        assert provider.provider_type == AIProviderType.OPENROUTER
    
    def test_ai_request_creation(self):
        """Test AI request creation."""
        request = AIRequest(
            messages=[AIMessage(role="user", content="Hello")],
            model="test-model",
            temperature=0.7,
        )
        assert len(request.messages) == 1
        assert request.messages[0].content == "Hello"


class TestUtils:
    """Test utility functions."""
    
    def test_truncate_text(self):
        """Test text truncation."""
        text = "Hello, World!"
        truncated = truncate_text(text, max_length=5)
        assert len(truncated) <= 5
    
    def test_truncate_text_short(self):
        """Test text truncation with short text."""
        text = "Hi"
        truncated = truncate_text(text, max_length=10)
        assert truncated == "Hi"
    
    def test_format_code_block(self):
        """Test code block formatting."""
        content = "print('hello')"
        formatted = format_code_block(content, language="python")
        assert "```python" in formatted
        assert "print('hello')" in formatted
    
    def test_escape_markdown(self):
        """Test markdown escaping."""
        text = "*bold* _italic_"
        escaped = escape_markdown(text)
        assert "\\*" in escaped
        assert "\\_" in escaped
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        text = "  Hello World  "
        sanitized = sanitize_input(text)
        assert sanitized == "Hello World"
    
    def test_validate_discord_id_valid(self):
        """Test Discord ID validation with valid ID."""
        valid = validate_discord_id("123456789012345678")
        assert valid is True
    
    def test_validate_discord_id_invalid(self):
        """Test Discord ID validation with invalid ID."""
        invalid = validate_discord_id("not-a-number")
        assert invalid is False
    
    def test_encryption_roundtrip(self):
        """Test encryption and decryption roundtrip."""
        if not settings.encryption_secret:
            pytest.skip("ENCRYPTION_SECRET not set")
        
        original = "my-secret-api-key"
        encrypted = encrypt_key(original)
        decrypted = decrypt_key(encrypted)
        assert decrypted == original
    
    def test_generate_encryption_key(self):
        """Test encryption key generation."""
        key = generate_encryption_key()
        assert len(key) == 64  # 32 bytes = 64 hex chars


class TestMemory:
    """Test memory module."""
    
    def test_context_builder(self):
        """Test context builder."""
        context = (
            ContextBuilder()
            .user(123, "TestUser")
            .guild(456, "TestGuild")
            .dm(True)
            .personality("friendly", "medium", 5, 5)
            .build()
        )
        assert context.user_id == 123
        assert context.username == "TestUser"
        assert context.guild_name == "TestGuild"
        assert context.is_dm is True
        assert context.personality_type == "friendly"
    
    def test_context_to_system_prompt(self):
        """Test system prompt generation."""
        context = ConversationContext(
            user_id=123,
            username="TestUser",
            personality_type="friendly",
        )
        prompt = context.to_system_prompt()
        assert len(prompt) > 0
        assert "TestUser" in prompt


class TestPersonalityService:
    """Test personality service."""
    
    def test_available_types(self):
        """Test available personality types."""
        service = PersonalityService()
        types = service.get_available_types()
        assert "friendly" in types
        assert "professional" in types
        assert "playful" in types
    
    def test_get_type_settings(self):
        """Test getting personality type settings."""
        service = PersonalityService()
        settings = service.get_type_settings("friendly")
        assert settings is not None
        assert "response_length" in settings
    
    def test_generate_personality_prompt(self):
        """Test personality prompt generation."""
        service = PersonalityService()
        prompt = service.generate_personality_prompt(
            "friendly",
            "medium",
            5,
            5,
        )
        assert len(prompt) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
