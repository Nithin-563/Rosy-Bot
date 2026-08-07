"""Provider factory for creating AI provider instances.

This module provides a factory pattern implementation for creating
AI provider instances based on configuration.
"""

from typing import Optional

from config import settings
from providers.base import (
    AIProviderBase,
    AIProviderType,
    ProviderConfig,
)
from providers.openrouter import OpenRouterProvider
from utils.logging import get_logger

logger = get_logger(__name__)


class ProviderFactory:
    """Factory for creating AI provider instances.
    
    This factory creates and manages AI provider instances based on
    the provider type. It supports dependency injection for testing
    and allows easy addition of new providers.
    """
    
    _providers: dict[AIProviderType, type[AIProviderBase]] = {
        AIProviderType.OPENROUTER: OpenRouterProvider,
    }
    
    _instances: dict[str, AIProviderBase] = {}
    
    @classmethod
    def register_provider(
        cls,
        provider_type: AIProviderType,
        provider_class: type[AIProviderBase],
    ) -> None:
        """Register a new provider type.
        
        Args:
            provider_type: The type identifier for the provider.
            provider_class: The provider class to register.
        """
        cls._providers[provider_type] = provider_class
        logger.info(f"Registered new provider: {provider_type.value}")
    
    @classmethod
    def create(
        cls,
        provider_type: AIProviderType,
        config: Optional[ProviderConfig] = None,
        use_cache: bool = True,
    ) -> AIProviderBase:
        """Create a provider instance.
        
        Args:
            provider_type: The type of provider to create.
            config: Optional configuration for the provider.
            use_cache: Whether to use cached instances.
            
        Returns:
            AIProviderBase: The provider instance.
            
        Raises:
            ValueError: If the provider type is not supported.
        """
        if provider_type not in cls._providers:
            raise ValueError(
                f"Unsupported provider type: {provider_type.value}. "
                f"Supported types: {[p.value for p in cls._providers.keys()]}"
            )
        
        cache_key = f"{provider_type.value}"
        if use_cache and cache_key in cls._instances:
            return cls._instances[cache_key]
        
        provider_class = cls._providers[provider_type]
        
        # Create default config if not provided
        if config is None:
            if provider_type == AIProviderType.OPENROUTER:
                config = ProviderConfig(
                    provider_type=provider_type,
                    api_key=settings.openrouter_api_key,
                    model=settings.openrouter_default_model,
                    site_url=settings.openrouter_site_url,
                    site_name=settings.openrouter_site_name,
                )
            else:
                raise ValueError(
                    f"Configuration required for provider type: {provider_type.value}"
                )
        
        provider = provider_class(config)
        cls._instances[cache_key] = provider
        
        return provider
    
    @classmethod
    def get_default(cls) -> AIProviderBase:
        """Get the default provider (OpenRouter).
        
        Returns:
            AIProviderBase: The default provider instance.
        """
        return cls.create(AIProviderType.OPENROUTER)
    
    @classmethod
    async def initialize_all(cls) -> None:
        """Initialize all registered providers."""
        for provider in cls._instances.values():
            await provider.initialize()
        logger.info("All providers initialized")
    
    @classmethod
    async def close_all(cls) -> None:
        """Close all provider connections."""
        for provider in cls._instances.values():
            await provider.close()
        cls._instances.clear()
        logger.info("All providers closed")
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the provider cache."""
        cls._instances.clear()
