"""Custom (guild-specific) commands.

Admins create named commands with fixed responses or AI-powered responses.
Custom commands only ever return text — they can never execute code.
"""

import discord
from discord.ext import commands

from ..db import session as db_session
from ..db.models import CustomCommand, Guild

is_admin = commands.has_permissions(manage_guild=True)


class CustomCommandsCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _get_all(self, guild_id: int) -> list[CustomCommand]:
        from sqlalchemy import select

        async with db_session.get_sessionmaker()() as s:
            stmt = (
                select(CustomCommand)
                .where(CustomCommand.guild_id == guild_id, CustomCommand.enabled.is_(True))
                .order_by(CustomCommand.name)
            )
            result = await s.execute(stmt)
            return list(result.scalars().all())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        content = message.content
        if not content.startswith(self.bot.command_prefix):
            return
        name = content[len(self.bot.command_prefix):].split()[0].lower() if len(content) > 1 else ""
        if not name:
            return
        cmds = await self._get_all(message.guild.id)
        target = next((c for c in cmds if c.name.lower() == name), None)
        if target is None:
            target = next((c for c in cmds if name in [a.lower() for a in (c.aliases or [])]), None)
        if target is None:
            return
        # Do not shadow real built-in commands.
        if self.bot.get_command(name):
            return
        if target.use_ai:
            await self.bot._maybe_respond(message)
            return
        await message.channel.send(target.response or f"`{name}`")

    @commands.group(name="command", invoke_without_command=True)
    async def command(self, ctx: commands.Context) -> None:
        cmds = await self._get_all(ctx.guild.id)
        if not cmds:
            await ctx.send("No custom commands yet. Use `!command add <name> <response>`.")
            return
        await ctx.send("Custom commands: " + ", ".join(c.name for c in cmds))

    @command.command(name="add")
    @is_admin
    async def add(self, ctx: commands.Context, name: str, *, response: str) -> None:
        if self.bot.get_command(name):
            await ctx.send(f"`{name}` is a built-in command.")
            return
        async with db_session.get_sessionmaker()() as s:
            g = await s.get(Guild, ctx.guild.id)
            if g is None:
                g = Guild(id=ctx.guild.id)
                s.add(g)
                await s.flush()
            existing = next((c for c in g.custom_commands if c.name.lower() == name.lower()), None)
            if existing:
                existing.response = response
            else:
                s.add(CustomCommand(guild_id=ctx.guild.id, name=name.lower(), response=response))
            await s.commit()
        await ctx.send(f"Custom command **{name}** added.")

    @command.command(name="remove")
    @is_admin
    async def remove(self, ctx: commands.Context, name: str) -> None:
        async with db_session.get_sessionmaker()() as s:
            stmt = CustomCommand.__table__.delete().where(
                CustomCommand.__table__.c.guild_id == ctx.guild.id,
                CustomCommand.__table__.c.name == name.lower(),
            )
            result = await s.execute(stmt)
            await s.commit()
        await ctx.send("Removed." if result.rowcount else "Not found.")

    @command.command(name="ai")
    @is_admin
    async def ai(self, ctx: commands.Context, name: str, enabled: str) -> None:
        async with db_session.get_sessionmaker()() as s:
            from sqlalchemy import select

            stmt = select(CustomCommand).where(
                CustomCommand.guild_id == ctx.guild.id, CustomCommand.name == name.lower()
            )
            cc = (await s.execute(stmt)).scalar_one_or_none()
            if cc is None:
                await ctx.send("Command not found.")
                return
            cc.use_ai = enabled.lower() in ("on", "true", "yes")
            await s.commit()
        await ctx.send(f"`{name}` AI mode set to {enabled.lower()}.")
