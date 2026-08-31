"""Help cog: overview of Rosy's commands and capabilities."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog, name="Help"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="Show what Rosy can do.")
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Rosy",
            description="A modular AI assistant for Discord. Chat, remember, moderate, remind, and play.",
            color=discord.Color.blurple(),
        )
        groups = {
            "💬 Chat": ["/chat <prompt>", "Mention @Rosy", "Reply to Rosy"],
            "🧠 Memory": ["/remember <thing>", "/forget <thing>", "/memories", "/clear_memories"],
            "⚙️ Admin": ["/config", "/set_provider", "/set_model", "/set_personality", "/set_autonomous"],
            "🛡️ Moderation": ["/warn", "/timeout", "/kick", "/ban", "/mod_history"],
            "⏰ Reminders": ["/remind <30m> <msg>", "/reminders", "/cancel_reminder <id>"],
            "🎮 Games": ["/8ball <q>", "/dice 2d6", "/trivia", "/guess"],
            "🎵 Music": ["/play <song>", "/pause", "/resume", "/skip", "/stop", "/queue"],
            "🔊 Voice": ["/join", "/leave"],
            "🧩 Custom": ["/add_command", "/remove_command"],
            "🎉 Fun": ["/echo", "/insult", "/stats", "/ping"],
        }
        for name, cmds in groups.items():
            embed.add_field(name=name, value="\n".join(cmds), inline=False)
        embed.set_footer(text="Set your provider/model under /config")
        await interaction.response.send_message(embed=embed, ephemeral=False)


async def setup(bot) -> None:
    await bot.add_cog(Help(bot))