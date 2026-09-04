"""Core cog — help, ping, status."""
from __future__ import annotations

import time

import discord
from discord.ext import commands

from rosy.ux import embed, safe_send


class CoreCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._start = time.monotonic()

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        latency = round(self.bot.latency * 1000, 1)
        await safe_send(ctx, embed=embed("Pong!", f"Latency: `{latency} ms`", footer="Rosy"))

    @commands.command(name="help")
    async def help(self, ctx: commands.Context) -> None:
        text = (
            "**Rosy — AI Discord bot**\n\n"
            "**Conversation**\n"
            "• Mention Rosy or reply to her to chat.\n\n"
            "**Commands**\n"
            "• `!ping` — latency\n"
            "• `!remember <text>` — save a memory\n"
            "• `!memories` — list what Rosy remembers\n"
            "• `!forget <id>` — delete a memory\n"
            "• `!clear-memory` — clear your/guild memories\n"
            "• `!remind <when> <message>` — set a reminder\n"
            "• `!reminders` — list reminders\n"
            "• `!trivia` — play trivia\n"
            "• `!8ball <question>` — ask the magic 8-ball\n"
            "• `!roll [dice] [sides]` — roll dice\n"
            "• `!cc add <name> <response>` — add a custom command (admin)\n"
            "• `!warn <user> <reason>` — moderation (mods)\n"
            "• `!set-personality <mode>` — set personality (admin)\n\n"
            "Reply with `!help admin` for admin commands."
        )
        if ctx.message.content.strip().lower().endswith("admin"):
            text = (
                "**Admin commands** (server admins)\n\n"
                "• `!set-personality <mode>`\n"
                "• `!set-provider <name>`\n"
                "• `!set-model <model>`\n"
                "• `!auto-reply on|off`\n"
                "• `!cc add|list|remove <...>`\n"
                "• `!warn` `!timeout` `!kick` `!ban` `!unban` `!purge`\n"
                "• `!warnings <user>`\n"
            )
        await safe_send(ctx, embed=embed(description=text, footer="Rosy"))
