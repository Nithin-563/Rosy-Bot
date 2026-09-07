"""Custom commands cog — server-specific commands (admin-managed)."""
from __future__ import annotations

from discord.ext import commands

from rosy.custom_commands.service import parse_role_ids
from rosy.security.permissions import is_moderator
from rosy.ux import embed, safe_send


class CustomCommandsCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.group(name="cc", invoke_without_command=True)
    async def cc(self, ctx, *, name: str = "") -> None:
        if not name:
            await self.list(ctx)
            return
        await self._run(ctx, name)

    async def _run(self, ctx, name: str) -> None:
        if ctx.guild is None:
            await safe_send(ctx, "Custom commands are server-only.")
            return
        async with self.bot.sessions() as session:
            cmd = await self.bot.custom_commands.get(session, ctx.guild.id, name)
        if cmd is None or not cmd.enabled:
            return
        roles = parse_role_ids(cmd.allowed_roles)
        if roles and not any(r.id in roles for r in ctx.author.roles):
            await safe_send(ctx, "You don't have permission to use that command.", ephemeral=True)
            return
        if cmd.ai_powered:
            text = f"*(custom command {cmd.name})* {ctx.message.content.removeprefix('!cc').strip()}"
            from rosy.ai.base import Message
            response = await self.bot.engine_ai.respond(recent_messages=[Message(role="user", content=text)], guild_id=ctx.guild.id, user_id=ctx.author.id)
            await safe_send(ctx, embed=embed(description=response.content, footer="Rosy"))
        else:
            await safe_send(ctx, embed=embed(description=cmd.response or "", footer="Rosy"))

    @cc.command(name="add")
    async def cc_add(self, ctx, name: str, *, response: str) -> None:
        if not is_moderator(ctx.author):
            await safe_send(ctx, "You need to be a moderator to add commands.", ephemeral=True)
            return
        async with self.bot.sessions() as session:
            await self.bot.custom_commands.upsert(session, guild_id=ctx.guild.id, name=name, response=response)
        await safe_send(ctx, f"✅ Custom command `!{name}` added.")

    @cc.command(name="list")
    async def list(self, ctx) -> None:
        if ctx.guild is None:
            return
        async with self.bot.sessions() as session:
            cmds = await self.bot.custom_commands.list(session, ctx.guild.id)
        if not cmds:
            await safe_send(ctx, "No custom commands yet.")
            return
        lines = [f"`!{c.name}` — {c.response[:40]}{' (AI)' if c.ai_powered else ''}" for c in cmds]
        await safe_send(ctx, embed=embed("Custom commands", "\n".join(lines), footer="Rosy"))

    @cc.command(name="remove")
    async def cc_remove(self, ctx, name: str) -> None:
        if not is_moderator(ctx.author):
            await safe_send(ctx, "You need to be a moderator.", ephemeral=True)
            return
        async with self.bot.sessions() as session:
            removed = await self.bot.custom_commands.delete(session, ctx.guild.id, name)
        await safe_send(ctx, "✅ Removed." if removed else "Command not found.")
