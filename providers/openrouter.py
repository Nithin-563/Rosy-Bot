"""OpenRouter AI provider implementation.

This module provides an implementation of the AIProviderBase interface
for the OpenRouter service, which acts as a unified gateway to multiple
AI providers including OpenAI, Anthropic, Google, and open-source models.
"""

import json
from typing import Any, Callable, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import settings
from providers.base import (
    AIProviderBase,
    AIProviderType,
    AIRequest,
    AIResponse,
    ModelInfo,
    ProviderConfig,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    InvalidRequestError,
)
from utils.logging import get_logger

logger = get_logger(__name__)


class OpenRouterProvider(AIProviderBase):
    """OpenRouter AI provider implementation.
    
    OpenRouter provides unified access to multiple AI providers through
    a single API interface. It supports free routing to find the best
    available model.
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        """Initialize the OpenRouter provider.
        
        Args:
            config: Provider configuration. If not provided, uses default settings.
        """
        self._config = config or self._create_default_config()
        self._client: Optional[httpx.AsyncClient] = None
    
    def _create_default_config(self) -> ProviderConfig:
        """Create default configuration from environment settings."""
        return ProviderConfig(
            provider_type=AIProviderType.OPENROUTER,
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_default_model,
            temperature=0.7,
            max_tokens=2048,
            site_url=settings.openrouter_site_url,
            site_name=settings.openrouter_site_name,
        )
    
    @property
    def provider_type(self) -> AIProviderType:
        """Return the provider type."""
        return AIProviderType.OPENROUTER
    
    @property
    def default_model(self) -> str:
        """Return the default model."""
        return settings.openrouter_default_model
    
    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self._config.timeout,
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": self._config.site_url or "",
                    "X-Title": self._config.site_name or "Rosy Bot",
                },
            )
        logger.info("OpenRouter provider initialized")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def validate_config(self) -> bool:
        """Validate the OpenRouter configuration."""
        if not self._config.api_key:
            logger.error("OpenRouter API key is missing")
            return False
        
        try:
            if self._client is None:
                await self.initialize()
            
            response = await self._client.get("/models")
            
            if response.status_code == 401:
                logger.error("OpenRouter authentication failed")
                return False
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenRouter validation failed: {e}")
            return False
    
    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def chat(self, request: AIRequest) -> AIResponse:
        """Send a chat request to OpenRouter.
        
        Args:
            request: The chat request.
            
        Returns:
            AIResponse: The response from OpenRouter.
        """
        if self._client is None:
            await self.initialize()
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        payload: dict[str, Any] = {
            "model": request.model or self._config.model,
            "messages": messages,
            "temperature": request.temperature or self._config.temperature,
            "max_tokens": request.max_tokens or self._config.max_tokens,
        }
        
        if request.stop:
            payload["stop"] = request.stop
        
        logger.debug(
            "Sending chat request to OpenRouter",
            extra={"model": payload["model"], "message_count": len(messages)},
        )
        
        try:
            response = await self._client.post("/chat/completions", json=payload)
            
            if response.status_code == 429:
                retry_after = float(response.headers.get("retry-after", 60))
                raise RateLimitError(
                    "OpenRouter rate limit exceeded",
                    retry_after=retry_after,
                    provider="openrouter",
                )
            
            if response.status_code == 401:
                raise AuthenticationError(
                    "OpenRouter authentication failed. Check your API key.",
                    provider="openrouter",
                )
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise InvalidRequestError(
                    f"OpenRouter request failed: {error_data.get('error', {}).get('message', 'Unknown error')}",
                    provider="openrouter",
                )
            
            data = response.json()
            return self._parse_response(data)
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during OpenRouter request: {e}")
            raise ProviderError(
                f"HTTP error: {str(e)}",
                provider="openrouter",
            )
    
    async def chat_stream(
        self,
        request: AIRequest,
        callback: Callable[[str], None],
    ) -> AIResponse:
        """Send a streaming chat request to OpenRouter.
        
        Args:
            request: The chat request.
            callback: Callback function to handle streamed content.
            
        Returns:
            AIResponse: The final response from OpenRouter.
        """
        if self._client is None:
            await self.initialize()
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        payload: dict[str, Any] = {
            "model": request.model or self._config.model,
            "messages": messages,
            "temperature": request.temperature or self._config.temperature,
            "max_tokens": request.max_tokens or self._config.max_tokens,
            "stream": True,
        }
        
        if request.stop:
            payload["stop"] = request.stop
        
        full_content = []
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        finish_reason = "stop"
        
        try:
            async with self._client.stream("POST", "/chat/completions", json=payload) as response:
                if response.status_code == 429:
                    retry_after = float(response.headers.get("retry-after", 60))
                    raise RateLimitError(
                        "OpenRouter rate limit exceeded",
                        retry_after=retry_after,
                        provider="openrouter",
                    )
                
                if response.status_code == 401:
                    raise AuthenticationError(
                        "OpenRouter authentication failed",
                        provider="openrouter",
                    )
                
                if response.status_code != 200:
                    error_data = await response.json() if response.content else {}
                    raise InvalidRequestError(
                        f"OpenRouter stream failed: {error_data.get('error', {}).get('message', 'Unknown error')}",
                        provider="openrouter",
                    )
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            
                            if "content" in delta:
                                content = delta["content"]
                                full_content.append(content)
                                callback(content)
                            
                            if chunk.get("choices", [{}])[0].get("finish_reason"):
                                finish_reason = chunk["choices"][0]["finish_reason"]
                            
                            if "usage" in chunk:
                                usage = chunk["usage"]
                        except json.JSONDecodeError:
                            continue
                        except Exception:
                            continue
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during OpenRouter stream: {e}")
            raise ProviderError(
                f"HTTP error: {str(e)}",
                provider="openrouter",
            )
        
        return AIResponse(
            content="".join(full_content),
            model=request.model or self._config.model,
            usage=usage,
            finish_reason=finish_reason,
        )
    
    async def list_models(self) -> list[ModelInfo]:
        """List available models from OpenRouter.
        
        Returns:
            List of ModelInfo objects.
        """
        if self._client is None:
            await self.initialize()
        
        try:
            response = await self._client.get("/models")
            
            if response.status_code != 200:
                logger.warning(f"Failed to list models: {response.status_code}")
                return []
            
            data = response.json()
            models = []
            
            for model in data.get("data", []):
                models.append(ModelInfo(
                    id=model.get("id", ""),
                    name=model.get("name", model.get("id", "")),
                    provider=model.get("id", "").split("/")[0] if "/" in model.get("id", "") else "unknown",
                    supports_streaming=True,
                    context_length=model.get("context_length"),
                    is_free="free" in model.get("id", "").lower(),
                ))
            
            return models
            
        except Exception as e:
            logger.error(f"Error listing OpenRouter models: {e}")
            return []
    
    def _parse_response(self, data: dict[str, Any]) -> AIResponse:
        """Parse the OpenRouter response into AIResponse.
        
        Args:
            data: Raw response data from OpenRouter.
            
        Returns:
            AIResponse: Parsed response.
        """
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        return AIResponse(
            content=message.get("content", ""),
            model=data.get("model", self._config.model),
            usage=data.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=data,
        )
