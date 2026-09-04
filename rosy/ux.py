"""Polished Discord UX helpers: embeds, typing, ephemeral replies."""
from __future__ import annotations

import time
from typing import Any

import discord


def embed(
    title: str = "",
    description: str = "",
    *,
    color: int = 0x6E7BFF,
    fields: list[tuple[str, str, bool]] | None = None,
    footer: str = "Rosy",
) -> discord.Embed:
    e = discord.Embed(title=title or None, description=description or None, color=color)
    for name, value, inline in fields or []:
        e.add_field(name=name, value=value, inline=inline)
    e.set_footer(text=footer)
    return e


async def safe_send(ctx, content: str = "", *, embed: discord.Embed | None = None, ephemeral: bool = False, **kwargs: Any):
    """Send a message, silently degrading if interaction already responded."""
    try:
        if ctx.interaction is not None:
            return await ctx.respond(content or None, embed=embed, ephemeral=ephemeral, **kwargs)
        return await ctx.send(content or None, embed=embed, **kwargs)
    except discord.HTTPException:
        try:
            return await ctx.send(content or None, embed=embed, **kwargs)
        except discord.HTTPException:
            return None


async def think(ctx) -> None:
    try:
        if ctx.interaction is not None and not ctx.interaction.response.is_done():
            await ctx.defer()
        else:
            await ctx.typing()
    except discord.HTTPException:
        pass


def duration_string(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
