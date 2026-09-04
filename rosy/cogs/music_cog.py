"""Music cog — play/pause/resume/skip/stop/queue/volume/loop/now-playing.

Playback requires a VoiceClient and ffmpeg. The `play` command resolves a
source via the optional `yt-dlp` extra; when unavailable, it instructs the user
to provide a direct audio URL.
"""
from __future__ import annotations

import logging

import discord
from discord.ext import commands

from rosy.music.player import Track
from rosy.ux import embed, safe_send

log = logging.getLogger(__name__)


class MusicCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def _voice(self, guild_id: int) -> discord.VoiceClient | None:
        return self.bot.voice._clients.get(guild_id)  # type: ignore[attr-defined]

    async def _ensure_voice(self, ctx) -> discord.VoiceClient | None:
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await safe_send(ctx, "Join a voice channel first.", ephemeral=True)
            return None
        client = self._voice(ctx.guild.id)
        if client is None:
            try:
                client = await ctx.author.voice.channel.connect()
                self.bot.voice.track(ctx.guild.id, client)
            except discord.HTTPException as exc:
                await safe_send(ctx, f"Could not join voice: {exc}", ephemeral=True)
                return None
        return client

    async def _play_next(self, ctx) -> None:
        client = self._voice(ctx.guild.id)
        if client is None:
            return
        track = self.bot.music.next(ctx.guild.id)
        if track is None:
            await client.disconnect()
            self.bot.voice.untrack(ctx.guild.id)
            self.bot.music.mark_playing(ctx.guild.id, False)
            return
        self.bot.music.mark_playing(ctx.guild.id, True)
        await safe_send(ctx, embed=embed("🎵 Now playing", f"**{track.title}**", footer="Rosy"))
        try:
            source = discord.FFmpegPCMAudio(track.url, options="-vn")
        except Exception:  # noqa: BLE001
            await safe_send(ctx, "Could not create audio source (ffmpeg required).")
            return
        client.play(source, after=lambda e: self.bot.loop.create_task(self._play_next(ctx)))

    @commands.command(name="play")
    async def play(self, ctx, *, query: str) -> None:
        client = await self._ensure_voice(ctx)
        if client is None:
            return
        url = query if query.startswith("http") else None
        title = query
        if url is None:
            await safe_send(ctx, "Provide a direct audio URL, or install `yt-dlp` for search/YouTube playback.")
            # Enqueue as a placeholder local source is not meaningful; require a URL.
            return
        track = Track(title=title, url=url, requested_by=ctx.author.id, source="url")
        pos = self.bot.music.enqueue(ctx.guild.id, track)
        await safe_send(ctx, f"⏳ Added to queue (position {pos}).")
        if not self.bot.music.now(ctx.guild.id):
            await self._play_next(ctx)

    @commands.command(name="pause")
    async def pause(self, ctx) -> None:
        client = self._voice(ctx.guild.id)
        if client and client.is_playing():
            client.pause()
            self.bot.music.mark_playing(ctx.guild.id, True, paused=True)
            await safe_send(ctx, "⏸ Paused.")
        else:
            await safe_send(ctx, "Nothing playing.")

    @commands.command(name="resume")
    async def resume(self, ctx) -> None:
        client = self._voice(ctx.guild.id)
        if client and client.is_paused():
            client.resume()
            await safe_send(ctx, "▶ Resumed.")
        else:
            await safe_send(ctx, "Nothing paused.")

    @commands.command(name="skip")
    async def skip(self, ctx) -> None:
        client = self._voice(ctx.guild.id)
        if client and client.is_playing():
            client.stop()
        await self._play_next(ctx)

    @commands.command(name="stop")
    async def stop(self, ctx) -> None:
        self.bot.music.clear(ctx.guild.id)
        client = self._voice(ctx.guild.id)
        if client:
            await client.disconnect()
            self.bot.voice.untrack(ctx.guild.id)
        self.bot.music.mark_playing(ctx.guild.id, False)
        await safe_send(ctx, "⏹ Stopped and cleared the queue.")

    @commands.command(name="queue")
    async def queue(self, ctx) -> None:
        st = self.bot.music.state(ctx.guild.id)
        now = st.current
        q = list(st.queue)
        lines = [f"Now: **{now.title}**" if now else "Nothing playing."]
        for i, t in enumerate(q[:15], 1):
            lines.append(f"{i}. {t.title}")
        await safe_send(ctx, embed=embed("Queue", "\n".join(lines), footer="Rosy"))

    @commands.command(name="volume")
    async def volume(self, ctx, value: float) -> None:
        vol = self.bot.music.set_volume(ctx.guild.id, value / 100.0)
        client = self._voice(ctx.guild.id)
        if client and client.source is not None:
            try:
                client.source.volume = vol
            except Exception:  # noqa: BLE001
                pass
        await safe_send(ctx, f"🔊 Volume set to **{vol * 100:.0f}%**.")

    @commands.command(name="loop")
    async def loop(self, ctx) -> None:
        enabled = self.bot.music.set_loop(ctx.guild.id, not self.bot.music.state(ctx.guild.id).loop)
        await safe_send(ctx, f"🔁 Loop **{'on' if enabled else 'off'}**.")

    @commands.command(name="np")
    async def now_playing(self, ctx) -> None:
        track = self.bot.music.now(ctx.guild.id)
        await safe_send(ctx, f"▶ **{track.title}**" if track else "Nothing playing.")
