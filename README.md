# Rosy 🤖

Rosy is a **modular, production-quality AI Discord bot** built as an extensible
platform — not just a chatbot. She chats naturally, remembers things per
server/user, moderates, reminds you, plays games and music, answers in voice,
and can be configured entirely from Discord.

Built with Python 3.12+, `discord.py`, PostgreSQL, SQLAlchemy async, Alembic,
Pydantic, and OpenRouter by default.

---

## ✨ Features

| Area | What Rosy does |
|---|---|
| 💬 **Conversation** | Mentions, replies, name usage, autonomous replies, cooldowns |
| 🧠 **Memory** | Per-DM, per-guild, and user-in-guild memories with importance/expiry |
| 🎭 **Personality** | 11 adaptive tones (friendly, technical, supportive, humorous, …) |
| 🗂️ **Multi-server** | Strictly isolated settings, memories, and AI config per guild |
| 🔌 **AI providers** | OpenRouter (default), OpenAI, Gemini, Anthropic, Groq, Mistral + fallback |
| 🔐 **Security** | Encrypted API keys at rest, no secrets in logs, safe tool execution |
| 🌐 **Tools** | Safe math, time/date, web fetch, file text extraction |
| 🛡️ **Moderation** | warn, timeout, kick, ban, history, anti-flood |
| ⏰ **Reminders** | Persistent, timezone-aware, survive restarts |
| 🎮 **Games** | 8-ball, dice, trivia, guess-the-number |
| 🎵 **Music** | play / pause / resume / skip / stop / queue (yt-dlp + ffmpeg) |
| 🔊 **Voice** | join / leave voice channels |
| 🧩 **Custom commands** | Admins create server-specific commands (no arbitrary code) |
| ⚙️ **Admin** | Everything configured through Discord |

---

## 🚀 Quick start (local)

```bash
# 1. Python 3.11+ with a PostgreSQL (or SQLite) available
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[voice,web,pdf,dev]"

# 2. Configure
cp .env.example .env
# fill in DISCORD_TOKEN (and OPENROUTER_API_KEY)

# 3. Run database migrations (or let the bot auto-create tables)
alembic upgrade head
# — alternatively the bot runs create_all() on first start —

# 4. Start
python -m rosy.main
```

---

## 🛤️ Deploy to Railway

1. Push this repo to GitHub.
2. On Railway, click **New Project → Deploy from GitHub** and pick the repo.
3. Railway auto-detects the `Dockerfile`.
4. Add a **PostgreSQL** plugin/service to the project.
5. Set environment variables (see `.env.example` and the table below).
6. Deploy. Railway sends `DATABASE_URL` automatically; just add
   `ROS_DISCORD_TOKEN` and your AI key.

Railway's built-in liveness health check hits port `8080` (configurable via
`ROS_HEALTH_PORT`), which the bot serves.

---

## 🔑 Environment variables

All config uses the `ROS_` prefix. The only required ones are:

| Variable | Required | Description |
|---|---|---|
| `ROS_DISCORD_TOKEN` | ✅ | Discord bot token |
| `ROS_OPENROUTER_API_KEY` | ✅ (default AI) | OpenRouter API key |

PostgreSQL `DATABASE_URL` is injected by Railway. Everything else has sensible
defaults — see `.env.example` for the full list.

Never commit `.env`. Secrets are loaded from environment variables only.

---

## 📁 Project structure

```
src/rosy/
├── main.py            # entrypoint + health server
├── bot.py             # app container wiring all services
├── config.py          # pydantic-settings config
├── core/              # db, security, errors, rate limiting
├── models/            # SQLAlchemy ORM models (schema)
├── ai/                # provider abstraction + manager + fallback
├── conversation/      # engine, context builder, decision, personality
├── memory/            # scoped memory service
├── tools/             # safe tool framework + built-in tools
├── settings/          # per-guild settings service
├── moderation/        # moderation records + flood detection
├── reminders/         # persistent scheduler
├── cogs/              # Discord command/event layer
└── plugins/           # future plugin framework
alembic/               # database migrations
tests/                 # automated tests (no real API keys)
```

---

## 🧪 Tests

```bash
pytest
```

Tests mock external services and require **no real API keys**.

---

## 📚 Documentation

- [`docs/DISCORD_DEVELOPER_PORTAL.md`](docs/DISCORD_DEVELOPER_PORTAL.md) — create the bot, token, intents, invite
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Railway + other hosts
- [`docs/DATABASE.md`](docs/DATABASE.md) — schema & migrations
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) — common issues

---

## 🧩 Extending

Add a capability without touching the core:

- **New AI provider** → subclass `Provider` in `rosy/ai/providers.py`, register it.
- **New tool** → subclass `BaseTool` in `rosy/tools/`, register in the registry.
- **New command/event** → add a cog in `rosy/cogs/`.
- **New game** → add a method to the `Games` cog.

## License

MIT — see [`LICENSE`](LICENSE).
## OpenRouter model routing

Rosy now defaults to OpenRouter's **Free Models Router**:

```env
ROS_DEFAULT_PROVIDER=openrouter
ROS_DEFAULT_MODEL=openrouter/free
ROS_OPENROUTER_FREE_MODEL=openrouter/free
ROS_OPENROUTER_AUTO_MODEL=openrouter/auto
ROS_OPENROUTER_API_KEY=sk-or-v1-...
```

`openrouter/free` is the free-inference router and selects an available free model. `openrouter/auto` is OpenRouter's task-aware Auto Router; the router itself has no routing fee, but it can select a paid model, so it should not be treated as a free-inference setting. Choose `openrouter/auto` explicitly when you want that behavior.
