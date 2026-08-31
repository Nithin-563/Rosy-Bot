"""Custom command cog: admins create server-specific commands (no arbitrary code)."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from rosy.core.errors import safe_user_message
from rosy.models import CustomCommand


class CustomCommands(commands.Cog, name="Custom Commands"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="add_command", description="Create a custom command for this server.")
    @app_commands.default_permissions(manage_guild=True)
    async def add_command(self, interaction: discord.Interaction, name: str, response: str, ai_powered: bool = False) -> None:
        name = name.lower().lstrip("!")
        if not re_is_valid_name(name):
            await interaction.response.send_message("Command names can only use letters, numbers, and underscores.", ephemeral=True)
            return
        async with self.bot.db.session() as session:
            from sqlalchemy import select

            res = await session.execute(
                select(CustomCommand).where(
                    CustomCommand.guild_id == interaction.guild_id,
                    CustomCommand.name == name,
                )
            )
            cmd = res.scalar_one_or_none()
            if cmd is None:
                cmd = CustomCommand(guild_id=interaction.guild_id, name=name)
                session.add(cmd)
            cmd.response = response
            cmd.ai_powered = ai_powered
            cmd.enabled = True
            await session.commit()
        await interaction.response.send_message(f"Command `{name}` saved.")

    @app_commands.command(name="remove_command", description="Delete a custom command.")
    @app_commands.default_permissions(manage_guild=True)
    async def remove_command(self, interaction: discord.Interaction, name: str) -> None:
        name = name.lower().lstrip("!")
        async with self.bot.db.session() as session:
            from sqlalchemy import select

            res = await session.execute(
                select(CustomCommand).where(
                    CustomCommand.guild_id == interaction.guild_id, CustomCommand.name == name
                )
            )
            cmd = res.scalar_one_or_none()
            if cmd is None:
                await interaction.response.send_message(f"No command named `{name}`.", ephemeral=True)
                return
            await session.delete(cmd)
            await session.commit()
        await interaction.response.send_message(f"Removed `{name}`.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        content = message.content.strip()
        if not content or not content.startswith(("!", "<")):
            return
        raw = content.lstrip("!").split()[0].lower()
        async with self.bot.db.session() as session:
            from sqlalchemy import select

            res = await session.execute(
                select(CustomCommand).where(
                    CustomCommand.guild_id == message.guild.id,
                    CustomCommand.name == raw,
                    CustomCommand.enabled == True,  # noqa: E712
                )
            )
            cmd = res.scalar_one_or_none()
        if cmd is None:
            return
        if cmd.ai_powered:
            try:
                result = await self.bot.conversation.generate(
                    user_text=cmd.response, user_id=message.author.id,
                    guild_id=message.guild.id, personality_mode="friendly",
                )
                await message.reply(result.text[:1999])
            except Exception as exc:
                await message.reply(safe_user_message(exc))
        else:
            await message.reply(cmd.response)


def re_is_valid_name(name: str) -> bool:
    import re

    return bool(re.fullmatch(r"[A-Za-z0-9_]{1,64}", name))


async def setup(bot) -> None:
    await bot.add_cog(CustomCommands(bot))