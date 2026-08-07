"""AI service for managing conversations and AI requests.

This module provides the AIService class that handles all AI-related
operations including message processing, conversation context building,
and response generation.
"""

from typing import Optional

from database.session import get_session_context
from memory import MemoryManager, ContextBuilder, ConversationContext
from memory.context import detect_conversation_tone
from providers import (
    AIProviderBase,
    AIRequest,
    Message as AIMessage,
    RateLimitError,
    AuthenticationError,
    ProviderError,
)
from utils.logging import get_logger

logger = get_logger(__name__)


class AIService:
    """Service for handling AI conversations.
    
    This class provides a high-level interface for AI operations,
    managing conversation context, personality adjustments, and
    error handling for AI requests.
    """
    
    def __init__(self, provider: AIProviderBase) -> None:
        """Initialize the AI service.
        
        Args:
            provider: The AI provider to use.
        """
        self.provider = provider
    
    async def chat(
        self,
        user_id: int,
        user_message: str,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        is_dm: bool = False,
        username: Optional[str] = None,
        guild_name: Optional[str] = None,
    ) -> str:
        """Process a chat message and generate a response.
        
        Args:
            user_id: Discord user ID.
            user_message: The user's message.
            guild_id: Discord guild ID.
            channel_id: Discord channel ID.
            is_dm: Whether this is a DM conversation.
            username: Discord username.
            guild_name: Discord guild name.
            
        Returns:
            Generated response string.
        """
        logger.info(
            "Processing chat message",
            user_id=user_id,
            guild_id=guild_id,
            is_dm=is_dm,
        )
        
        async with get_session_context() as session:
            memory_manager = MemoryManager(session)
            
            # Build conversation context
            messages, system_prompt = await memory_manager.build_context_for_ai(
                user_id=user_id,
                guild_id=guild_id,
                channel_id=channel_id,
                is_dm=is_dm,
            )
            
            # Build enhanced context with personality
            context = (
                ContextBuilder()
                .user(user_id, username)
                .guild(guild_id, guild_name)
                .channel(channel_id or 0)
                .dm(is_dm)
                .build()
            )
            
            # Get personality adjustments
            personality_prompt = context.to_system_prompt()
            
            # Combine system prompts
            full_system = f"{system_prompt}\n\n{personality_prompt}"
            
            # Add user message to messages
            messages.append(AIMessage(role="user", content=user_message))
            
            # Detect conversation tone from recent messages
            conversation_tone = detect_conversation_tone(messages[:-1])
            context.conversation_tone = conversation_tone
            
            # Build AI request
            request = AIRequest(
                messages=messages,
                model="",  # Use provider default
                system_prompt=full_system,
            )
            
            # Generate response
            try:
                response = await self._generate_response(request)
                return response
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit: {e}")
                retry_after = e.retry_after or 60
                return (
                    f"I'm getting a bit overwhelmed with requests right now. "
                    f"Please wait {retry_after} seconds and try again. "
                    f"Sorry for the inconvenience!"
                )
                
            except AuthenticationError:
                logger.error("AI provider authentication failed")
                return (
                    "I'm having trouble authenticating with the AI service. "
                    "Please contact the bot administrator."
                )
                
            except ProviderError as e:
                logger.error(f"AI provider error: {e}")
                return (
                    "I encountered an issue with the AI service. "
                    "Please try again in a moment."
                )
                
            except Exception as e:
                logger.error(f"Unexpected error in AI chat: {e}")
                return (
                    "I encountered an unexpected error. "
                    "Please try again later."
                )
    
    async def _generate_response(self, request: AIRequest) -> str:
        """Generate a response from the AI provider.
        
        Args:
            request: The AI request.
            
        Returns:
            Generated response string.
        """
        logger.debug(
            "Generating AI response",
            model=request.model,
            message_count=len(request.messages),
        )
        
        response = await self.provider.chat(request)
        
        logger.debug(
            "AI response generated",
            model=response.model,
            content_length=len(response.content),
            tokens=response.usage,
        )
        
        return response.content
    
    async def stream_chat(
        self,
        user_id: int,
        user_message: str,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        is_dm: bool = False,
        username: Optional[str] = None,
        guild_name: Optional[str] = None,
        callback=None,
    ) -> str:
        """Process a chat message with streaming response.
        
        Args:
            user_id: Discord user ID.
            user_message: The user's message.
            guild_id: Discord guild ID.
            channel_id: Discord channel ID.
            is_dm: Whether this is a DM conversation.
            username: Discord username.
            guild_name: Discord guild name.
            callback: Optional callback for streaming.
            
        Returns:
            Complete generated response string.
        """
        async with get_session_context() as session:
            memory_manager = MemoryManager(session)
            
            # Build context
            messages, system_prompt = await memory_manager.build_context_for_ai(
                user_id=user_id,
                guild_id=guild_id,
                channel_id=channel_id,
                is_dm=is_dm,
            )
            
            # Build personality context
            context = (
                ContextBuilder()
                .user(user_id, username)
                .guild(guild_id, guild_name)
                .dm(is_dm)
                .build()
            )
            
            full_system = f"{system_prompt}\n\n{context.to_system_prompt()}"
            
            # Add user message
            messages.append(AIMessage(role="user", content=user_message))
            
            request = AIRequest(
                messages=messages,
                model="",
                system_prompt=full_system,
            )
            
            if callback:
                return await self.provider.chat_stream(request, callback)
            else:
                return await self._generate_response(request)
    
    async def validate_provider(self) -> bool:
        """Validate the AI provider configuration.
        
        Returns:
            True if provider is valid, False otherwise.
        """
        try:
            return await self.provider.validate_config()
        except Exception as e:
            logger.error(f"Provider validation failed: {e}")
            return False
