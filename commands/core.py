"""Core slash commands for Rosy Bot.

This module provides basic utility commands like ping, help, and about.
"""

from typing import Optional

import discord

from bot.client import RosyBot
from utils.logging import get_logger

logger = get_logger(__name__)


async def ping_command(bot: RosyBot, interaction: discord.Interaction) -> None:
    """Handle the /ping command.
    
    Args:
        bot: The RosyBot instance.
        interaction: Discord interaction.
    """
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="Pong! 🏓",
        description=f"Latency: **{latency}ms**",
        color=discord.Color.green(),
    )
    
    await interaction.response.send_message(embed=embed)
    
    logger.debug(
        "Ping command executed",
        user_id=interaction.user.id,
        guild_id=interaction.guild_id,
        latency=latency,
    )


async def help_command(
    bot: RosyBot,
    interaction: discord.Interaction,
    command: Optional[str] = None,
) -> None:
    """Handle the /help command.
    
    Args:
        bot: The RosyBot instance.
        interaction: Discord interaction.
        command: Optional specific command to get help for.
    """
    if command:
        await send_command_help(bot, interaction, command)
        return
    
    # General help
    embed = discord.Embed(
        title="Rosy Bot - Help",
        description="I'm Rosy, a friendly AI assistant! Here's how you can interact with me:",
        color=discord.Color.blue(),
    )
    
    # Commands section
    embed.add_field(
        name="📌 Basic Commands",
        value=(
            "**/ping** - Check if I'm responding\n"
            "**/help** - Show this help message\n"
            "**/about** - Learn more about me"
        ),
        inline=False,
    )
    
    embed.add_field(
        name="💭 Conversation",
        value=(
            "**/memory** - View your stored memories\n"
            "**/clear_memory** - Clear your history or memories"
        ),
        inline=False,
    )
    
    # Admin commands (only show if user is admin)
    if interaction.guild:
        member = interaction.guild.get_member(interaction.user.id)
        if member and (member.guild_permissions.administrator or member.guild_permissions.manage_guild):
            embed.add_field(
                name="⚙️ Admin Commands",
                value=(
                    "**/settings** - Configure bot settings\n"
                    "**/provider** - Manage AI provider\n"
                    "**/model** - Set AI model"
                ),
                inline=False,
            )
    
    # How to chat
    embed.add_field(
        name="💬 Chatting with Me",
        value=(
            "• **Mention me** (@Rosy) followed by your question\n"
            "• My name is 'Rosy' - I'll occasionally chime in when mentioned naturally\n"
            "• Use `/` to see all available commands"
        ),
        inline=False,
    )
    
    embed.set_footer(text="Need more help? Contact your server admin or bot owner.")
    
    await interaction.response.send_message(embed=embed)
    
    logger.debug(
        "Help command executed",
        user_id=interaction.user.id,
        guild_id=interaction.guild_id,
    )


async def send_command_help(
    bot: RosyBot,
    interaction: discord.Interaction,
    command: str,
) -> None:
    """Send detailed help for a specific command.
    
    Args:
        bot: The RosyBot instance.
        interaction: Discord interaction.
        command: Command name to get help for.
    """
    command_helps = {
        "ping": {
            "title": "/ping",
            "description": "Check if the bot is responding and see the latency.",
            "usage": "/ping",
        },
        "help": {
            "title": "/help",
            "description": "Get help with using the bot.",
            "usage": "/help [command]",
            "options": "**command** (optional): Get help for a specific command",
        },
        "about": {
            "title": "/about",
            "description": "Learn about Rosy and what she can do.",
            "usage": "/about",
        },
        "memory": {
            "title": "/memory",
            "description": "View your stored memories and information I've learned about you.",
            "usage": "/memory [type]",
            "options": "**type** (optional): Filter by memory type (fact, preference, etc.)",
        },
        "clear_memory": {
            "title": "/clear_memory",
            "description": "Clear your conversation history or stored memories.",
            "usage": "/clear_memory <what>",
            "options": "**what**: What to clear - 'history' or 'memories'",
        },
        "settings": {
            "title": "/settings",
            "description": "View or update bot settings (admin only).",
            "usage": "/settings [what] [value]",
            "options": (
                "**what** (optional): Setting to view/update\n"
                "**value** (optional): New value for the setting"
            ),
        },
        "provider": {
            "title": "/provider",
            "description": "Configure AI provider settings (admin only).",
            "usage": "/provider [action] [provider] [key]",
            "options": (
                "**action**: 'status', 'set', or 'reset'\n"
                "**provider** (optional): Provider name\n"
                "**key** (optional): API key (for 'set' action)"
            ),
        },
        "model": {
            "title": "/model",
            "description": "Configure AI model settings (admin only).",
            "usage": "/model [action] [name]",
            "options": (
                "**action**: 'status', 'set', or 'list'\n"
                "**name** (optional): Model name"
            ),
        },
    }
    
    command_lower = command.lower()
    
    if command_lower not in command_helps:
        await interaction.response.send_message(
            f"I don't have help for '{command}'. Use /help to see all commands.",
            ephemeral=True,
        )
        return
    
    help_info = command_helps[command_lower]
    
    embed = discord.Embed(
        title=help_info["title"],
        description=help_info["description"],
        color=discord.Color.blue(),
    )
    
    embed.add_field(
        name="Usage",
        value=f"```{help_info['usage']}```",
        inline=False,
    )
    
    if "options" in help_info:
        embed.add_field(
            name="Options",
            value=help_info["options"],
            inline=False,
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def about_command(bot: RosyBot, interaction: discord.Interaction) -> None:
    """Handle the /about command.
    
    Args:
        bot: The RosyBot instance.
        interaction: Discord interaction.
    """
    embed = discord.Embed(
        title="About Rosy 🌹",
        description=(
            "Hello! I'm **Rosy**, an AI-powered Discord bot designed to be "
            "your friendly and helpful assistant in any server."
        ),
        color=discord.Color.magenta(),
    )
    
    embed.add_field(
        name="What I Can Do",
        value=(
            "• Chat with you about various topics\n"
            "• Remember information about you and your server\n"
            "• Help with questions and tasks\n"
            "• Provide information and explanations\n"
            "• And much more!"
        ),
        inline=False,
    )
    
    embed.add_field(
        name="My Features",
        value=(
            "• **Multi-server support** - I adapt to each server's settings\n"
            "• **Persistent memory** - I remember important things\n"
            "• **Flexible AI** - I can connect to various AI providers\n"
            "• **Admin controls** - Server admins can configure me"
        ),
        inline=False,
    )
    
    embed.add_field(
        name="How to Use",
        value=(
            "• Mention me (@Rosy) in any message to chat\n"
            "• Use `/` followed by commands for specific actions\n"
            "• Type `/help` for a list of all commands"
        ),
        inline=False,
    )
    
    # Add bot stats
    uptime = bot.get_uptime()
    embed.add_field(
        name="Stats",
        value=(
            f"• Servers: {len(bot.guilds)}\n"
            f"• Uptime: {uptime}"
        ),
        inline=False,
    )
    
    embed.set_footer(text="Made with ❤️ using Discord.py and Python")
    
    await interaction.response.send_message(embed=embed)
    
    logger.debug(
        "About command executed",
        user_id=interaction.user.id,
        guild_id=interaction.guild_id,
    )
