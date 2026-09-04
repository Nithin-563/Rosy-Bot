"""Files & documents cog — summarize and answer questions about attachments.

Requires an AI provider that supports text input (image/PDF understanding is
provider-dependent). Files are not stored permanently; content is read,
converted to text, and passed to the model in a single context.
"""
from __future__ import annotations

import logging

import discord
from discord.ext import commands

from rosy.ai.base import Message
from rosy.ux import embed, safe_send

log = logging.getLogger(__name__)

MAX_BYTES = 8 * 1024 * 1024  # 8 MB safety cap


class FilesCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name="analyze")
    async def analyze(self, ctx, *, instruction: str = "Summarize this file.") -> None:
        if not ctx.message.attachments:
            await safe_send(ctx, "Attach a file to analyze, e.g. `!analyze` with a PDF or text file attached.")
            return
        att = ctx.message.attachments[0]
        if att.size > MAX_BYTES:
            await safe_send(ctx, "File is too large (max 8 MB).", ephemeral=True)
            return

        data = await att.read()
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            text = f"[binary file: {att.filename}, {len(data)} bytes]"

        if not text.strip() and not att.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            await safe_send(ctx, "Could not extract text from this file type.")
            return

        prompt = (
            f"{instruction}\n\nFile: {att.filename}\n---\n"
            f"{text[:14000]}"
        )
        try:
            response = await self.bot.engine_ai.respond(
                recent_messages=[Message(role="user", content=prompt)],
                guild_id=ctx.guild.id if ctx.guild else None,
                user_id=ctx.author.id,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("analyze failed: %s", exc)
            await safe_send(ctx, "Analysis failed. The model may not support this file type.")
            return
        await safe_send(ctx, embed=embed(f"📄 {att.filename}", response.content[:4000], footer="Rosy"))
