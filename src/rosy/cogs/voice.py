"""Voice cog: join/leave voice, and speak text via a TTS provider (optional)."""

from __future__ import annotations

import io
import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("rosy.voice")


def _load_tts():
    """Return an async TTS callable if edge-tts is installed, else None."""
    try:
        import edge_tts

        async def _speak(text: str, voice: str = "en-US-JennyNeural") -> bytes:
            communicate = edge_tts.Communicate(text, voice)
            buf = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.write(chunk["data"])
            return buf.getvalue()

        return _speak
    except Exception:  # pragma: no cover - feature-flag
        return None


class Voice(commands.Cog, name="Voice"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.tts = _load_tts()
        self.auto_speak = False
        self._queue: list[str] = []

    async def speak(self, text: str) -> None:
        """Play text aloud in the guild's voice channel if connected."""
        if self.tts is None:
            return
        for guild in self.bot.guilds:
            if guild.voice_client:
                await self._play(guild.voice_client, text)
                break

    async def _play(self, vc, text: str) -> None:
        try:
            audio = await self.tts(text[:300])
            if not audio:
                return
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio)
                path = f.name
            source = discord.FFmpegPCMAudio(path)
            if not vc.is_playing():
                vc.play(source, after=lambda e: None)
        except Exception as exc:  # pragma: no cover
            logger.warning("TTS playback failed: %s", exc)

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

    @app_commands.command(name="say", description="Make Rosy speak text aloud in the voice channel.")
    async def say(self, interaction: discord.Interaction, text: str) -> None:
        if self.tts is None:
            await interaction.response.send_message(
                "Voice speech isn't enabled on this deployment (needs the `voice` extra / edge-tts).",
                ephemeral=True,
            )
            return
        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            await interaction.response.send_message("I need to be in a voice channel first. Use `/join`.", ephemeral=True)
            return
        await interaction.response.defer()
        await self._play(vc, text)
        await interaction.followup.send("🔊 Speaking...")

    @app_commands.command(name="voice", description="Toggle Rosy speaking replies aloud in voice.")
    async def voice_toggle(self, interaction: discord.Interaction, enabled: bool) -> None:
        self.auto_speak = enabled
        await interaction.response.send_message(
            f"🗣️ Auto-speak {'enabled' if enabled else 'disabled'}.",
            ephemeral=True,
        )

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