"""Utility cog: a large set of deterministic, always-working commands.

These need no AI credits — they run entirely on the sandbox/bot host. Includes
web search/fetch powered by the inbuilt web tools.
"""

from __future__ import annotations

import base64
import hashlib
import random
import re
import string
import time
import uuid
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

LEET = str.maketrans(
    {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7", "g": "9", "b": "8"}
)


class Utility(commands.Cog, name="Utility"):
    def __init__(self, bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------- pick/random

    @app_commands.command(name="pick", description="Pick a random option from a list.")
    async def pick(self, interaction: discord.Interaction, options: str) -> None:
        opts = [o.strip() for o in options.split(",") if o.strip()]
        if len(opts) < 2:
            await interaction.response.send_message("Give at least 2 comma-separated options.", ephemeral=True)
            return
        await interaction.response.send_message(f"🎯 I pick: **{random.choice(opts)}**")

    @app_commands.command(name="random", description="Generate a random number in a range.")
    async def random_number(self, interaction: discord.Interaction, min_value: int = 1, max_value: int = 100) -> None:
        if min_value > max_value:
            min_value, max_value = max_value, min_value
        await interaction.response.send_message(f"🔢 Random number: **{random.randint(min_value, max_value)}**")

    @app_commands.command(name="coin", description="Flip a coin.")
    async def coin(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🪙 {random.choice(['Heads!', 'Tails!'])}")

    # ------------------------------------------------------------- text utils

    @app_commands.command(name="reverse", description="Reverse a piece of text.")
    async def reverse(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.send_message(text[::-1][:1900])

    @app_commands.command(name="leetspeak", description="Convert text to 1337 speak.")
    async def leetspeak(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.send_message(text.translate(LEET)[:1900])

    @app_commands.command(name="uppercase", description="Convert text to UPPERCASE.")
    async def uppercase(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.send_message(text.upper()[:1900])

    @app_commands.command(name="lowercase", description="Convert text to lowercase.")
    async def lowercase(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.send_message(text.lower()[:1900])

    @app_commands.command(name="emojify", description="Convert letters to regional-indicator emojis.")
    async def emojify(self, interaction: discord.Interaction, text: str) -> None:
        out = []
        for ch in text[:90]:
            if ch.isalpha():
                out.append(chr(0x1F1E6 + (ord(ch.lower()) - 97)))
            elif ch in "0123456789":
                out.append("🔢")
            elif ch == " ":
                out.append("   ")
            else:
                out.append(ch)
        await interaction.response.send_message("".join(out) or "😀")

    # ------------------------------------------------------------- encoding

    @app_commands.command(name="base64", description="Encode or decode base64.")
    async def base64_cmd(self, interaction: discord.Interaction, text: str, mode: str = "encode") -> None:
        mode = mode.lower()
        try:
            if mode == "encode":
                result = base64.b64encode(text.encode()).decode()
            elif mode == "decode":
                result = base64.b64decode(text.encode()).decode(errors="replace")
            else:
                await interaction.response.send_message("Mode must be `encode` or `decode`.", ephemeral=True)
                return
        except Exception:
            result = "Invalid base64 input."
        await interaction.response.send_message(result[:1900])

    @app_commands.command(name="rot13", description="Apply ROT13 cipher to text.")
    async def rot13(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.send_message(text.translate(str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
        ))[:1900])

    # ------------------------------------------------------------- generation

    @app_commands.command(name="password", description="Generate a secure random password.")
    async def password(self, interaction: discord.Interaction, length: int = 16) -> None:
        length = max(4, min(int(length), 64))
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        await interaction.response.send_message(f"🔐 `{''.join(random.choice(chars) for _ in range(length))}`")

    @app_commands.command(name="uuid", description="Generate a random UUID.")
    async def uuid_cmd(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🆔 `{uuid.uuid4()}`")

    @app_commands.command(name="hash", description="Hash text with sha256.")
    async def hash_cmd(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.send_message(f"#️⃣ `{hashlib.sha256(text.encode()).hexdigest()}`")

    @app_commands.command(name="hexcolor", description="Generate a random hex color.")
    async def hexcolor(self, interaction: discord.Interaction) -> None:
        color = f"#{random.randint(0, 0xFFFFFF):06x}"
        await interaction.response.send_message(f"🎨 Random color: **{color}**")

    # ------------------------------------------------------------- info

    @app_commands.command(name="avatar", description="Show a user's avatar.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None) -> None:
        member = member or interaction.user
        embed = discord.Embed(title=f"{member.display_name}'s avatar", color=discord.Color.blurple())
        embed.set_image(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="banner", description="Show a user's banner.")
    async def banner(self, interaction: discord.Interaction, member: discord.Member = None) -> None:
        member = member or interaction.user
        user = await self.bot.fetch_user(member.id)
        if user.banner:
            embed = discord.Embed(title=f"{member.display_name}'s banner", color=discord.Color.blurple())
            embed.set_image(url=user.banner.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("This user has no banner.", ephemeral=True)

    @app_commands.command(name="serverinfo", description="Show information about this server.")
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        g = interaction.guild
        embed = discord.Embed(title=g.name, color=discord.Color.green())
        embed.add_field(name="Members", value=str(g.member_count), inline=True)
        embed.add_field(name="Roles", value=str(len(g.roles)), inline=True)
        embed.add_field(name="Channels", value=str(len(g.channels)), inline=True)
        embed.add_field(name="Created", value=g.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Owner", value=str(g.owner or "unknown"), inline=True)
        embed.add_field(name="Boost level", value=str(g.premium_tier), inline=True)
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Show information about a user.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None) -> None:
        member = member or interaction.user
        embed = discord.Embed(title=member.display_name, color=discord.Color.blurple())
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "unknown", inline=True)
        embed.add_field(name="Roles", value=str(len(member.roles)), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="uptime", description="How long Rosy has been running.")
    async def uptime(self, interaction: discord.Interaction) -> None:
        up = int(time.monotonic() - self.bot._stats["started"])
        await interaction.response.send_message(f"⏱️ Online for **{up // 3600}h {(up % 3600) // 60}m {up % 60}s**")

    @app_commands.command(name="timestamp", description="Show the current UTC time.")
    async def timestamp(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"🕐 **{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC**")

    # ------------------------------------------------------------- web tools

    @app_commands.command(name="search", description="Search the web and show results.")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        await interaction.response.defer()
        try:
            result = await self.bot.tools.run("web_search", {"query": query, "max_results": 5})
        except Exception as exc:
            await interaction.followup.send(f"⚠️ Search failed: {safe_str(exc)}")
            return
        await interaction.followup.send(f"🔎 **Results for:** {query}\n\n{result[:1800]}")

    @app_commands.command(name="fetch", description="Fetch and summarize the main text of a web page.")
    async def fetch(self, interaction: discord.Interaction, url: str) -> None:
        await interaction.response.defer()
        try:
            result = await self.bot.tools.run("web_fetch", {"url": url, "max_chars": 1500})
        except Exception as exc:
            await interaction.followup.send(f"⚠️ Could not fetch page: {safe_str(exc)}")
            return
        await interaction.followup.send(result[:1900])

    # ------------------------------------------------------------- misc

    @app_commands.command(name="poll", description="Create a quick poll (up to 4 options).")
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = "", option4: str = "") -> None:
        opts = [option1, option2] + ([option3] if option3 else []) + ([option4] if option4 else [])
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        lines = "\n".join(f"{emojis[i]} {o}" for i, o in enumerate(opts))
        msg = await interaction.response.send_message(f"**📊 {question}**\n{lines}")
        for i in range(len(opts)):
            await msg.add_reaction(emojis[i])

    # ------------------------------------------------------------ web info

    @app_commands.command(name="weather", description="Get the current weather for a city.")
    async def weather(self, interaction: discord.Interaction, city: str) -> None:
        await interaction.response.defer()
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(
                    "https://wttr.in/" + city.replace(" ", "+") + "?format=3&m"
                )
                text = (r.text or "").strip()
            if not text or "Unknown location" in text:
                await interaction.followup.send(f"Couldn't find weather for **{city}**.")
            else:
                await interaction.followup.send(f"🌤️ {text}")
        except Exception as exc:
            await interaction.followup.send(f"Weather lookup failed: {safe_str(exc)}")

    @app_commands.command(name="define", description="Look up the definition of a word.")
    async def define(self, interaction: discord.Interaction, word: str) -> None:
        await interaction.response.defer()
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
                if r.status_code != 200:
                    await interaction.followup.send(f"No definition found for **{word}**.")
                    return
                data = r.json()[0]
                meaning = data.get("meanings", [{}])[0]
                pos = meaning.get("partOfSpeech", "")
                defn = meaning.get("definitions", [{}])[0].get("definition", "")
                await interaction.followup.send(
                    f"📖 **{word}** ({pos}): {defn}"[:1900]
                )
        except Exception as exc:
            await interaction.followup.send(f"Definition lookup failed: {safe_str(exc)}")

    @app_commands.command(name="fact", description="Get a random fun fact.")
    async def fact(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get("https://uselessfacts.jsph.pl/random.json?language=en", follow_redirects=True)
                data = r.json()
                text = data.get("text", "").strip()
            await interaction.followup.send(f"💡 {text}" if text else "No fact right now!")
        except Exception as exc:
            await interaction.followup.send(f"Couldn't get a fact: {safe_str(exc)}")


def safe_str(exc: Exception) -> str:
    return getattr(exc, "message", None) or str(exc)[:200]


async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))