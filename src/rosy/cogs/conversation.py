"""Conversation cog: listens to messages and decides when to respond."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from rosy.core.errors import safe_user_message

logger = logging.getLogger("rosy.cog.conversation")


class Conversation(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.guild is None:
            await self._handle(message, is_dm=True)
            return
        # skip if not addressed in a busy channel to avoid spam (decision engine handles this)
        await self._handle(message, is_dm=False)

    async def _handle(self, message: discord.Message, is_dm: bool) -> None:
        mentions_me = message.mentions and self.bot.user in message.mentions
        is_reply = False
        if message.reference and message.reference.resolved is not None:
            is_reply = message.reference.resolved.author == self.bot.user
        content = message.content or ""
        if not content.strip() and not mentions_me:
            # ignore messages with no text (images only) unless mentioned
            if not mentions_me:
                return

        gs = None
        if message.guild:
            gs = await self.bot.guild_settings.get_settings(message.guild.id)
            await self.bot.guild_settings.ensure_guild(message.guild.id, message.guild.name)

        provider = gs.ai_provider if gs else None
        model = gs.ai_model if gs else ""
        autonomous = (gs.autonomous_enabled if gs else True)
        probability = (gs.autonomous_probability if gs else 0.15)

        should = await self.bot.conversation.should_respond(
            bot_id=self.bot.user.id,
            author_id=message.author.id,
            content=content,
            mentions_me=mentions_me,
            is_reply_to_me=is_reply,
            is_dm=is_dm,
            is_bot=message.author.bot,
            channel_key=str(message.channel.id),
            autonomous_enabled=autonomous,
            probability=probability,
        )
        if not should:
            return

        try:
            await message.channel.typing()
            result = await self.bot.conversation.generate(
                user_text=content,
                user_id=message.author.id,
                guild_id=message.guild.id if message.guild else None,
                channel_id=message.channel.id,
                is_dm=is_dm,
                personality_mode=gs.personality_mode if gs else "friendly",
                guild_name=message.guild.name if message.guild else "",
                user_name=message.author.display_name,
                provider=provider,
                model=model,
            )
            self.bot.conversation.mark_response(str(message.channel.id))
            text = result.text.strip()
            if len(text) > 2000:
                text = text[:1997] + "..."
            await message.reply(text)
            # Optional: speak the reply aloud if auto-speak is on.
            voice = self.bot.get_cog("Voice")
            if voice is not None and getattr(voice, "auto_speak", False):
                try:
                    await voice.speak(text)
                except Exception:
                    logger.warning("Could not speak reply in voice")
        except Exception as exc:
            try:
                await message.reply(safe_user_message(exc))
            except Exception:
                pass
            logger.exception("Conversation error")

    @discord.app_commands.command(name="chat", description="Ask Rosy something directly.")
    async def chat(self, interaction: discord.Interaction, prompt: str) -> None:
        await interaction.response.defer()
        try:
            result = await self.bot.conversation.generate(
                user_text=prompt,
                user_id=interaction.user.id,
                guild_id=interaction.guild_id,
                channel_id=interaction.channel_id,
                is_dm=interaction.guild is None,
                personality_mode="friendly",
                user_name=interaction.user.display_name,
            )
            text = result.text.strip()
            if len(text) > 1900:
                text = text[:1897] + "..."
            await interaction.followup.send(text)
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(Conversation(bot))