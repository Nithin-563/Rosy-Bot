"""Additional safe, useful Rosy utilities."""
from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from rosy.core.errors import safe_user_message

class Advanced(commands.Cog, name="Advanced"):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="web", description="Ask Rosy to search the public web for something.")
    async def web(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            result = await self.bot.tools.run("web_search", {"query": query, "max_results": 6}, permission="ai_tools")
            await interaction.followup.send(result[:1900])
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)

    @app_commands.command(name="debate", description="Debate a topic with Rosy.")
    async def debate(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer()
        try:
            result = await self.bot.conversation.generate(user_text=f"Debate this topic with me. Take a clear position, challenge weak points, and mention the strongest counterargument: {topic}", user_id=interaction.user.id, guild_id=interaction.guild_id, channel_id=interaction.channel_id, personality_mode="debate", user_name=interaction.user.display_name)
            await interaction.followup.send(result.text[:1900])
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)

    @app_commands.command(name="mood", description="Set Rosy's current chat style for this request.")
    @app_commands.choices(style=[
        app_commands.Choice(name="Friendly", value="friendly"),
        app_commands.Choice(name="Playful", value="playful"),
        app_commands.Choice(name="Humorous", value="humorous"),
        app_commands.Choice(name="Serious", value="serious"),
        app_commands.Choice(name="Supportive", value="supportive"),
        app_commands.Choice(name="Debate", value="debate"),
    ])
    async def mood(self, interaction: discord.Interaction, style: app_commands.Choice[str]):
        await interaction.response.defer()
        await interaction.followup.send(f"Got it — I’ll use a {style.value} vibe.", ephemeral=True)

    @app_commands.command(name="pick", description="Randomly choose from pipe-separated options.")
    async def pick(self, interaction: discord.Interaction, options: str):
        await interaction.response.defer()
        try:
            result = await self.bot.tools.run("random_choice", {"items": options}, permission="ai_tools")
            await interaction.followup.send(f"🎯 {result}")
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)

    @app_commands.command(name="regex_test", description="Test a regex against text safely.")
    async def regex_test(self, interaction: discord.Interaction, pattern: str, text: str):
        await interaction.response.defer()
        try:
            result = await self.bot.tools.run("regex_test", {"pattern": pattern, "text": text}, permission="ai_tools")
            await interaction.followup.send(f"🔎 {result}")
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)

    @app_commands.command(name="tool_status", description="Show Rosy's safe tool availability.")
    async def tool_status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        names = [t.name for t in self.bot.tools.specs()]
        await interaction.followup.send("🧰 Available: " + ", ".join(names))

async def setup(bot):
    await bot.add_cog(Advanced(bot))
