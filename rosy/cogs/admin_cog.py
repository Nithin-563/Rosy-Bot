"""Admin cog — server configuration through Discord."""
from __future__ import annotations

from discord.ext import commands

from rosy.personality.manager import PERSONALITY_MODES
from rosy.security.permissions import is_admin
from rosy.ux import embed, safe_send


class AdminCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _guild_only(self, ctx):
        if ctx.guild is None:
            await safe_send(ctx, "This command is server-only.")
            return False
        if not is_admin(ctx.author):
            await safe_send(ctx, "You need server admin permissions.", ephemeral=True)
            return False
        return True

    async def _prefs(self, session, guild_id):
        from rosy.db.models import GuildPreference
        gp = await session.get(GuildPreference, guild_id)
        if gp is None:
            gp = GuildPreference(guild_id=guild_id)
            session.add(gp)
        return gp

    @commands.command(name="set-personality")
    async def set_personality(self, ctx, mode: str) -> None:
        if not await self._guild_only(ctx):
            return
        if mode.lower() not in PERSONALITY_MODES:
            await safe_send(ctx, f"Valid modes: {', '.join(PERSONALITY_MODES)}")
            return
        async with self.bot.sessions() as session:
            gp = await self._prefs(session, ctx.guild.id)
            gp.personality_mode = mode.lower()
            await session.commit()
        await safe_send(ctx, f"✅ Personality set to **{mode.lower()}**.")

    @commands.command(name="auto-reply")
    async def auto_reply(self, ctx, state: str) -> None:
        if not await self._guild_only(ctx):
            return
        enabled = state.lower() in ("on", "true", "yes", "1")
        async with self.bot.sessions() as session:
            gp = await self._prefs(session, ctx.guild.id)
            gp.autonomous_replies = enabled
            await session.commit()
        await safe_send(ctx, f"✅ Autonomous replies **{'on' if enabled else 'off'}**.")

    @commands.command(name="set-model")
    async def set_model(self, ctx, model: str) -> None:
        if not await self._guild_only(ctx):
            return
        async with self.bot.sessions() as session:
            gp = await self._prefs(session, ctx.guild.id)
            gp.model = model
            await session.commit()
        await safe_send(ctx, f"✅ Model set to `{model}`.")

    @commands.command(name="set-provider")
    async def set_provider(self, ctx, provider: str) -> None:
        if not await self._guild_only(ctx):
            return
        if provider.lower() not in ("openrouter", "openai", "anthropic", "gemini", "groq", "mistral"):
            await safe_send(ctx, "Supported providers: openrouter, openai, anthropic, gemini, groq, mistral.")
            return
        async with self.bot.sessions() as session:
            gp = await self._prefs(session, ctx.guild.id)
            gp.provider_name = provider.lower()
            await session.commit()
        await safe_send(ctx, f"✅ Provider set to **{provider.lower()}**.")

    @commands.command(name="settings")
    async def settings(self, ctx) -> None:
        if ctx.guild is None:
            await safe_send(ctx, "This command is server-only.")
            return
        async with self.bot.sessions() as session:
            gp = await session.get(__import__("rosy.db.models", fromlist=["GuildPreference"]).GuildPreference, ctx.guild.id)
            if gp is None:
                await safe_send(ctx, "Default settings are active.")
                return
            lines = [
                f"Personality: **{gp.personality_mode}**",
                f"Provider: **{gp.provider_name or '(default)'}**",
                f"Model: **{gp.model or '(default)'}**",
                f"Autonomous replies: **{'on' if gp.autonomous_replies else 'off'}**",
                f"Memory: **{'on' if gp.memory_enabled else 'off'}**",
            ]
            await safe_send(ctx, embed=embed("Server settings", "\n".join(lines), footer="Rosy"))
