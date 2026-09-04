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

- 🧠 **Conversation engine** — replies to mentions, replies, and her name; can
  join conversations autonomously when configured; cooldowns + rate limiting.
- 🎭 **Adaptive personality** — a stable core identity with 11 tone modes
  (friendly, technical, supportive, humorous, …) that adapt to context.
- 💾 **Memory system** — DM, guild, and user-in-guild scopes with strict
  isolation; `remember`, `forget`, `memories`, `clear-memory`.
- 🔌 **AI provider abstraction** — OpenRouter (default), OpenAI, Anthropic
  Claude, Gemini, Groq, Mistral, with per-guild override + fallback.
- 🧰 **Safe tool architecture** — calculator, date/time, web search, and memory
  tools; validated, time-limited, no arbitrary system access.
- 🏰 **Multi-server isolation** — every guild's data is fully separated; DMs are
  isolated from guild data.
- 🛡️ **Moderation** — warn / timeout / kick / ban / unban / purge with Discord
  permission checks and recorded history.
- ⏰ **Reminders & automation** — timezone-aware, DB-backed, survive restarts.
- 🎮 **Games** — trivia, magic 8-ball, dice.
- 📝 **Custom commands** — server-specific commands (admin-managed).
- 🎵 **Music** — play / pause / resume / skip / stop / queue / volume / loop.
- 🔊 **Voice** — join / leave voice channels with pluggable STT/TTS.
- 📄 **Files & documents** — summarize attached text/PDFs via the AI provider.
- 🔒 **Security** — encrypted stored credentials, permission checks, rate
  limiting, guild isolation, no secrets in logs.
- 🧪 **Tests** — unit + async tests that mock external services (no real keys).

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

MIT — see [LICENSE](LICENSE).
