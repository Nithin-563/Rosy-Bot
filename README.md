# Rosy 🤖

**Rosy is a modular, production-grade AI Discord bot built as an extensible AI
platform — not a simple chatbot.**

Rosy runs on [OpenRouter](https://openrouter.ai) by default (bring your own key),
supports many AI providers, uses **PostgreSQL** for durable state, and is ready
to deploy to **Railway** with a single click.

> Everything is configured through **environment variables**. No hard-coded
> secrets anywhere. See [`.env.example`](.env.example).

---

## ✨ Features

| Area | What Rosy does |
|---|---|
| 💬 **Conversation** | Mentions, replies, name usage, autonomous replies, cooldowns, rate limiting |
| 🧠 **Memory** | Per-DM, per-guild, and user-in-guild memories with importance/expiry; `remember`, `forget`, `memories` |
| 🎭 **Personality** | 11 adaptive tones (friendly, technical, supportive, humorous, …) — stable core identity with modes |
| 🗂️ **Multi-server** | Strictly isolated settings, memories, and AI config per guild; DMs are isolated |
| 🔌 **AI providers** | OpenRouter (default), OpenAI, Gemini, Anthropic, Groq, Mistral + per-guild override & fallback |
| 🔐 **Security** | Encrypted API keys at rest, permission checks, rate limiting, no secrets in logs, safe tool execution |
| 🌐 **Tools** | Safe math/time, public web search + fetch, bounded tool calls with SSRF/prompt-injection hardening |
| 🛡️ **Moderation** | warn, timeout, kick, ban, unban, purge, history, anti-flood |
| ⏰ **Reminders** | Persistent, timezone-aware, survive restarts |
| 🎮 **Games** | 8-ball, dice, trivia, guess-the-number |
| 🎵 **Music** | play / pause / resume / skip / stop / queue / volume / loop (yt-dlp + ffmpeg) |
| 🔊 **Voice** | join / leave, pluggable STT/TTS, TTS speech, AI voice-chat responses (optional Edge TTS) |
| 🧩 **Custom commands** | Admins create server-specific commands (no arbitrary code) |
| ⚙️ **Admin** | Everything configured through Discord; backend model IDs are never shown to users |
| 🧰 **Utilities** | 75 slash commands for weather, polls, encoding, hashing, randomization, server/user info and more |
| 📄 **Files & documents** | Summarize attached text/PDFs via the AI provider |
| 🧪 **Tests** | Unit + async tests that mock external services (no real keys) |
| 🔐 **AI boundary** | AI cannot execute shell/filesystem/database/moderation/destructive actions; only allowlisted safe tools are callable |

---

## 🏗 Architecture

Rosy is built in clean layers so new capabilities don't require rewrites:

```
Discord layer  (cogs)
   ↓
Event / Command layer
   ↓
Conversation & Service layer
   ↓
AI / Tool layer
   ↓
Memory / Knowledge layer
   ↓
Database layer (PostgreSQL + SQLAlchemy async + Alembic)
```

```
rosy/
├── bot.py              # composition root — wires all services + cogs
├── main.py             # entry point
├── config.py           # pydantic-settings, all env config
├── cogs/               # Discord commands & event handlers
├── ai/                 # provider abstraction (OpenRouter, OpenAI, Claude, …)
├── conversation/       # engine, context builder, response decision
├── personality/        # adaptive tone engine
├── memory/             # memory service + scopes
├── tools/              # safe tool framework + built-in tools
├── security/           # crypto, rate limiting, permissions
├── voice/  music/      # voice & music subsystems
├── moderation/         # moderation service
├── reminders/          # scheduled reminders
├── knowledge/          # guild-isolated knowledge store
├── games/              # trivia, 8-ball, dice
├── custom_commands/    # server-specific commands
├── db/                 # SQLAlchemy async engine + models
└── migrations/         # Alembic migrations
```

---

## 🚀 Quickstart (local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env       # fill in DISCORD_TOKEN and OPENROUTER_API_KEY
alembic upgrade head       # create the schema
rosy                       # run the bot
```

---

## 🖥 Deploy to Railway

1. Push this repository to GitHub.
2. In Railway, **New Project → Deploy from GitHub repo**.
3. Add a **PostgreSQL** plugin.
4. Set the environment variables from [`.env.example`](.env.example)
   (`DISCORD_TOKEN`, `OPENROUTER_API_KEY`, `ENCRYPTION_KEY`, `DATABASE_URL`).
5. Railway reads the `Dockerfile` and runs `alembic upgrade head && rosy`.

The `Dockerfile` uses a healthcheck and runs the DB migration before starting
the bot. Moving to another host later is just a matter of pointing
`DATABASE_URL` at any PostgreSQL instance.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [docs/DISCORD_PORTAL.md](docs/DISCORD_PORTAL.md).

---

## 🔑 Required environment variables

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Discord bot token (from the Developer Portal) |
| `OPENROUTER_API_KEY` | OpenRouter API key (default AI provider) |
| `ENCRYPTION_KEY` | Strong random string used to encrypt stored credentials |
| `DATABASE_URL` | e.g. `postgresql+asyncpg://user:pass@host:5432/rosy` |

All optional variables are documented in [`.env.example`](.env.example).

---

## 🧪 Tests

```bash
pytest -q
```

Tests use SQLite in-memory and mock HTTP; **no real API keys required**.

---

## 📚 Documentation

- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Railway + other hosts
- [`docs/DISCORD_PORTAL.md`](docs/DISCORD_PORTAL.md) — create the bot, intents, invite
- [`docs/MIGRATIONS.md`](docs/MIGRATIONS.md) — database migrations
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) — common issues
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — deeper design notes

---

## ⚖️ License

Add a capability without touching the core:

- **New AI provider** → subclass `Provider` in `rosy/ai/providers.py`, register it.
- **New tool** → subclass `BaseTool` in `rosy/tools/`, register in the registry.
- **New command/event** → add a cog in `rosy/cogs/`.
- **New game** → add a method to the `Games` cog.

## License

MIT — see [`LICENSE`](LICENSE).

### Command discovery

Rosy now syncs the live command tree after every startup. The launcher no longer overrides the bot `on_ready` event, so command synchronization actually runs. For instant development updates, `ROS_SYNC_ALL_GUILD_COMMANDS=true` copies the global command set into every current guild; set it to `false` and use `ROS_DEV_GUILD_IDS` when operating at larger scale.

### Security model

AI tool calls are allowlisted. The AI can use safe calculation, time, public web search/fetch and explicitly provided file extraction; tools cannot access the shell, arbitrary filesystem paths, secrets, database credentials or destructive Discord actions. Tool results are treated as untrusted data, and public web requests reject local/private targets and redirects.
