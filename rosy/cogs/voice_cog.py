"""Voice cog — join/leave voice channels (speech hooks wired to providers)."""
from __future__ import annotations

import logging

import discord
from discord.ext import commands

from rosy.ux import embed, safe_send

log = logging.getLogger(__name__)


class VoiceCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name="join")
    async def join(self, ctx) -> None:
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await safe_send(ctx, "Join a voice channel first.", ephemeral=True)
            return
        try:
            client = await ctx.author.voice.channel.connect()
            self.bot.voice.track(ctx.guild.id, client)
            await safe_send(ctx, f"🔊 Joined **{ctx.author.voice.channel.name}**.")
        except discord.HTTPException as exc:
            await safe_send(ctx, f"Could not join: {exc}", ephemeral=True)

    @commands.command(name="leave")
    async def leave(self, ctx) -> None:
        client = self.bot.voice._clients.get(ctx.guild.id)  # type: ignore[attr-defined]
        if client is None:
            await safe_send(ctx, "I'm not in a voice channel.")
            return
        await client.disconnect()
        self.bot.voice.untrack(ctx.guild.id)
        await safe_send(ctx, "👋 Left the voice channel.")

    @commands.command(name="speak")
    async def speak(self, ctx, *, text: str) -> None:
        client = self.bot.voice._clients.get(ctx.guild.id)  # type: ignore[attr-defined]
        if client is None:
            await safe_send(ctx, "Join me to a voice channel first (`!join`).", ephemeral=True)
            return
        ok = await self.bot.voice.speak(ctx.guild.id, text)
        await safe_send(ctx, "🔊 Speaking..." if ok else "Voice/TTS is not configured on this instance.", ephemeral=True)
