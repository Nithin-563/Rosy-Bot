"""Music cog: play audio via yt-dlp + ffmpeg into a voice channel.

Gracefully disabled if yt-dlp/ffmpeg are unavailable (keeps the bot functional
on minimal deployments).
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("rosy.music")


class Music(commands.Cog, name="Music"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.queue: dict[int, list[str]] = {}
        self._volume: dict[int, float] = {}
        self._loop: dict[int, bool] = {}
        self._current: dict[int, str] = {}

    def _ytdl_available(self) -> bool:
        try:
            import yt_dlp  # noqa: F401

            return True
        except ImportError:
            return False

    @app_commands.command(name="play", description="Play a song/URL in your voice channel.")
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        if not self._ytdl_available():
            await interaction.response.send_message(
                "Music is not installed on this deployment (missing `yt-dlp`). Chat, games, and tools still work.",
                ephemeral=True,
            )
            return
        author = interaction.user
        if not author.voice or not author.voice.channel:
            await interaction.response.send_message("Join a voice channel first.", ephemeral=True)
            return
        vc = interaction.guild.voice_client
        if vc is None:
            vc = await author.voice.channel.connect()
        self.queue.setdefault(interaction.guild_id, []).append(query)
        await interaction.response.send_message(f"🔎 Added **{query}** to the queue.")
        if not vc.is_playing():
            await self._play_next(interaction.guild_id, interaction.channel)

    async def _play_next(self, guild_id: int, channel) -> None:
        vc = self.bot.get_guild(guild_id).voice_client
        if vc is None or not self.queue.get(guild_id):
            return
        query = self.queue[guild_id].pop(0)
        self._current[guild_id] = query
        url = await self._get_url(query)
        if url is None:
            await channel.send("Couldn't find that track.")
            await self._play_next(guild_id, channel)
            return
        vc.play(discord.FFmpegPCMAudio(url, executable=self.bot.settings.ffmpeg_path))
        vc.source = discord.PCMVolumeTransformer(vc.source, volume=self._volume.get(guild_id, 1.0))
        await channel.send(f"▶️ Now playing: **{query}**")

    async def _get_url(self, query: str) -> str | None:
        try:
            import yt_dlp

            opts = {"format": "bestaudio/best", "quiet": True, "noplaylist": True, "youtube_metadata": False}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(query, download=False)
                return info.get("url")
        except Exception as exc:
            logger.warning("yt-dlp error: %s", exc)
            return None

    @app_commands.command(name="skip", description="Skip the current track.")
    async def skip(self, interaction: discord.Interaction) -> None:
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭ Skipped.")
        else:
            await interaction.response.send_message("Nothing playing.", ephemeral=True)

    @app_commands.command(name="stop", description="Stop playback and clear the queue.")
    async def stop(self, interaction: discord.Interaction) -> None:
        self.queue.pop(interaction.guild_id, None)
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
        await interaction.response.send_message("🛑 Stopped and cleared queue.")

    @app_commands.command(name="pause", description="Pause playback.")
    async def pause(self, interaction: discord.Interaction) -> None:
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ Paused.")
        else:
            await interaction.response.send_message("Nothing playing.", ephemeral=True)

    @app_commands.command(name="resume", description="Resume playback.")
    async def resume(self, interaction: discord.Interaction) -> None:
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Resumed.")

    @app_commands.command(name="queue", description="Show the current queue.")
    async def queue(self, interaction: discord.Interaction) -> None:
        q = self.queue.get(interaction.guild_id, [])
        if not q:
            await interaction.response.send_message("Queue is empty.", ephemeral=True)
            return
        await interaction.response.send_message("\n".join(f"{i}. {t}" for i, t in enumerate(q, 1))[:1900])


async def setup(bot) -> None:
    await bot.add_cog(Music(bot))