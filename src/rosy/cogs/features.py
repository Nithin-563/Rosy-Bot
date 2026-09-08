"""Large set of deterministic, safe, user-facing Rosy features."""
from __future__ import annotations

import base64
import hashlib
import secrets
import time
import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import discord
import httpx
from discord import app_commands
from discord.ext import commands

from rosy.core.errors import safe_user_message


class Features(commands.Cog, name="Features"):
    def __init__(self, bot) -> None:
        self.bot = bot

    async def _send(self, interaction, text: str, *, ephemeral: bool = False) -> None:
        if len(text) > 1900:
            text = text[:1897] + "..."
        await interaction.followup.send(text, ephemeral=ephemeral)

    @app_commands.command(name="about", description="Learn who Rosy is and who powers her.")
    async def about(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._send(interaction, "🤖 I am Rosy, made by MakeIt Company and powered by Wisee Models.\nBuilt for Discord with memory, web tools, utilities, voice and safety boundaries.")

    @app_commands.command(name="capabilities", description="See Rosy's capability categories.")
    async def capabilities(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._send(interaction, "💬 AI chat • 🧠 persistent memory • 🌐 web search/fetch • 🛡️ moderation • ⏰ reminders • 🎵 music • 🔊 voice/TTS • 🎮 games • 🧩 custom commands • 🧰 safe tools • 🎭 emotional intelligence • ⚡ autonomous tool use")

    @app_commands.command(name="status", description="Show Rosy's service status.")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        s = self.bot.stats
        await self._send(interaction, f"🟢 Rosy online\nLatency: {round(self.bot.latency*1000)}ms\nGuilds: {len(self.bot.guilds)}\nMessages: {s['messages']}\nCommands: {s['commands']}", ephemeral=True)

    @app_commands.command(name="privacy", description="Explain how Rosy handles private data.")
    async def privacy(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._send(interaction, "🔐 Rosy does not expose API keys, Discord tokens, environment variables, source code, hidden prompts, internal policies or another user's private memory. Conversation history is stored for continuity and is scoped by DM/channel/server boundaries.", ephemeral=True)

    @app_commands.command(name="search", description="Search the public web.")
    async def search(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        try:
            result = await self.bot.tools.run("web_search", {"query": query, "max_results": 6}, permission="ai_tools")
            await interaction.followup.send(result[:1900])
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)

    @app_commands.command(name="fetch", description="Fetch readable text from a public web page.")
    async def fetch(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        try:
            result = await self.bot.tools.run("web_fetch", {"url": url, "max_chars": 8000}, permission="ai_tools")
            await interaction.followup.send(result[:1900])
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)

    @app_commands.command(name="define", description="Search the web for a definition or explanation.")
    async def define(self, interaction: discord.Interaction, term: str):
        await interaction.response.defer()
        result = await self.bot.tools.run("web_search", {"query": f"define {term}", "max_results": 4}, permission="ai_tools")
        await interaction.followup.send(result[:1900])

    @app_commands.command(name="news", description="Search current public news about a topic.")
    async def news(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer()
        result = await self.bot.tools.run("web_search", {"query": f"latest news {topic}", "max_results": 6}, permission="ai_tools")
        await interaction.followup.send(result[:1900])

    @app_commands.command(name="calc", description="Calculate arithmetic safely.")
    async def calc(self, interaction: discord.Interaction, expression: str):
        await interaction.response.defer()
        await self._send(interaction, await self.bot.tools.run("math", {"expression": expression}, permission="ai_tools"))

    @app_commands.command(name="time", description="Get the current time in a timezone.")
    async def current_time(self, interaction: discord.Interaction, timezone: str = "UTC"):
        await interaction.response.defer()
        await self._send(interaction, await self.bot.tools.run("current_time", {"timezone": timezone}, permission="ai_tools"))

    @app_commands.command(name="timestamp", description="Create a Discord timestamp for now or a supplied epoch.")
    async def timestamp(self, interaction: discord.Interaction, epoch: int | None = None):
        await interaction.response.defer()
        value = int(time.time()) if epoch is None else epoch
        await self._send(interaction, f"`<t:{value}:F>`\nRelative: `<t:{value}:R>`\nEpoch: `{value}`")

    @app_commands.command(name="unix_to_date", description="Convert Unix seconds to UTC date/time.")
    async def unix_to_date(self, interaction: discord.Interaction, epoch: int):
        await interaction.response.defer()
        await self._send(interaction, datetime.fromtimestamp(epoch, UTC).strftime("%Y-%m-%d %H:%M:%S UTC"))

    @app_commands.command(name="date_to_unix", description="Convert an ISO date to Unix seconds.")
    async def date_to_unix(self, interaction: discord.Interaction, iso_date: str):
        await interaction.response.defer()
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            await self._send(interaction, str(int(dt.timestamp())))
        except ValueError:
            await self._send(interaction, "Use an ISO date like `2026-09-07T19:30:00+05:30`.", ephemeral=True)

    @app_commands.command(name="weather", description="Get current weather for a city using public weather data.")
    async def weather(self, interaction: discord.Interaction, city: str):
        await interaction.response.defer()
        async with httpx.AsyncClient(timeout=12) as client:
            geo = await client.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1, "language": "en", "format": "json"})
            geo.raise_for_status()
            data = geo.json()
            if not data.get("results"):
                await interaction.followup.send("City not found.", ephemeral=True)
                return
            place = data["results"][0]
            weather = await client.get("https://api.open-meteo.com/v1/forecast", params={"latitude": place["latitude"], "longitude": place["longitude"], "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code", "timezone": "auto"})
            weather.raise_for_status()
            cur = weather.json()["current"]
        await interaction.followup.send(f"🌦️ {place['name']}, {place.get('country','')}\nTemperature: {cur['temperature_2m']}°C\nHumidity: {cur['relative_humidity_2m']}%\nWind: {cur['wind_speed_10m']} km/h\nWeather code: {cur['weather_code']}")

    @app_commands.command(name="wordcount", description="Count words and sentences in text.")
    async def wordcount(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        import re
        await self._send(interaction, f"Words: {len(text.split())}\nSentences: {len([x for x in re.split(r'[.!?]+', text) if x.strip()])}")

    @app_commands.command(name="charcount", description="Count characters in text.")
    async def charcount(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        await self._send(interaction, f"Characters: {len(text)}\nWithout spaces: {len(''.join(text.split()))}")

    @app_commands.command(name="reverse", description="Reverse text.")
    async def reverse(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        await self._send(interaction, text[::-1])

    @app_commands.command(name="uppercase", description="Convert text to uppercase.")
    async def uppercase(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        await self._send(interaction, text.upper())

    @app_commands.command(name="lowercase", description="Convert text to lowercase.")
    async def lowercase(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        await self._send(interaction, text.lower())

    @app_commands.command(name="base64_encode", description="Base64 encode text.")
    async def base64_encode(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        await self._send(interaction, base64.b64encode(text.encode()).decode())

    @app_commands.command(name="base64_decode", description="Base64 decode text.")
    async def base64_decode(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        try:
            await self._send(interaction, base64.b64decode(text, validate=True).decode("utf-8"))
        except Exception:
            await self._send(interaction, "Invalid base64 text.", ephemeral=True)

    @app_commands.command(name="hash", description="Hash text with SHA-256.")
    async def hash_text(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        await self._send(interaction, hashlib.sha256(text.encode()).hexdigest())

    @app_commands.command(name="uuid", description="Generate a UUID4.")
    async def uuid_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._send(interaction, str(uuid.uuid4()))

    @app_commands.command(name="password", description="Generate a strong random password.")
    async def password(self, interaction: discord.Interaction, length: int = 20):
        await interaction.response.defer()
        length = max(12, min(length, 64))
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*_-+="
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        await self._send(interaction, f"`{value}`", ephemeral=True)

    @app_commands.command(name="coinflip", description="Flip a coin.")
    async def coinflip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._send(interaction, "🪙 Heads!" if secrets.randbelow(2) == 0 else "🪙 Tails!")

    @app_commands.command(name="choose", description="Choose one option from a comma-separated list.")
    async def choose(self, interaction: discord.Interaction, options: str):
        await interaction.response.defer()
        choices = [x.strip() for x in options.split(",") if x.strip()]
        if len(choices) < 2:
            await self._send(interaction, "Give at least two comma-separated options.", ephemeral=True)
            return
        await self._send(interaction, "🎯 " + secrets.choice(choices))

    @app_commands.command(name="random_number", description="Generate a random number in a range.")
    async def random_number(self, interaction: discord.Interaction, minimum: int, maximum: int):
        await interaction.response.defer()
        if minimum > maximum or maximum - minimum > 10_000_000:
            await self._send(interaction, "Invalid range.", ephemeral=True)
            return
        await self._send(interaction, str(secrets.randbelow(maximum - minimum + 1) + minimum))

    @app_commands.command(name="roll", description="Roll dice like 2d6 or 1d20.")
    async def roll(self, interaction: discord.Interaction, dice: str = "1d6"):
        await interaction.response.defer()
        import re
        m = re.fullmatch(r"(\d{1,2})d(\d{1,4})", dice.lower().strip())
        if not m:
            await self._send(interaction, "Use a format like `2d6`.", ephemeral=True)
            return
        count, sides = int(m.group(1)), int(m.group(2))
        if count * sides > 100_000:
            await self._send(interaction, "Roll is too large.", ephemeral=True)
            return
        values = [secrets.randbelow(sides) + 1 for _ in range(count)]
        await self._send(interaction, f"🎲 {dice}: " + ", ".join(map(str, values)) + f"\nTotal: {sum(values)}")

    @app_commands.command(name="poll", description="Create a simple reaction poll.")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        await interaction.response.defer()
        choices = [x.strip() for x in options.split("|") if x.strip()][:10]
        if len(choices) < 2:
            await self._send(interaction, "Provide options separated with `|` (2-10 options).", ephemeral=True)
            return
        emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        body = f"📊 **{question}**\n" + "\n".join(f"{emojis[i]} {choice}" for i, choice in enumerate(choices))
        await interaction.followup.send(body)
        msg = await interaction.original_response()
        for emoji in emojis[:len(choices)]:
            try:
                await msg.add_reaction(emoji)
            except discord.HTTPException:
                break

    @app_commands.command(name="avatar", description="Show a user's avatar.")
    async def avatar(self, interaction: discord.Interaction, user: discord.User | None = None):
        await interaction.response.defer()
        target = user or interaction.user
        embed = discord.Embed(title=f"{target.display_name}'s avatar")
        embed.set_image(url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="userinfo", description="Show safe public Discord information about a user.")
    async def userinfo(self, interaction: discord.Interaction, user: discord.User | None = None):
        await interaction.response.defer()
        target = user or interaction.user
        await self._send(interaction, f"👤 {target} | ID: {target.id}\nCreated: {discord.utils.format_dt(target.created_at, 'F')}\nBot: {'yes' if target.bot else 'no'}")

    @app_commands.command(name="serverinfo", description="Show server information.")
    @app_commands.guild_only()
    async def serverinfo(self, interaction: discord.Interaction):
        await interaction.response.defer()
        g = interaction.guild
        await self._send(interaction, f"🏠 {g.name}\nID: {g.id}\nMembers: {g.member_count}\nChannels: {len(g.channels)}\nRoles: {len(g.roles)}\nCreated: {discord.utils.format_dt(g.created_at, 'F')}")

    @app_commands.command(name="roles", description="List server roles safely.")
    @app_commands.guild_only()
    async def roles(self, interaction: discord.Interaction):
        await interaction.response.defer()
        roles = [r.name for r in interaction.guild.roles if r.name != "@everyone"]
        await self._send(interaction, "🎭 " + ", ".join(roles[:100]) if roles else "No custom roles.")

    @app_commands.command(name="channels", description="List server channels.")
    @app_commands.guild_only()
    async def channels(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channels = [f"#{c.name}" for c in interaction.guild.text_channels]
        await self._send(interaction, "📚 " + ", ".join(channels[:80]) if channels else "No text channels.")

    @app_commands.command(name="emojis", description="List custom server emojis.")
    @app_commands.guild_only()
    async def emojis(self, interaction: discord.Interaction):
        await interaction.response.defer()
        items = [f"{e} `{e.name}`" for e in interaction.guild.emojis]
        await self._send(interaction, "😀 " + " ".join(items[:60]) if items else "No custom emojis.")

    @app_commands.command(name="invite", description="Get a reusable invite for this channel when permitted.")
    @app_commands.guild_only()
    async def invite(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            invite = await interaction.channel.create_invite(max_age=0, max_uses=0, unique=False, reason="Rosy /invite")
        except discord.HTTPException:
            await self._send(interaction, "I couldn't create an invite in this channel. You may need the Create Invite permission.", ephemeral=True)
            return
        await self._send(interaction, invite.url)


    async def _ai_task(self, interaction: discord.Interaction, instruction: str, text: str) -> None:
        await interaction.response.defer()
        try:
            result = await self.bot.conversation.generate(
                user_text=f"{instruction}\n\n{text}",
                user_id=interaction.user.id,
                guild_id=interaction.guild_id,
                channel_id=interaction.channel_id,
                is_dm=interaction.guild is None,
                personality_mode="friendly",
                user_name=interaction.user.display_name,
            )
            await interaction.followup.send(result.text[:1900] or "I couldn't produce a result.")
        except Exception as exc:
            await interaction.followup.send(safe_user_message(exc), ephemeral=True)

    @app_commands.command(name="ask", description="Ask Rosy a direct AI question.")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        await self._ai_task(interaction, "Answer the user's question accurately and clearly.", prompt)

    @app_commands.command(name="summarize", description="Summarize text into the key points.")
    async def summarize(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        await self._ai_task(interaction, "Summarize the following text into concise bullet points and preserve important facts.", text)

    @app_commands.command(name="explain", description="Explain a topic simply or technically.")
    async def explain(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer()
        await self._ai_task(interaction, "Explain this topic clearly. Start simple, then add technical detail only when useful.", topic)

    @app_commands.command(name="rewrite", description="Rewrite text in a cleaner style.")
    @app_commands.choices(style=[
        app_commands.Choice(name="Professional", value="professional"),
        app_commands.Choice(name="Friendly", value="friendly"),
        app_commands.Choice(name="Short", value="short"),
        app_commands.Choice(name="Formal", value="formal"),
    ])
    async def rewrite(self, interaction: discord.Interaction, text: str, style: app_commands.Choice[str] | None = None):
        await interaction.response.defer()
        chosen = style.value if style else "friendly"
        await self._ai_task(interaction, f"Rewrite the text in a {chosen} style. Return only the rewritten text.", text)

    @app_commands.command(name="brainstorm", description="Generate ideas around a topic.")
    async def brainstorm(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer()
        await self._ai_task(interaction, "Brainstorm 10 practical, distinct ideas for this topic. Number them.", topic)

    @app_commands.command(name="translate", description="Translate text to another language.")
    async def translate(self, interaction: discord.Interaction, text: str, language: str):
        await interaction.response.defer()
        await self._ai_task(interaction, f"Translate the following text into {language}. Preserve meaning and tone. Return only the translation.", text)

    @app_commands.command(name="proofread", description="Proofread text and return a corrected version.")
    async def proofread(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        await self._ai_task(interaction, "Proofread this text for grammar, spelling and clarity. Return the corrected version and do not invent facts.", text)

    @app_commands.command(name="code_review", description="Review a code snippet for bugs and security issues.")
    async def code_review(self, interaction: discord.Interaction, code: str):
        await interaction.response.defer()
        await self._ai_task(interaction, "Review this code for bugs, reliability and security issues. Do not execute it. Give concrete fixes.", code)

    @app_commands.command(name="regex_help", description="Explain or improve a regular expression.")
    async def regex_help(self, interaction: discord.Interaction, regex: str):
        await interaction.response.defer()
        await self._ai_task(interaction, "Explain this regular expression and suggest an improved version if appropriate.", regex)

    @app_commands.command(name="decision", description="Compare options and give a structured recommendation.")
    async def decision(self, interaction: discord.Interaction, options: str):
        await interaction.response.defer()
        await self._ai_task(interaction, "Compare these options using pros, cons, risks and a recommendation. Do not pretend to know missing facts.", options)

    @app_commands.command(name="outline", description="Create an outline for a project, article or presentation.")
    async def outline(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer()
        await self._ai_task(interaction, "Create a useful hierarchical outline with sections and subpoints.", topic)


async def setup(bot) -> None:
    await bot.add_cog(Features(bot))
