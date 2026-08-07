"""Discord event handlers.

This module provides event handlers for various Discord events
including errors, typing indicators, and member updates.
"""

from typing import Any

import discord
from discord.ext import commands

from bot.client import RosyBot
from utils.logging import get_logger

logger = get_logger(__name__)


def setup_events(bot: RosyBot) -> None:
    """Set up event handlers for the bot.
    
    Args:
        bot: The RosyBot instance.
    """
    
    @bot.event
    async def on_error(event_method: str, *args: Any, **kwargs: Any) -> None:
        """Handle Discord errors.
        
        Args:
            event_method: The method that raised the error.
            *args: Positional arguments from the event.
            **kwargs: Keyword arguments from the event.
        """
        logger.error(
            f"Discord event error in {event_method}",
            event=event_method,
            args=str(args)[:500],
        )
    
    @bot.event
    async def on_command_error(
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        """Handle command errors.
        
        Args:
            ctx: The command context.
            error: The error that was raised.
        """
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "You don't have permission to use this command.",
                delete_after=10,
            )
            return
        
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                f"Invalid argument: {error}",
                delete_after=10,
            )
            return
        
        logger.error(
            f"Command error: {error}",
            command=ctx.command.name if ctx.command else "unknown",
            user_id=ctx.author.id,
            guild_id=ctx.guild.id if ctx.guild else None,
        )
        
        await ctx.send(
            "An error occurred while processing your command.",
            delete_after=10,
        )
    
    @bot.event
    async def on_typing(
        channel: discord.abc.Messageable,
        user: discord.abc.User,
        _when: float,
    ) -> None:
        """Handle typing indicators.
        
        Args:
            channel: The channel where typing is occurring.
            user: The user who is typing.
            _when: When the typing started.
        """
        # Ignore typing from bots
        if user.bot:
            return
        
        logger.debug(
            f"User typing",
            user_id=user.id,
            channel_id=channel.id if hasattr(channel, "id") else None,
        )
    
    @bot.event
    async def on_member_join(member: discord.Member) -> None:
        """Handle new member joining.
        
        Args:
            member: The member who joined.
        """
        logger.info(
            f"Member joined",
            user_id=member.id,
            guild_id=member.guild.id,
            guild_name=member.guild.name,
        )
    
    @bot.event
    async def on_member_remove(member: discord.Member) -> None:
        """Handle member leaving.
        
        Args:
            member: The member who left.
        """
        logger.info(
            f"Member left",
            user_id=member.id,
            guild_id=member.guild.id,
            guild_name=member.guild.name,
        )
    
    @bot.event
    async def on_message_delete(message: discord.Message) -> None:
        """Handle message deletion.
        
        Args:
            message: The deleted message.
        """
        if message.author.bot:
            return
        
        logger.debug(
            f"Message deleted",
            user_id=message.author.id,
            guild_id=message.guild.id if message.guild else None,
            channel_id=message.channel.id,
        )
    
    @bot.event
    async def on_message_edit(
        before: discord.Message,
        after: discord.Message,
    ) -> None:
        """Handle message edits.
        
        Args:
            before: The message before edit.
            after: The message after edit.
        """
        if before.author.bot:
            return
        
        # Log significant edits
        if before.content != after.content:
            logger.debug(
                f"Message edited",
                user_id=before.author.id,
                guild_id=before.guild.id if before.guild else None,
                channel_id=before.channel.id,
            )
    
    @bot.event
    async def on_reaction_add(
        reaction: discord.Reaction,
        user: discord.abc.User,
    ) -> None:
        """Handle reactions being added.
        
        Args:
            reaction: The reaction that was added.
            user: The user who added the reaction.
        """
        if user.bot:
            return
        
        logger.debug(
            f"Reaction added",
            user_id=user.id,
            message_id=reaction.message.id,
            emoji=str(reaction.emoji),
        )
    
    @bot.event
    async def on_disconnect() -> None:
        """Handle disconnection from Discord."""
        logger.warning("Disconnected from Discord")
    
    @bot.event
    async def on_resumed() -> None:
        """Handle reconnection to Discord."""
        logger.info("Reconnected to Discord")
    
    @bot.event
    async def on_shard_disconnect(shard_id: int) -> None:
        """Handle a shard disconnecting.
        
        Args:
            shard_id: The ID of the shard that disconnected.
        """
        logger.warning(f"Shard {shard_id} disconnected")
    
    @bot.event
    async def on_shard_resumed(shard_id: int) -> None:
        """Handle a shard reconnecting.
        
        Args:
            shard_id: The ID of the shard that reconnected.
        """
        logger.info(f"Shard {shard_id} reconnected")
