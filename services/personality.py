"""Personality service for adaptive behavior adjustments.

This module provides the PersonalityService class that handles
personality configuration and adaptive tone adjustments based on
conversation context.
"""

from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import Guild, PersonalityPreference
from database.session import get_session_context
from memory.context import ConversationContext
from utils.logging import get_logger

logger = get_logger(__name__)


class PersonalityService:
    """Service for managing personality and adaptive behavior.
    
    This class provides methods for configuring personality settings
    and adjusting behavior based on conversation context.
    """
    
    # Personality types and their default settings
    PERSONALITY_TYPES = {
        "friendly": {
            "response_length": "medium",
            "humor_level": 5,
            "formality_level": 5,
            "traits": {
                "warm": 0.8,
                "helpful": 0.9,
                "patient": 0.8,
            },
        },
        "professional": {
            "response_length": "medium",
            "humor_level": 3,
            "formality_level": 7,
            "traits": {
                "formal": 0.8,
                "precise": 0.9,
                "helpful": 0.9,
            },
        },
        "playful": {
            "response_length": "short",
            "humor_level": 8,
            "formality_level": 3,
            "traits": {
                "fun": 0.9,
                "witty": 0.8,
                "casual": 0.9,
            },
        },
        "supportive": {
            "response_length": "medium",
            "humor_level": 4,
            "formality_level": 4,
            "traits": {
                "empathetic": 0.9,
                "encouraging": 0.9,
                "patient": 0.9,
            },
        },
    }
    
    async def get_guild_personality(
        self,
        guild_id: int,
    ) -> Optional[dict[str, Any]]:
        """Get personality settings for a guild.
        
        Args:
            guild_id: Discord guild ID.
            
        Returns:
            Personality settings dictionary or None.
        """
        async with get_session_context() as session:
            result = await session.execute(
                select(Guild).where(Guild.guild_id == guild_id)
            )
            guild = result.scalar_one_or_none()
            
            if not guild or not guild.personality:
                return None
            
            return {
                "personality_type": guild.personality.personality_type,
                "response_length": guild.personality.response_length,
                "humor_level": guild.personality.humor_level,
                "formality_level": guild.personality.formality_level,
                "traits": guild.personality.traits,
            }
    
    async def set_guild_personality(
        self,
        guild_id: int,
        personality_type: str,
        **kwargs,
    ) -> bool:
        """Set personality settings for a guild.
        
        Args:
            guild_id: Discord guild ID.
            personality_type: Type of personality to set.
            **kwargs: Additional personality settings.
            
        Returns:
            True if successful, False otherwise.
        """
        if personality_type not in self.PERSONALITY_TYPES:
            logger.warning(f"Unknown personality type: {personality_type}")
            return False
        
        defaults = self.PERSONALITY_TYPES[personality_type].copy()
        defaults.update(kwargs)
        
        async with get_session_context() as session:
            # Get or create guild
            result = await session.execute(
                select(Guild).where(Guild.guild_id == guild_id)
            )
            guild = result.scalar_one_or_none()
            
            if not guild:
                guild = Guild(guild_id=guild_id, is_active=True)
                session.add(guild)
                await session.flush()
            
            # Get or create personality
            if guild.personality:
                personality = guild.personality
            else:
                personality = PersonalityPreference(guild_id=guild.id)
                session.add(personality)
                guild.personality = personality
                await session.flush()
            
            # Update settings
            personality.personality_type = personality_type
            personality.response_length = defaults.get(
                "response_length", "medium"
            )
            personality.humor_level = defaults.get("humor_level", 5)
            personality.formality_level = defaults.get("formality_level", 5)
            personality.traits = defaults.get("traits", {})
            
            logger.info(
                f"Updated personality for guild {guild_id}",
                personality_type=personality_type,
            )
            
            return True
    
    async def adjust_tone(
        self,
        context: ConversationContext,
        guild_id: Optional[int] = None,
    ) -> ConversationContext:
        """Adjust conversation context tone based on guild settings.
        
        Args:
            context: Base conversation context.
            guild_id: Discord guild ID.
            
        Returns:
            Adjusted conversation context.
        """
        if not guild_id:
            return context
        
        personality = await self.get_guild_personality(guild_id)
        
        if not personality:
            return context
        
        # Apply personality settings to context
        context.personality_type = personality.get(
            "personality_type", context.personality_type
        )
        context.response_length = personality.get(
            "response_length", context.response_length
        )
        context.humor_level = personality.get(
            "humor_level", context.humor_level
        )
        context.formality_level = personality.get(
            "formality_level", context.formality_level
        )
        
        # Update memories with traits
        traits = personality.get("traits", {})
        for key, value in traits.items():
            if value > 0.7:
                context.memories.append({
                    "key": f"trait_{key}",
                    "content": f"User appreciates {key} responses",
                })
        
        return context
    
    def get_available_types(self) -> list[str]:
        """Get list of available personality types.
        
        Returns:
            List of personality type names.
        """
        return list(self.PERSONALITY_TYPES.keys())
    
    def get_type_settings(self, personality_type: str) -> Optional[dict]:
        """Get default settings for a personality type.
        
        Args:
            personality_type: The personality type name.
            
        Returns:
            Settings dictionary or None.
        """
        return self.PERSONALITY_TYPES.get(personality_type)
    
    def generate_personality_prompt(
        self,
        personality_type: str,
        response_length: str = "medium",
        humor_level: int = 5,
        formality_level: int = 5,
    ) -> str:
        """Generate a system prompt for a personality.
        
        Args:
            personality_type: Type of personality.
            response_length: Desired response length.
            humor_level: Humor level (1-10).
            formality_level: Formality level (1-10).
            
        Returns:
            Generated system prompt.
        """
        parts = []
        
        # Add personality type guidance
        if personality_type in self.PERSONALITY_TYPES:
            traits = self.PERSONALITY_TYPES[personality_type].get("traits", {})
            trait_parts = []
            for trait, value in traits.items():
                if value > 0.7:
                    trait_parts.append(trait)
            
            if trait_parts:
                parts.append(f"Your personality is: {', '.join(trait_parts)}")
        
        # Response length guidance
        length_guides = {
            "short": "Keep responses concise and to the point.",
            "medium": "Provide balanced responses that are informative but not excessive.",
            "long": "Feel free to provide detailed, comprehensive responses.",
        }
        parts.append(length_guides.get(response_length, length_guides["medium"]))
        
        # Humor guidance
        if humor_level >= 7:
            parts.append("Include light humor and wit when appropriate.")
        elif humor_level <= 3:
            parts.append("Keep responses serious and focused.")
        
        # Formality guidance
        if formality_level >= 7:
            parts.append("Use a more formal tone.")
        elif formality_level <= 3:
            parts.append("Use a casual, friendly tone.")
        
        return "\n".join(parts)
