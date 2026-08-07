"""Memory-related slash commands for Rosy Bot.

This module provides commands for viewing and managing memories
and conversation history.
"""

from typing import Optional

import discord

from bot.client import RosyBot
from database.session import get_session_context
from memory import MemoryManager
from utils.logging import get_logger

logger = get_logger(__name__)


async def memory_command(
    bot: RosyBot,
    interaction: discord.Interaction,
    memory_type: Optional[str] = None,
) -> None:
    """Handle the /memory command.
    
    Args:
        bot: The RosyBot instance.
        interaction: Discord interaction.
        memory_type: Optional filter for memory type.
    """
    user_id = interaction.user.id
    guild_id = interaction.guild_id
    
    async with get_session_context() as session:
        memory_manager = MemoryManager(session)
        
        # Get user
        user = await memory_manager.get_or_create_user(
            user_id,
            interaction.user.name,
            getattr(interaction.user, "global_name", None),
        )
        
        # Get memories
        memories = await memory_manager.get_memories(
            user_id=user_id,
            guild_id=guild_id,
            memory_type=memory_type,
            limit=20,
        )
        
        if not memories:
            embed = discord.Embed(
                title="📝 Your Memories",
                description=(
                    "You don't have any memories stored yet. "
                    "I'll remember important things about you as we chat!"
                ),
                color=discord.Color.orange(),
            )
            
            if memory_type:
                embed.description = (
                    f"No {memory_type} memories found. "
                    "I'll remember things as we talk!"
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Group memories by type
        by_type: dict[str, list] = {}
        for mem in memories:
            if mem.memory_type not in by_type:
                by_type[mem.memory_type] = []
            by_type[mem.memory_type].append(mem)
        
        embed = discord.Embed(
            title="📝 Your Memories",
            description=f"Found {len(memories)} memories",
            color=discord.Color.blue(),
        )
        
        for mem_type, mems in by_type.items():
            value_lines = []
            for mem in mems[:5]:  # Show max 5 per type
                importance_bar = "⭐" * min(mem.importance, 5)
                value_lines.append(
                    f"**{mem.key}** {importance_bar}\n"
                    f"└ {mem.content[:100]}{'...' if len(mem.content) > 100 else ''}"
                )
            
            if len(mems) > 5:
                value_lines.append(f"_...and {len(mems) - 5} more {mem_type}_")
            
            embed.add_field(
                name=f"Type: {mem_type.title()}",
                value="\n".join(value_lines),
                inline=False,
            )
        
        embed.set_footer(text="Memories help me provide better responses!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    logger.debug(
        "Memory command executed",
        user_id=user_id,
        guild_id=guild_id,
        memory_count=len(memories),
    )


async def clear_memory_command(
    bot: RosyBot,
    interaction: discord.Interaction,
    what: str = "history",
) -> None:
    """Handle the /clear_memory command.
    
    Args:
        bot: The RosyBot instance.
        interaction: Discord interaction.
        what: What to clear ('history' or 'memories').
    """
    user_id = interaction.user.id
    guild_id = interaction.guild_id
    
    # Validate input
    what_lower = what.lower()
    if what_lower not in ("history", "memories"):
        await interaction.response.send_message(
            "Please specify what to clear: `history` or `memories`",
            ephemeral=True,
        )
        return
    
    # Create confirmation view
    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.value = None
        
        @discord.ui.button(label="Yes, Clear", style=discord.ButtonStyle.danger)
        async def confirm(
            self,
            button: discord.ui.Button,
            ctx: discord.Interaction,
        ) -> None:
            self.value = True
            await ctx.response.defer()
            self.stop()
        
        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
        async def cancel(
            self,
            button: discord.ui.Button,
            ctx: discord.Interaction,
        ) -> None:
            self.value = False
            await ctx.response.send_message("Operation cancelled.", ephemeral=True)
            self.stop()
    
    view = ConfirmView()
    
    await interaction.response.send_message(
        f"Are you sure you want to clear your **{what_lower}**? This action cannot be undone.",
        view=view,
        ephemeral=True,
    )
    
    await view.wait()
    
    if not view.value:
        return
    
    # Perform the clear operation
    async with get_session_context() as session:
        memory_manager = MemoryManager(session)
        
        if what_lower == "history":
            # Get or create conversation
            conversation = await memory_manager.get_or_create_conversation(
                user_id=user_id,
                guild_id=guild_id,
                channel_id=interaction.channel_id,
                is_dm=isinstance(interaction.channel, discord.DMChannel),
            )
            
            deleted_count = await memory_manager.clear_conversation_history(
                conversation.id
            )
            
            embed = discord.Embed(
                title="✅ History Cleared",
                description=f"Deleted {deleted_count} messages from your conversation history.",
                color=discord.Color.green(),
            )
            
        else:  # memories
            deleted_count = await memory_manager.clear_all_memories(
                user_id=user_id,
                guild_id=guild_id,
            )
            
            embed = discord.Embed(
                title="✅ Memories Cleared",
                description=f"Deleted {deleted_count} memories.",
                color=discord.Color.green(),
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    logger.info(
        f"Clear memory command executed: {what_lower}",
        user_id=user_id,
        guild_id=guild_id,
        deleted_count=deleted_count,
    )


def isinstance(obj, cls) -> bool:
    """Simple isinstance helper for type checking."""
    return isinstance(obj, cls)
