"""Conversation context builders for AI requests.

This module provides utilities for building conversation context
with personality adjustments and adaptive tone.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from providers import AIRequest, Message as AIMessage


@dataclass
class ConversationContext:
    """Represents the context for a conversation.
    
    This class holds all the context information needed to build
    an AI request, including messages, system prompts, and metadata.
    """
    
    user_id: int
    guild_id: Optional[int] = None
    channel_id: Optional[int] = None
    is_dm: bool = False
    username: Optional[str] = None
    guild_name: Optional[str] = None
    
    # Personality settings
    personality_type: str = "friendly"
    response_length: str = "medium"
    humor_level: int = 5
    formality_level: int = 5
    
    # Memory and context
    memories: list[dict[str, str]] = field(default_factory=list)
    recent_topics: list[str] = field(default_factory=list)
    conversation_tone: str = "neutral"
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    
    def to_system_prompt(self) -> str:
        """Generate a system prompt from the context.
        
        Returns:
            Formatted system prompt string.
        """
        parts = []
        
        # Base identity and behavior
        parts.append(self._get_identity_prompt())
        
        # Personality adjustments
        parts.append(self._get_personality_prompt())
        
        # Context information
        if self.guild_name:
            parts.append(f"You are chatting in the server: {self.guild_name}")
        
        if self.username:
            parts.append(f"You are talking to: {self.username}")
        
        # Memories
        if self.memories:
            parts.append(self._get_memory_prompt())
        
        # Tone guidance
        parts.append(self._get_tone_prompt())
        
        return "\n\n".join(parts)
    
    def _get_identity_prompt(self) -> str:
        """Get the base identity prompt."""
        return """You are Rosy, a helpful, friendly AI assistant in a Discord server.
