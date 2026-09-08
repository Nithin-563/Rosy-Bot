"""Voice join/leave and optional AI TTS voice-chat."""
from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from rosy.core.errors import safe_user_message

logger = logging.getLogger("rosy.voice")


class Voice(commands.Cog, name="Voice"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self._speaking_tasks: dict[int, asyncio.Task] = {}

    async def _tts(self, text: str, voice: str) -> Path:
        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError("Voice TTS is not installed. Deploy with the `voice` extra.") from exc
        fd, raw = tempfile.mkstemp(suffix=".mp3", prefix="rosy-tts-")
        import os
        os.close(fd)
        path = Path(raw)
        communicate = edge_tts.Communicate(text[:3000], voice=voice)
        await communicate.save(str(path))
        return path

    async def _speak(self, guild: discord.Guild, text: str) -> None:
        vc = guild.voice_client
        if vc is None:
            raise RuntimeError("Rosy is not in a voice channel.")
        if not self.bot.settings.tts_enabled:
            raise RuntimeError("TTS is disabled by the deployment settings. Set `ROS_TTS_ENABLED=true`.")
        path = await self._tts(text, self.bot.settings.tts_voice)
        source = discord.FFmpegPCMAudio(str(path), executable=self.bot.settings.ffmpeg_path)
        previous = self._speaking_tasks.get(guild.id)
        if previous and not previous.done():
            previous.cancel()
        done = asyncio.get_running_loop().create_future()
        def after(error):
            try:
                path.unlink(missing_ok=True)
            finally:
                if not done.done():
                    done.set_result(error)
        vc.play(source, after=after)
        await done
        error = done.result()
        if error:
            raise RuntimeError("Voice playback failed.") from error

    @app_commands.command(name="join", description="Make Rosy join your voice channel.")
    async def join(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        author = interaction.user
        if not author.voice or not author.voice.channel:
            await interaction.followup.send("Join a voice channel first.", ephemeral=True)
            return
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(author.voice.channel)
        else:
            await author.voice.channel.connect()
        await interaction.followup.send(f"🔊 Joined {author.voice.channel.name}.")

    @app_commands.command(name="leave", description="Make Rosy leave the voice channel.")
    async def leave(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.followup.send("👋 Left the voice channel.")
        else:
            await interaction.followup.send("I'm not in a voice channel.", ephemeral=True)

    @app_commands.command(name="speak", description="Speak text aloud in Rosy's current voice channel.")
    async def speak(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self._speak(interaction.guild, text)
            await interaction.followup.send("🔊 Spoken.", ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)

    @app_commands.command(name="voice_chat", description="Ask Rosy a question and have her answer aloud.")
    async def voice_chat(self, interaction: discord.Interaction, prompt: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            result = await self.bot.conversation.generate(user_text=prompt, user_id=interaction.user.id, guild_id=interaction.guild_id, channel_id=interaction.channel_id, user_name=interaction.user.display_name)
            await self._speak(interaction.guild, result.text)
            await interaction.followup.send(f"🗣️ {result.text[:1800]}", ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)

    @app_commands.command(name="stop_speaking", description="Stop current voice playback.")
    async def stop_speaking(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.followup.send("⏹️ Stopped speaking.", ephemeral=True)
        else:
            await interaction.followup.send("Nothing is playing.", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after) -> None:
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
