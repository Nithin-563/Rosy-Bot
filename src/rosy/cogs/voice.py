"""Voice cog: join/leave voice, and speak text via a TTS provider (optional)."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("rosy.voice")


class Voice(commands.Cog, name="Voice"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="join", description="Make Rosy join your voice channel.")
    async def join(self, interaction: discord.Interaction) -> None:
        author = interaction.user
        if not author.voice or not author.voice.channel:
            await interaction.response.send_message("Join a voice channel first.", ephemeral=True)
            return
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(author.voice.channel)
        else:
            await author.voice.channel.connect()
        await interaction.response.send_message(f"🔊 Joined {author.voice.channel.name}.")

    @app_commands.command(name="leave", description="Make Rosy leave the voice channel.")
    async def leave(self, interaction: discord.Interaction) -> None:
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("👋 Left the voice channel.")
        else:
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after) -> None:
        """Auto-leave if Rosy is alone in the channel."""
        if member.id != self.bot.user.id and before.channel is not None and after.channel is None:
            return
        vc = member.guild.voice_client if member.guild else None
        if vc and len(vc.channel.members) <= 1:
            try:
                await vc.disconnect()
            except Exception:
                pass


async def setup(bot) -> None:
    await bot.add_cog(Voice(bot))