"""Memory manager for conversation history and persistent memories.

This module provides the MemoryManager class which handles all memory-related
operations including conversation history, user memories, guild memories, and DM memories.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import (
    Conversation,
    Message,
    Memory,
    User,
    Guild,
)
from providers import AIRequest, Message as AIMessage
from utils.logging import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """Manages conversation history and persistent memories.
    
    This class provides a unified interface for all memory operations,
    including storing conversation history, managing user/guild memories,
    and retrieving context for AI requests.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the memory manager.
        
        Args:
            session: Async database session.
        """
        self.session = session
    
    # =========================================================================
    # User Management
    # =========================================================================
    
    async def get_or_create_user(self, user_id: int, username: str, global_name: Optional[str] = None) -> User:
        """Get or create a user record.
        
        Args:
            user_id: Discord user ID.
            username: Discord username.
            global_name: Global Discord name.
            
        Returns:
            User record.
        """
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                user_id=user_id,
                username=username,
                global_name=global_name,
            )
            self.session.add(user)
            await self.session.flush()
            logger.debug(f"Created new user record: {user_id}")
        
        return user
    
    async def get_or_create_guild(self, guild_id: int, name: Optional[str] = None) -> Guild:
        """Get or create a guild record.
        
        Args:
            guild_id: Discord guild ID.
            name: Guild name.
            
        Returns:
            Guild record.
        """
        result = await self.session.execute(
            select(Guild).where(Guild.guild_id == guild_id)
        )
        guild = result.scalar_one_or_none()
        
        if not guild:
            guild = Guild(
                guild_id=guild_id,
                name=name,
                is_active=True,
            )
            self.session.add(guild)
            await self.session.flush()
            logger.debug(f"Created new guild record: {guild_id}")
        
        return guild
    
    # =========================================================================
    # Conversation Management
    # =========================================================================
    
    async def get_or_create_conversation(
        self,
        user_id: int,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        is_dm: bool = False,
    ) -> Conversation:
        """Get or create a conversation context.
        
        Args:
            user_id: Discord user ID.
            guild_id: Discord guild ID (if applicable).
            channel_id: Discord channel ID.
            is_dm: Whether this is a DM conversation.
            
        Returns:
            Conversation record.
        """
        # Build query based on conversation type
        if is_dm:
            query = select(Conversation).where(
                Conversation.user_id == User.id,
                User.user_id == user_id,
                Conversation.is_dm == True,
            )
        else:
            query = select(Conversation).where(
                Conversation.guild_id == Guild.id,
                Guild.guild_id == guild_id,
                Conversation.user_id == User.id,
                User.user_id == user_id,
                Conversation.is_dm == False,
            )
        
        result = await self.session.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            # Ensure user and guild exist
            user = await self.get_or_create_user(user_id, str(user_id))
            
            if guild_id:
                await self.get_or_create_guild(guild_id)
            
            # Get the database IDs
            if guild_id:
                guild_result = await self.session.execute(
                    select(Guild).where(Guild.guild_id == guild_id)
                )
                guild = guild_result.scalar_one()
            else:
                guild = None
            
            conversation_type = "dm" if is_dm else "guild"
            conversation = Conversation(
                guild_id=guild.id if guild else None,
                user_id=user.id,
                channel_id=channel_id,
                conversation_type=conversation_type,
                is_dm=is_dm,
                is_active=True,
            )
            self.session.add(conversation)
            await self.session.flush()
            logger.debug(f"Created new conversation for user {user_id}")
        
        return conversation
    
    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        message_type: str = "user",
        discord_message_id: Optional[int] = None,
        token_count: Optional[int] = None,
    ) -> Message:
        """Add a message to conversation history.
        
        Args:
            conversation_id: Database ID of the conversation.
            role: Message role (system, user, assistant).
            content: Message content.
            message_type: Type of message (user, bot, system).
            discord_message_id: Discord message ID.
            token_count: Token count for the message.
            
        Returns:
            Created Message record.
        """
        message = Message(
            conversation_id=conversation_id,
            discord_message_id=discord_message_id,
            role=role,
            content=content,
            message_type=message_type,
            token_count=token_count,
        )
        self.session.add(message)
        await self.session.flush()
        
        logger.debug(
            f"Added message to conversation {conversation_id}",
            role=role,
            content_length=len(content),
        )
        
        return message
    
    async def get_conversation_history(
        self,
        conversation_id: int,
        limit: int = 50,
    ) -> list[Message]:
        """Get conversation history.
        
        Args:
            conversation_id: Database ID of the conversation.
            limit: Maximum number of messages to retrieve.
            
        Returns:
            List of Message records.
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        
        # Return in chronological order
        messages = list(reversed(result.scalars().all()))
        return messages
    
    async def clear_conversation_history(self, conversation_id: int) -> int:
        """Clear conversation history.
        
        Args:
            conversation_id: Database ID of the conversation.
            
        Returns:
            Number of messages deleted.
        """
        result = await self.session.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )
        
        logger.info(f"Cleared {result.rowcount} messages from conversation {conversation_id}")
        return result.rowcount
    
    # =========================================================================
    # Persistent Memory
    # =========================================================================
    
    async def add_memory(
        self,
        user_id: int,
        memory_type: str,
        key: str,
        content: str,
        guild_id: Optional[int] = None,
        importance: int = 5,
    ) -> Memory:
        """Add a persistent memory.
        
        Args:
            user_id: Discord user ID.
            memory_type: Type of memory (fact, preference, etc.).
            key: Memory key identifier.
            content: Memory content.
            guild_id: Discord guild ID (if applicable).
            importance: Memory importance level (1-10).
            
        Returns:
            Created Memory record.
        """
        # Get or create user and guild
        user = await self.get_or_create_user(user_id, str(user_id))
        
        guild_db_id = None
        if guild_id:
            guild = await self.get_or_create_guild(guild_id)
            guild_db_id = guild.id
        
        # Check if memory already exists
        query = select(Memory).where(
            Memory.user_id == user.id,
            Memory.memory_type == memory_type,
            Memory.key == key,
        )
        if guild_id:
            query = query.where(Memory.guild_id == guild_db_id)
        
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing memory
            existing.content = content
            existing.importance = importance
            existing.updated_at = datetime.utcnow()
            return existing
        
        # Create new memory
        memory = Memory(
            guild_id=guild_db_id,
            user_id=user.id,
            memory_type=memory_type,
            key=key,
            content=content,
            importance=importance,
            access_count=0,
        )
        self.session.add(memory)
        await self.session.flush()
        
        logger.debug(f"Added memory: {memory_type}/{key}")
        return memory
    
    async def get_memories(
        self,
        user_id: int,
        memory_type: Optional[str] = None,
        guild_id: Optional[int] = None,
        limit: int = 20,
    ) -> list[Memory]:
        """Get memories for a user.
        
        Args:
            user_id: Discord user ID.
            memory_type: Filter by memory type.
            guild_id: Filter by guild.
            limit: Maximum memories to retrieve.
            
        Returns:
            List of Memory records.
        """
        user_result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return []
        
        query = select(Memory).where(Memory.user_id == user.id)
        
        if guild_id:
            guild_result = await self.session.execute(
                select(Guild).where(Guild.guild_id == guild_id)
            )
            guild = guild_result.scalar_one_or_none()
            if guild:
                query = query.where(Memory.guild_id == guild.id)
        
        if memory_type:
            query = query.where(Memory.memory_type == memory_type)
        
        query = query.order_by(Memory.importance.desc(), Memory.last_accessed.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_memory_access(self, memory_id: int) -> None:
        """Update memory access statistics.
        
        Args:
            memory_id: Database ID of the memory.
        """
        await self.session.execute(
            update(Memory)
            .where(Memory.id == memory_id)
            .values(
                access_count=Memory.access_count + 1,
                last_accessed=datetime.utcnow(),
            )
        )
    
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory.
        
        Args:
            memory_id: Database ID of the memory.
            
        Returns:
            True if deleted, False if not found.
        """
        result = await self.session.execute(
            delete(Memory).where(Memory.id == memory_id)
        )
        
        if result.rowcount > 0:
            logger.debug(f"Deleted memory {memory_id}")
            return True
        return False
    
    async def clear_all_memories(
        self,
        user_id: int,
        guild_id: Optional[int] = None,
        memory_type: Optional[str] = None,
    ) -> int:
        """Clear all memories for a user.
        
        Args:
            user_id: Discord user ID.
            guild_id: Filter by guild.
            memory_type: Filter by type.
            
        Returns:
            Number of memories deleted.
        """
        user_result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return 0
        
        query = delete(Memory).where(Memory.user_id == user.id)
        
        if guild_id:
            guild_result = await self.session.execute(
                select(Guild).where(Guild.guild_id == guild_id)
            )
            guild = guild_result.scalar_one_or_none()
            if guild:
                query = query.where(Memory.guild_id == guild.id)
        
        if memory_type:
            query = query.where(Memory.memory_type == memory_type)
        
        result = await self.session.execute(query)
        logger.info(f"Cleared {result.rowcount} memories for user {user_id}")
        return result.rowcount
    
    # =========================================================================
    # Context Building for AI
    # =========================================================================
    
    async def build_context_for_ai(
        self,
        user_id: int,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        is_dm: bool = False,
        message_count: int = 50,
    ) -> tuple[list[AIMessage], str]:
        """Build conversation context for AI request.
        
        Args:
            user_id: Discord user ID.
            guild_id: Discord guild ID.
            channel_id: Discord channel ID.
            is_dm: Whether this is a DM conversation.
            message_count: Number of recent messages to include.
            
        Returns:
            Tuple of (messages list, system prompt).
        """
        # Get conversation and history
        conversation = await self.get_or_create_conversation(
            user_id=user_id,
            guild_id=guild_id,
            channel_id=channel_id,
            is_dm=is_dm,
        )
        
        history = await self.get_conversation_history(conversation.id, limit=message_count)
        
        # Convert to AI messages
        messages = [
            AIMessage(role=msg.role, content=msg.content)
            for msg in history
        ]
        
        # Build system prompt with memories
        system_parts = []
        
        # Add user info
        user = await self.get_or_create_user(user_id, str(user_id))
        system_parts.append(f"User: {user.global_name or user.username or 'Unknown'}")
        
        # Add guild context
        if guild_id:
            guild = await self.get_or_create_guild(guild_id)
            system_parts.append(f"Server: {guild.name or 'Unknown'}")
        
        # Add memories
        memories = await self.get_memories(
            user_id=user_id,
            guild_id=guild_id,
            limit=10,
        )
        
        if memories:
            memory_parts = ["Important context:"]
            for mem in memories:
                memory_parts.append(f"- {mem.key}: {mem.content}")
            system_parts.append("\n".join(memory_parts))
        
        system_prompt = "\n".join(system_parts)
        
        return messages, system_prompt
