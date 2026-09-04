"""Admin cog: per-guild configuration through Discord (requires manage_guild)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from rosy.conversation.personality import PERSONALITIES


def admin_only():
    return app_commands.default_permissions(manage_guild=True)


class Admin(commands.Cog, name="Admin"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="config", description="Show Rose's configuration for this server.")
    @app_commands.default_permissions(manage_guild=True)
    async def config(self, interaction: discord.Interaction) -> None:
        gs = await self.bot.guild_settings.get_settings(interaction.guild_id)
        embed = discord.Embed(title="Server configuration", color=discord.Color.blurple())
        embed.add_field(name="AI provider", value=gs.ai_provider or "default")
        embed.add_field(name="AI model", value=gs.ai_model or "default")
        embed.add_field(name="Personality", value=gs.personality_mode)
        embed.add_field(name="Autonomous replies", value="on" if gs.autonomous_enabled else "off")
        embed.add_field(name="Memory", value="on" if gs.memory_enabled else "off")
        embed.add_field(name="Prefix", value=gs.prefix or "none")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="set_provider", description="Set the AI provider for this server.")
    @app_commands.default_permissions(manage_guild=True)
    async def set_provider(self, interaction: discord.Interaction, provider: str) -> None:
        known = self.bot.ai.registry.known()
        if provider not in known:
            await interaction.response.send_message(
                f"Unknown provider. Known: {', '.join(known)}", ephemeral=True
            )
            return
        await self.bot.guild_settings.update_settings(interaction.guild_id, ai_provider=provider)
        await interaction.response.send_message(f"AI provider set to **{provider}**.", ephemeral=True)

    @app_commands.command(name="set_model", description="Set the AI model for this server.")
    @app_commands.default_permissions(manage_guild=True)
    async def set_model(self, interaction: discord.Interaction, model: str) -> None:
        await self.bot.guild_settings.update_settings(interaction.guild_id, ai_model=model)
        await interaction.response.send_message(f"AI model set to **{model}**.", ephemeral=True)

    @app_commands.command(name="set_personality", description="Set Rose's personality mode.")
    @app_commands.default_permissions(manage_guild=True)
    async def set_personality(self, interaction: discord.Interaction, mode: str) -> None:
        if mode not in PERSONALITIES:
            await interaction.response.send_message(
                f"Unknown mode. Options: {', '.join(sorted(PERSONALITIES))}", ephemeral=True
            )
            return
        await self.bot.guild_settings.update_settings(interaction.guild_id, personality_mode=mode)
        await interaction.response.send_message(f"Personality set to **{mode}**.", ephemeral=True)

    @app_commands.command(name="set_autonomous", description="Enable/disable autonomous replies.")
    @app_commands.default_permissions(manage_guild=True)
    async def set_autonomous(self, interaction: discord.Interaction, enabled: bool) -> None:
        await self.bot.guild_settings.update_settings(interaction.guild_id, autonomous_enabled=enabled)
        await interaction.response.send_message(
            f"Autonomous replies {'enabled' if enabled else 'disabled'}.", ephemeral=True
        )


async def setup(bot) -> None:
    await bot.add_cog(Admin(bot))