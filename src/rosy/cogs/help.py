"""Dynamic help generated from the live Discord command tree."""
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog, name="Help"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="Show Rose's live command list.")
    async def help(self, interaction: discord.Interaction) -> None:
        commands_list = sorted(self.bot.tree.get_commands(), key=lambda c: c.name)
        lines = [f"`/{c.name}` — {c.description}" for c in commands_list]
        chunks = []
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > 1000:
                chunks.append(current)
                current = line
            else:
                current += ("\n" if current else "") + line
        if current:
            chunks.append(current)
        embed = discord.Embed(title="Rose • Commands", description="Live commands registered with Discord.", color=discord.Color.blurple())
        for i, chunk in enumerate(chunks[:25], 1):
            embed.add_field(name=f"Commands {i}", value=chunk, inline=False)
        embed.set_footer(text="Powered by Wisee Models • MakeIt Company")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot) -> None:
    await bot.add_cog(Help(bot))
