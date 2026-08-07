"""Admin slash commands for Rosy Bot.

This module provides commands for server administrators to configure
bot settings, AI providers, and models.
"""

from typing import Optional

import discord
from sqlalchemy import select, update

from bot.client import RosyBot
from config import settings
from database import Guild, GuildSetting, AIProvider, PersonalityPreference
from database.session import get_session_context
from memory import MemoryManager
from services.personality import PersonalityService
from utils.encryption import encrypt_key, decrypt_key
from utils.validation import is_admin, validate_model_name, validate_api_key
from utils.logging import get_logger

logger = get_logger(__name__)


async def check_admin(interaction: discord.Interaction) -> bool:
    """Check if the user has admin permissions.
    
    Args:
        interaction: Discord interaction.
        
    Returns:
        True if user is admin, False otherwise.
    """
    if not interaction.guild:
        await interaction.response.send_message(
            "This command can only be used in servers.",
            ephemeral=True,
        )
        return False
    
    member = interaction.guild.get_member(interaction.user.id)
    
    if not member:
        return False
    
    is_admin_user = await is_admin(
        interaction.user.id,
        interaction.guild.id,
        member,
    )
    
    if not is_admin_user:
        await interaction.response.send_message(
            "This command requires administrator permissions.",
            ephemeral=True,
        )
        return False
    
    return True