You are not a human - you are an AI.
Be warm, friendly, and helpful. Don't pretend to have emotions you don't have.
If you're not sure about something, say so honestly.
Keep responses conversational and appropriate for Discord."""
    
    def _get_personality_prompt(self) -> str:
        """Get personality-adjusted prompt."""
        prompts = []
        
        # Response length
        if self.response_length == "short":
            prompts.append("Keep responses brief and to the point.")
        elif self.response_length == "long":
            prompts.append("Feel free to give detailed, comprehensive responses.")
        else:
            prompts.append("Give balanced responses - neither too short nor too long.")
        
        # Humor level
        if self.humor_level >= 7:
            prompts.append("You can be witty and include light humor when appropriate.")
        elif self.humor_level <= 3:
            prompts.append("Keep responses more serious and focused.")
        
        # Formality level
        if self.formality_level >= 7:
            prompts.append("Use a more formal tone.")
        elif self.formality_level <= 3:
            prompts.append("Use a casual, relaxed tone.")
        
        return "\n".join(prompts)
    
    def _get_memory_prompt(self) -> str:
        """Get memory-related prompt."""
        parts = ["Important context about this user:"]
        
        for mem in self.memories[:5]:  # Limit to 5 most important memories
            key = mem.get("key", "")
            content = mem.get("content", "")
            if key and content:
                parts.append(f"- {key}: {content}")
        
        return "\n".join(parts)
    
    def _get_tone_prompt(self) -> str:
        """Get tone guidance based on conversation context."""
        tone_guides = {
            "supportive": "Be encouraging and supportive.",
            "serious": "Be more serious and focused on facts.",
            "playful": "Be playful and lighthearted.",
            "neutral": "Maintain a balanced, neutral tone.",
        }
        
        return tone_guides.get(self.conversation_tone, tone_guides["neutral"])


class ContextBuilder:
    """Builder for ConversationContext objects.
    
    This class provides a fluent interface for building conversation context
    with various sources of information.
    """
    
    def __init__(self):
        """Initialize the context builder."""
        self._user_id: int = 0
        self._guild_id: Optional[int] = None
        self._channel_id: Optional[int] = None
        self._is_dm: bool = False
        self._username: Optional[str] = None
        self._guild_name: Optional[str] = None
        self._personality_type: str = "friendly"
        self._response_length: str = "medium"
        self._humor_level: int = 5
        self._formality_level: int = 5
        self._memories: list[dict[str, str]] = []
        self._recent_topics: list[str] = []
        self._conversation_tone: str = "neutral"
    
    def user(self, user_id: int, username: Optional[str] = None) -> "ContextBuilder":
        """Set user information.
        
        Args:
            user_id: Discord user ID.
            username: Discord username.
            
        Returns:
            Self for chaining.
        """
        self._user_id = user_id
        self._username = username
        return self
    
    def guild(
        self,
        guild_id: int,
        guild_name: Optional[str] = None,
    ) -> "ContextBuilder":
        """Set guild information.
        
        Args:
            guild_id: Discord guild ID.
            guild_name: Guild name.
            
        Returns:
            Self for chaining.
        """
        self._guild_id = guild_id
        self._guild_name = guild_name
        return self
    
    def channel(self, channel_id: int) -> "ContextBuilder":
        """Set channel information.
        
        Args:
            channel_id: Discord channel ID.
            
        Returns:
            Self for chaining.
        """
        self._channel_id = channel_id
        return self
    
    def dm(self, is_dm: bool = True) -> "ContextBuilder":
        """Set DM context.
        
        Args:
            is_dm: Whether this is a DM conversation.
            
        Returns:
            Self for chaining.
        """
        self._is_dm = is_dm
        return self
    
    def personality(
        self,
        personality_type: str = "friendly",
        response_length: str = "medium",
        humor_level: int = 5,
        formality_level: int = 5,
    ) -> "ContextBuilder":
        """Set personality settings.
        
        Args:
            personality_type: Type of personality.
            response_length: Desired response length.
            humor_level: Humor level (1-10).
            formality_level: Formality level (1-10).
            
        Returns:
            Self for chaining.
        """
        self._personality_type = personality_type
        self._response_length = response_length
        self._humor_level = humor_level
        self._formality_level = formality_level
        return self
    
    def add_memory(self, key: str, content: str) -> "ContextBuilder":
        """Add a memory to the context.
        
        Args:
            key: Memory key.
            content: Memory content.
            
        Returns:
            Self for chaining.
        """
        self._memories.append({"key": key, "content": content})
        return self
    
    def memories(self, memories: list[dict[str, str]]) -> "ContextBuilder":
        """Set all memories.
        
        Args:
            memories: List of memory dictionaries.
            
        Returns:
            Self for chaining.
        """
        self._memories = memories
        return self
    
    def add_topic(self, topic: str) -> "ContextBuilder":
        """Add a recent topic.
        
        Args:
            topic: Topic string.
            
        Returns:
            Self for chaining.
        """
        self._recent_topics.append(topic)
        return self
    
    def tone(self, conversation_tone: str) -> "ContextBuilder":
        """Set conversation tone.
        
        Args:
            conversation_tone: Desired tone.
            
        Returns:
            Self for chaining.
        """
        self._conversation_tone = conversation_tone
        return self
    
    def build(self) -> ConversationContext:
        """Build the ConversationContext object.
        
        Returns:
            Built ConversationContext.
        """
        return ConversationContext(
            user_id=self._user_id,
            guild_id=self._guild_id,
            channel_id=self._channel_id,
            is_dm=self._is_dm,
            username=self._username,
            guild_name=self._guild_name,
            personality_type=self._personality_type,
            response_length=self._response_length,
            humor_level=self._humor_level,
            formality_level=self._formality_level,
            memories=self._memories,
            recent_topics=self._recent_topics,
            conversation_tone=self._conversation_tone,
        )


def detect_conversation_tone(messages: list[AIMessage]) -> str:
    """Detect the tone of a conversation from recent messages.
    
    Args:
        messages: Recent messages in the conversation.
        
    Returns:
        Detected tone string.
    """
    if not messages:
        return "neutral"
    
    # Simple heuristic-based detection
    recent = messages[-5:]  # Check last 5 messages
    
    happy_indicators = ["😊", "😄", "😁", "great", "awesome", "amazing", "love"]
    serious_indicators = ["serious", "important", "urgent", "critical", "!"]
    playful_indicators = ["haha", "lol", "lmao", "xd", "wanna", "gonna"]
    
    happy_count = sum(1 for msg in recent for ind in happy_indicators if ind in msg.content.lower())
    serious_count = sum(1 for msg in recent for ind in serious_indicators if ind in msg.content.lower())
    playful_count = sum(1 for msg in recent for ind in playful_indicators if ind in msg.content.lower())
    
    counts = {
        "supportive": happy_count,
        "serious": serious_count,
        "playful": playful_count,
    }
    
    max_tone = max(counts, key=counts.get)  # type: ignore
    
    # Only return detected tone if it has significant indicators
    if counts[max_tone] >= 2:
        return max_tone
    
    return "neutral"
