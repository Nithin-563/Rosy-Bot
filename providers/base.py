"""Base AI provider interface and common types.

This module defines the abstract base class that all AI providers must implement,
along with common data structures used across providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class AIProviderType(str, Enum):
    """Supported AI provider types."""
    
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROQ = "groq"
    MISTRAL = "mistral"
    OLLAMA = "ollama"


class ProviderError(Exception):
    """Base exception for provider-related errors."""
    
    def __init__(self, message: str, provider: Optional[str] = None, **kwargs: Any):
        super().__init__(message)
        self.provider = provider
        self.extra_data = kwargs


class RateLimitError(ProviderError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Exception raised when authentication fails."""
    
    pass


class InvalidRequestError(ProviderError):
    """Exception raised when request is invalid."""
    
    pass


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    
    provider_type: AIProviderType
    api_key: str
    model: str
    api_endpoint: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: float = 60.0
    extra_headers: dict[str, str] = field(default_factory=dict)
    site_url: Optional[str] = None
    site_name: Optional[str] = None


@dataclass
class Message:
    """A message in a conversation."""
    
    role: str
    content: str


@dataclass
class AIRequest:
    """A request to the AI provider."""
    
    messages: list[Message]
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    system_prompt: Optional[str] = None
    stop: Optional[list[str]] = None


@dataclass
class AIResponse:
    """A response from the AI provider."""
    
    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str
    raw_response: Optional[dict[str, Any]] = None


@dataclass
class ModelInfo:
    """Information about an available model."""
    
    id: str
    name: str
    provider: str
    supports_streaming: bool = True
    context_length: Optional[int] = None
    is_free: bool = False


class AIProviderBase(ABC):
    """Abstract base class for AI providers.
    
    All AI providers must implement this interface to ensure
    consistent behavior across different providers.
    """
    
    @property
    @abstractmethod
    def provider_type(self) -> AIProviderType:
        """Return the type of this provider."""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider with any necessary setup."""
        pass
    
    @abstractmethod
    async def chat(self, request: AIRequest) -> AIResponse:
        """Send a chat request to the provider.
        
        Args:
            request: The chat request containing messages and options.
            
        Returns:
            AIResponse: The response from the provider.
            
        Raises:
            RateLimitError: If rate limit is exceeded.
            AuthenticationError: If authentication fails.
            InvalidRequestError: If the request is invalid.
            ProviderError: For other provider-related errors.
        """
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        request: AIRequest,
        callback: Any,
    ) -> AIResponse:
        """Send a streaming chat request to the provider.
        
        Args:
            request: The chat request containing messages and options.
            callback: Callback function to handle streamed chunks.
            
        Returns:
            AIResponse: The final response from the provider.
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models for this provider.
        
        Returns:
            List of ModelInfo objects describing available models.
        """
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate the provider configuration.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        pass
    
    async def close(self) -> None:
        """Clean up provider resources.
        
        Override this method if the provider needs cleanup.
        """
        pass