async def settings_command(
    bot: RosyBot,
    interaction: discord.Interaction,
    what: Optional[str] = None,
    value: Optional[str] = None,
) -> None:
    """Handle the /settings command.
    
    Args:
        bot: The RosyBot instance.
        interaction: Discord interaction.
        what: Setting to view/update.
        value: New value for the setting.
    """
    if not await check_admin(interaction):
        return
    
    guild_id = interaction.guild_id
    if not guild_id:
        return
    
    async with get_session_context() as session:
        memory_manager = MemoryManager(session)
        guild = await memory_manager.get_or_create_guild(guild_id, interaction.guild.name)
        
        if not what:
            # Show all settings
            embed = discord.Embed(
                title="⚙️ Bot Settings",
                description=f"Configure settings for **{interaction.guild.name}**",
                color=discord.Color.blue(),
            )
            
            # Get current settings
            result = await session.execute(
                select(GuildSetting).where(GuildSetting.guild_id == guild.id)
            )
            settings_list = result.scalars().all()
            
            if not settings_list:
                embed.add_field(
                    name="Current Settings",
                    value="No custom settings configured. Using defaults.",
                    inline=False,
                )
            else:
                settings_text = []
                for s in settings_list:
                    settings_text.append(f"**{s.key}**: `{s.value}`")
                embed.add_field(
                    name="Current Settings",
                    value="\n".join(settings_text),
                    inline=False,
                )
            
            embed.add_field(
                name="Configurable Settings",
                value=(
                    "• `response_length` - short, medium, long\n"
                    "• `humor_level` - 1-10\n"
                    "• `formality_level` - 1-10\n"
                    "• `personality` - friendly, professional, playful, supportive"
                ),
                inline=False,
            )
            
            embed.add_field(
                name="Usage",
                value="`/settings [setting] [value]`",
                inline=False,
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Handle setting a value
        what_lower = what.lower()
        
        if what_lower == "personality":
            if not value:
                await interaction.response.send_message(
                    "Please specify a personality type: friendly, professional, playful, supportive",
                    ephemeral=True,
                )
                return
            
            value_lower = value.lower()
            personality_service = PersonalityService()
            
            if value_lower not in personality_service.get_available_types():
                await interaction.response.send_message(
                    f"Unknown personality type: {value}. "
                    f"Available: {', '.join(personality_service.get_available_types())}",
                    ephemeral=True,
                )
                return
            
            success = await personality_service.set_guild_personality(
                guild_id, value_lower
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Personality Updated",
                    description=f"Personality set to **{value_lower}**",
                    color=discord.Color.green(),
                )
            else:
                embed = discord.Embed(
                    title="❌ Update Failed",
                    description="Failed to update personality settings.",
                    color=discord.Color.red(),
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Generic setting storage
        if not value:
            # Get current value
            result = await session.execute(
                select(GuildSetting).where(
                    GuildSetting.guild_id == guild.id,
                    GuildSetting.key == what_lower,
                )
            )
            setting = result.scalar_one_or_none()
            
            current_value = setting.value if setting else "not set"
            await interaction.response.send_message(
                f"Current value of `{what}`: `{current_value}`",
                ephemeral=True,
            )
            return
        
        # Set new value
        result = await session.execute(
            select(GuildSetting).where(
                GuildSetting.guild_id == guild.id,
                GuildSetting.key == what_lower,
            )
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
        else:
            setting = GuildSetting(
                guild_id=guild.id,
                key=what_lower,
                value=value,
            )
            session.add(setting)
        
        embed = discord.Embed(
            title="✅ Setting Updated",
            description=f"**{what}** set to `{value}`",
            color=discord.Color.green(),
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    logger.info(
        f"Settings updated: {what} = {value}",
        guild_id=guild_id,
        user_id=interaction.user.id,
    )


async def provider_command(
    bot: RosyBot,
    interaction: discord.Interaction,
    action: str = "status",
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> None:
    """Handle the /provider command.
    
    Args:
        bot: The RosyBot instance.
        interaction: Discord interaction.
        action: Action to perform (status, set, reset).
        provider_name: Provider name.
        api_key: API key for the provider.
    """
    if not await check_admin(interaction):
        return
    
    guild_id = interaction.guild_id
    if not guild_id:
        return
    
    action_lower = action.lower()
    
    if action_lower == "status":
        embed = discord.Embed(
            title="🔧 AI Provider Status",
            description="Current AI provider configuration",
            color=discord.Color.blue(),
        )
        
        embed.add_field(
            name="Default Provider",
            value="**OpenRouter** (using global API key)",
            inline=False,
        )
        
        embed.add_field(
            name="Configuration",
            value=(
                f"• Model: `{settings.openrouter_default_model}`\n"
                f"• Status: Using global settings"
            ),
            inline=False,
        )
        
        embed.add_field(
            name="Usage",
            value=(
                "`/provider status` - Show current status\n"
                "`/provider set [provider] [key]` - Set custom provider\n"
                "`/provider reset` - Reset to defaults"
            ),
            inline=False,
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if action_lower == "reset":
        async with get_session_context() as session:
            memory_manager = MemoryManager(session)
            guild = await memory_manager.get_or_create_guild(
                guild_id, interaction.guild.name
            )
            
            if guild.provider:
                guild.provider.delete()
            
        embed = discord.Embed(
            title="✅ Provider Reset",
            description="Using default OpenRouter configuration",
            color=discord.Color.green(),
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if action_lower == "set":
        if not provider_name:
            await interaction.response.send_message(
                "Please specify a provider name: openrouter, openai, anthropic, etc.",
                ephemeral=True,
            )
            return
        
        if not api_key:
            await interaction.response.send_message(
                "Please provide an API key with the `key` parameter.",
                ephemeral=True,
            )
            return
        
        if not validate_api_key(api_key):
            await interaction.response.send_message(
                "Invalid API key format. Please check and try again.",
                ephemeral=True,
            )
            return
        
        # Store the API key securely
        encrypted_key = encrypt_key(api_key)
        
        async with get_session_context() as session:
            memory_manager = MemoryManager(session)
            guild = await memory_manager.get_or_create_guild(
                guild_id, interaction.guild.name
            )
            
            # Create or update provider
            if guild.provider:
                guild.provider.provider_name = provider_name.lower()
                guild.provider.api_endpoint = None
            else:
                provider = AIProvider(
                    guild_id=guild.id,
                    provider_name=provider_name.lower(),
                    model="auto",
                    is_default=False,
                )
                session.add(provider)
            
            # Store encrypted API key
            from database import APIKey as APIKeyModel
            
            # Remove old key for this provider
            result = await session.execute(
                select(APIKeyModel).where(
                    APIKeyModel.guild_id == guild.id,
                    APIKeyModel.provider_name == provider_name.lower(),
                )
            )
            old_key = result.scalar_one_or_none()
            if old_key:
                await session.delete(old_key)
            
            # Add new key
            api_key_model = APIKeyModel(
                guild_id=guild.id,
                provider_name=provider_name.lower(),
                encrypted_key=encrypted_key,
                key_name=f"{provider_name}_custom",
                is_active=True,
            )
            session.add(api_key_model)
        
        embed = discord.Embed(
            title="✅ Provider Configured",
            description=f"Custom {provider_name} provider configured successfully",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Note",
            value="Your API key has been securely stored and encrypted.",
            inline=False,
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        logger.info(
            f"Provider configured: {provider_name}",
            guild_id=guild_id,
            user_id=interaction.user.id,
        )
        return
    
    await interaction.response.send_message(
        f"Unknown action: {action}. Use status, set, or reset.",
        ephemeral=True,
    )


async def model_command(
    bot: RosyBot,
    interaction: discord.Interaction,
    action: str = "status",
    model_name: Optional[str] = None,
) -> None:
    """Handle the /model command.
    
    Args:
        bot: The RosyBot instance.
        interaction: Discord interaction.
        action: Action to perform (status, set, list).
        model_name: Model name to set.
    """
    if not await check_admin(interaction):
        return
    
    guild_id = interaction.guild_id
    if not guild_id:
        return
    
    action_lower = action.lower()
    
    if action_lower == "status":
        embed = discord.Embed(
            title="🤖 AI Model Status",
            description="Current AI model configuration",
            color=discord.Color.blue(),
        )
        
        embed.add_field(
            name="Current Model",
            value=f"`{settings.openrouter_default_model}`",
            inline=False,
        )
        
        embed.add_field(
            name="Model Info",
            value=(
                "• Provider: OpenRouter (free routing)\n"
                "• Uses 'auto' routing to find available models"
            ),
            inline=False,
        )
        
        embed.add_field(
            name="Popular Models",
            value=(
                "• `openrouter/auto` - Free routing (recommended)\n"
                "• `openai/gpt-4` - GPT-4\n"
                "• `anthropic/claude-3` - Claude 3\n"
                "• `google/gemini-pro` - Gemini Pro"
            ),
            inline=False,
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if action_lower == "list":
        embed = discord.Embed(
            title="📋 Available Models",
            description="Popular models available through OpenRouter",
            color=discord.Color.blue(),
        )
        
        models = [
            ("openrouter/auto", "Free routing - finds best available model"),
            ("openai/gpt-4-turbo", "GPT-4 Turbo - powerful and fast"),
            ("openai/gpt-3.5-turbo", "GPT-3.5 Turbo - fast and affordable"),
            ("anthropic/claude-3-opus", "Claude 3 Opus - most capable"),
            ("anthropic/claude-3-sonnet", "Claude 3 Sonnet - balanced"),
            ("google/gemini-pro", "Gemini Pro - Google's model"),
            ("meta-llama/llama-3-70b-instruct", "Llama 3 70B - open source"),
        ]
        
        for model, desc in models:
            embed.add_field(name=model, value=desc, inline=False)
        
        embed.set_footer(text="Use /model set [name] to change the model")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if action_lower == "set":
        if not model_name:
            await interaction.response.send_message(
                "Please specify a model name.",
                ephemeral=True,
            )
            return
        
        if not validate_model_name(model_name):
            await interaction.response.send_message(
                "Invalid model name format.",
                ephemeral=True,
            )
            return
        
        async with get_session_context() as session:
            memory_manager = MemoryManager(session)
            guild = await memory_manager.get_or_create_guild(
                guild_id, interaction.guild.name
            )
            
            # Update or create provider with new model
            if guild.provider:
                guild.provider.model = model_name
            else:
                provider = AIProvider(
                    guild_id=guild.id,
                    provider_name="openrouter",
                    model=model_name,
                    is_default=False,
                )
                session.add(provider)
        
        embed = discord.Embed(
            title="✅ Model Updated",
            description=f"Model set to `{model_name}`",
            color=discord.Color.green(),
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        logger.info(
            f"Model updated: {model_name}",
            guild_id=guild_id,
            user_id=interaction.user.id,
        )
        return
    
    await interaction.response.send_message(
        f"Unknown action: {action}. Use status, set, or list.",
        ephemeral=True,
    )
