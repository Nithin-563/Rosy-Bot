"""Discord bot client implementation.

This module provides the main RosyBot class that handles Discord
connection, event processing, and command registration.
"""

import asyncio
import re
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from database.session import get_session_context
from memory import MemoryManager
from providers import ProviderFactory
from services.ai import AIService
from utils.logging import get_logger

logger = get_logger(__name__)


class RosyBot(commands.Bot):
    """Main Discord bot client.
    
    This class extends discord.py's commands.Bot and provides
    the core functionality for Rosy including message handling,
    slash command registration, and AI integration.
    """
    
    def __init__(self) -> None:
        """Initialize the bot with configuration."""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True
        intents.members = True
        
        super().__init__(
            command_prefix=settings.command_prefix,
            intents=intents,
            description="A friendly AI assistant for Discord",
            help_command=None,
        )
        
        # Bot state
        self._ai_service: Optional[AIService] = None
        self._initialized = False
        self._start_time: Optional[float] = None
        
        # Patterns for detecting when to respond
        self._name_pattern = re.compile(r"\brosy\b", re.IGNORECASE)
        self._mention_pattern = re.compile(r"<@!?(\d+)>")
    
    async def setup_hook(self) -> None:
        """Set up the bot after initialization but before connection."""
        if self._initialized:
            return
        
        logger.info("Running bot setup_hook...")
        
        # Initialize AI service
        logger.info("Initializing AI provider...")
        provider = ProviderFactory.get_default()
        await provider.initialize()
        self._ai_service = AIService(provider)
        logger.info("AI provider initialized")
        
        # Register slash commands
        logger.info("Registering slash commands...")
        await self.register_slash_commands()
        logger.info("Slash commands registered")
        
        self._initialized = True
        logger.info("Bot setup_hook complete - ready to connect to Discord")
    
    async def on_connect(self) -> None:
        """Called when the bot has successfully connected to Discord."""
        logger.info("WebSocket connection to Discord established")
    
    async def on_disconnect(self) -> None:
        """Called when the bot disconnects from Discord."""
        logger.warning("Disconnected from Discord WebSocket")
    
    async def on_resumed(self) -> None:
        """Called when the bot resumes a connection."""
        logger.info("Resumed Discord connection")
    
    async def register_slash_commands(self) -> None:
        """Register all slash commands."""
        # Import commands here to avoid circular imports
        from commands.core import (
            ping_command,
            help_command,
            about_command,
        )
        from commands.memory import memory_command, clear_memory_command
        from commands.admin import settings_command, provider_command, model_command
        
        # Create command tree
        tree = self.tree
        
        # Core commands
        @tree.command(name="ping", description="Check if the bot is responding")
        async def ping(interaction: discord.Interaction) -> None:
            await ping_command(self, interaction)
        
        @tree.command(name="help", description="Get help with using the bot")
        async def help_cmd(
            interaction: discord.Interaction,
            command: Optional[str] = None,
        ) -> None:
            await help_command(self, interaction, command)
        
        @tree.command(name="about", description="Learn about Rosy")
        async def about(interaction: discord.Interaction) -> None:
            await about_command(self, interaction)
        
        # Memory commands
        @tree.command(name="memory", description="View your memories")
        async def memory(
            interaction: discord.Interaction,
            memory_type: Optional[str] = None,
        ) -> None:
            await memory_command(self, interaction, memory_type)
        
        @tree.command(
            name="clear_memory",
            description="Clear your conversation history or memories",
        )
        async def clear_memory(
            interaction: discord.Interaction,
            what: str = "history",
        ) -> None:
            await clear_memory_command(self, interaction, what)
        
        # Admin commands
        @tree.command(
            name="settings",
            description="View or update bot settings (admin only)",
        )
        @app_commands.describe(what="What to view or update")
        async def settings_cmd(
            interaction: discord.Interaction,
            what: Optional[str] = None,
            value: Optional[str] = None,
        ) -> None:
            await settings_command(self, interaction, what, value)
        
        @tree.command(
            name="provider",
            description="Configure AI provider settings (admin only)",
        )
        @app_commands.describe(action="Action to perform")
        async def provider_cmd(
            interaction: discord.Interaction,
            action: str = "status",
            provider_name: Optional[str] = None,
            api_key: Optional[str] = None,
        ) -> None:
            await provider_command(self, interaction, action, provider_name, api_key)
        
        @tree.command(
            name="model",
            description="Configure AI model settings (admin only)",
        )
        @app_commands.describe(
            action="Action to perform",
            model_name="Model name (e.g., openrouter/auto, gpt-4, claude-3)",
        )
        async def model_cmd(
            interaction: discord.Interaction,
            action: str = "status",
            model_name: Optional[str] = None,
        ) -> None:
            await model_command(self, interaction, action, model_name)
        
        logger.info("Slash commands registered")
    
    @property
    def ai_service(self) -> AIService:
        """Get the AI service instance."""
        if not self._ai_service:
            raise RuntimeError("Bot not initialized")
        return self._ai_service
    
    @property
    def start_time(self) -> float:
        """Get bot start time."""
        if not self._start_time:
            self._start_time = asyncio.get_event_loop().time()
        return self._start_time
    
    def get_uptime(self) -> str:
        """Get bot uptime string."""
        if not self._start_time:
            return "Unknown"
        
        elapsed = asyncio.get_event_loop().time() - self._start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        
        return f"{hours}h {minutes}m {seconds}s"
    
    async def on_ready(self) -> None:
        """Handle bot ready event."""
        self._start_time = asyncio.get_event_loop().time()
        
        logger.info(
            f"Bot connected as {self.user}",
            user_id=self.user.id if self.user else 0,
            username=str(self.user) if self.user else "unknown",
            guilds=len(self.guilds),
        )
        print(f"[DISCORD] Connected as {self.user} (ID: {self.user.id})")
        print(f"[DISCORD] In {len(self.guilds)} guilds")
        
        # Sync slash commands
        try:
            print("[DISCORD] Syncing slash commands...")
            await self.tree.sync()
            logger.info("Slash commands synced globally")
            print("[DISCORD] Slash commands synced")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}", exc_info=True)
            print(f"[DISCORD] Failed to sync commands: {e}")
        
        # Set status
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/help for commands",
        )
        await self.change_presence(activity=activity)
        print("[DISCORD] Bot is now online and ready")
    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Handle bot joining a new guild."""
        logger.info(
            f"Joined guild",
            guild_id=guild.id,
            guild_name=guild.name,
        )
        
        # Initialize guild in database
        async with get_session_context() as session:
            memory_manager = MemoryManager(session)
            await memory_manager.get_or_create_guild(guild.id, guild.name)
    
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Handle bot leaving a guild."""
        logger.info(
            f"Left guild",
            guild_id=guild.id,
            guild_name=guild.name,
        )
    
    async def on_message(self, message: discord.Message) -> None:
        """Handle incoming messages.
        
        This is the main message handler that determines when
        the bot should respond to messages.
        """
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Ignore messages without content
        if not message.content:
            return
        
        # Check if bot is mentioned
        if self.user:
            is_mentioned = self._mention_pattern.search(message.content)
            if is_mentioned and str(self.user.id) in is_mentioned.group(0):
                await self.handle_mention(message)
                return
        
        # Check if "rosy" is mentioned naturally
        if self._name_pattern.search(message.content):
            await self.handle_name_mention(message)
            return
    
    async def handle_mention(self, message: discord.Message) -> None:
        """Handle when the bot is mentioned.
        
        Args:
            message: The Discord message.
        """
        if not self._ai_service:
            logger.error("AI service not initialized")
            return
        
        # Extract content without the mention
        content = self._mention_pattern.sub("", message.content).strip()
        
        if not content:
            # Just a mention, respond with help
            await message.channel.send(
                "Hi! I'm Rosy. Mention me with a question to chat! "
                "Use /help to see all available commands."
            )
            return
        
        # Get guild info
        guild_id = message.guild.id if message.guild else None
        channel_id = message.channel.id
        user_id = message.author.id
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        # Process the message
        async with get_session_context() as session:
            memory_manager = MemoryManager(session)
            
            # Get user
            await memory_manager.get_or_create_user(
                user_id,
                message.author.name,
                getattr(message.author, "global_name", None),
            )
            
            # Store user message
            conversation = await memory_manager.get_or_create_conversation(
                user_id=user_id,
                guild_id=guild_id,
                channel_id=channel_id,
                is_dm=is_dm,
            )
            
            await memory_manager.add_message(
                conversation_id=conversation.id,
                role="user",
                content=content,
                message_type="user",
                discord_message_id=message.id,
            )
            
            # Show typing indicator
            async with message.channel.typing():
                try:
                    response = await self._ai_service.chat(
                        user_id=user_id,
                        user_message=content,
                        guild_id=guild_id,
                        channel_id=channel_id,
                        is_dm=is_dm,
                        username=message.author.name,
                        guild_name=message.guild.name if message.guild else None,
                    )
                    
                    # Store bot response
                    await memory_manager.add_message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=response,
                        message_type="bot",
                    )
                    
                    # Send response (truncated if necessary)
                    max_length = 4000
                    for i in range(0, len(response), max_length):
                        await message.channel.send(response[i:i + max_length])
                        
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await message.channel.send(
                        "I'm sorry, I encountered an error processing your message. "
                        "Please try again later."
                    )
    
    async def handle_name_mention(self, message: discord.Message) -> None:
        """Handle when Rosy's name appears naturally in conversation.
        
        This allows Rosy to chime in when her name is mentioned in
        ongoing conversations, but only occasionally to avoid spam.
        
        Args:
            message: The Discord message.
        """
        # Don't respond to every mention, maybe 10% of the time
        # This creates a more natural feel
        import random
        if random.random() > 0.1:
            return
        
        # Don't respond if this is a DM (handled by mentions)
        if isinstance(message.channel, discord.DMChannel):
            return
        
        # Optionally respond with a brief acknowledgment
        # For now, we'll just log it
        logger.debug(
            f"Rosy's name mentioned in conversation",
            guild_id=message.guild.id if message.guild else None,
            channel_id=message.channel.id,
            user_id=message.author.id,
        )
    
    async def close(self) -> None:
        """Clean up and close the bot."""
        logger.info("Shutting down bot...")
        
        # Close providers
        await ProviderFactory.close_all()
        
        # Close database connections
        from database.session import close_db
        await close_db()
        
        await super().close()
