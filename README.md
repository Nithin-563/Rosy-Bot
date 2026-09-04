# Rosy 🤖

**Rosy** is a production-quality, modular AI Discord bot built in Python. She's
not just a chatbot — she's an extensible platform whose primary interface is
Discord. She can chat naturally, remember things, remind you, moderate your
server, run games, and use tools like web search and math — all isolated
per-server, deployable to Railway with a single Docker build.

> Rosy uses the official Discord **Bot API** (created via the Discord Developer
> Portal). It is **not** a self-bot and never automates a normal user account.

---

## ✨ Features

- **Natural conversation engine** — replies to mentions, replies-to-Rosy, and
  your name; optionally joins conversations autonomously (with cooldowns and
  spam protection).
- **Adaptive personality** — a stable core identity that shifts tone based on
  context (friendly, casual, technical, supportive, playful…). She is always
  honest that she is an AI.
- **Memory system** — remembers preferences and facts, with full isolation
  between servers, DMs, and user-in-guild. `!remember`, `!forget`,
  `!whatdoyouremember`, `!clearmymemories`.
- **Multi-provider AI** — OpenRouter by default, plus OpenAI, Gemini, Anthropic,
  Groq and Mistral. Provider and model are configurable per server.
- **Safe tools** — deterministic math, web search. Tool-calling architecture
  with permission gating and validation.
- **Moderation** — `!warn`, `!timeout`, `!kick`, `!ban`, `!modhistory`, with
  persistent records. Rosy never bypasses Discord permissions.
- **Reminders** — `!remindme 30m …`, persisted in PostgreSQL, survive restarts.
- **Custom commands** — admins create server commands (text or AI-powered).
- **Games** — `!roll`, `!8ball`, `!flip`, `!trivia`.
- **Per-guild admin** — `!setpersonality`, `!autonomous`, `!setmodel`,
  `!guildsettings` (requires `Manage Server` permission).

## 🏗️ Architecture

Clean, layered separation (no giant files):

```
Discord Layer  ── cogs (general, admin, memory, moderation, reminders,
                   custom_commands, fun)
      │
Event/Command Layer ── RosyBot (on_message decision engine)
      │
Conversation & Service Layer ── engine, context builder, personality,
                                moderation, reminders
      │
AI / Tool Layer ── provider abstraction (OpenRouter, OpenAI, Gemini…),
                   tool registry
      │
Memory / Knowledge Layer ── memory service (scoped & isolated)
      │
Database Layer ── SQLAlchemy 2.x async, Alembic, PostgreSQL
```

```
src/rosy/
├── main.py                # entry point (runs migrations, starts bot)
├── config.py              # pydantic-settings env config
├── logging_config.py      # structured logging
├── bot/rosy_bot.py        # bot wiring + response decision
├── ai/                    # provider abstraction & manager
│   └── providers/         # OpenRouter, OpenAI, Gemini, Anthropic, Groq, Mistral
├── conversation/          # engine, context builder, personality
├── memory/service.py      # scoped memory storage
├── tools/                 # tool base, registry, math, web
├── services/              # moderation, reminders
├── db/                    # models, session, encryption
└── cogs/                  # Discord command modules
```

## 🧱 Tech Stack

- **Python 3.12+**
- **discord.py** 2.3+ (official Discord API)
- **PostgreSQL** + **SQLAlchemy 2.x async** + **asyncpg**
- **Alembic** migrations
- **pydantic / pydantic-settings**
- **httpx** async HTTP client
- **cryptography** (Fernet) for encrypting stored API keys
- **APScheduler**-style background loops for reminders
- **pytest / pytest-asyncio** for testing

---

## 🚀 Quick Start (local)

1. **Clone and install**

   ```bash
   git clone <your-repo-url> && cd rosy
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Create your bot on Discord** — see [DISCORD_SETUP.md](docs/DISCORD_SETUP.md).

3. **Configure environment**

   ```bash
   cp .env.example .env
   # Fill in DISCORD_TOKEN, DATABASE_URL, ENCRYPTION_KEY, OPENROUTER_API_KEY
   ```

   Generate an encryption key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. **Run the database migrations**

   ```bash
   alembic upgrade head
   ```

5. **Run Rosy**

   ```bash
   rosy
   ```

---

## ☁️ Deploy to Railway

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full walkthrough. Short version:

1. Push this repo to GitHub.
2. On Railway, **New Project → Deploy from GitHub repo**.
3. Add a **PostgreSQL** plugin and attach it.
4. Set the required **environment variables** (below) in the service.
5. Deploy — Railway uses the included `Dockerfile` and runs `rosy`, which
   applies migrations automatically on startup.

### Required environment variables

| Variable | Purpose |
|----------|---------|
| `DISCORD_TOKEN` | Your bot token (secret). |
| `DATABASE_URL` | SQLAlchemy async URL (Railway sets `$POSTGRES_URL`). |
| `ENCRYPTION_KEY` | 64-hex key used to encrypt stored credentials (secret). |
| `OPENROUTER_API_KEY` | OpenRouter key for AI responses (secret). |

Optional: `OPENROUTER_MODEL`, provider keys/models, `ROS_PERSONALITY`,
`ROS_AUTONOMOUS_REPLIES`, `LOG_LEVEL`, and more — see `.env.example`.

> ⚠️ **Never commit a real `.env` or real tokens.** The `.gitignore` already
> excludes them.

---

## 🧪 Tests

Run the full suite (no real API keys needed — external services are mocked):

```bash
pytest -q
```

Tests cover config, encryption, tools, personality, the conversation engine,
memory + guild/DM isolation, moderation, reminders, the AI manager, and the
context builder.

## 🗄️ Database Migrations

- Migrations live in `alembic/versions/`. Apply: `alembic upgrade head`.
- Create a new migration after model changes:
  `alembic revision --autogenerate -m "description"`.
- See [docs/DATABASE.md](docs/DATABASE.md).

## 📚 Docs

- [DISCORD_SETUP.md](docs/DISCORD_SETUP.md) — create the app, bot, token, intents, invite URL.
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — Railway deployment.
- [DATABASE.md](docs/DATABASE.md) — schema & migration notes.
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — common issues.

## 🔒 Security

- Secrets are never hard-coded or logged.
- Stored API keys are encrypted with Fernet.
- Memory/data are isolated per guild — no cross-guild leakage.
- Custom commands and tools can **never** execute arbitrary code.
- Moderation respects Discord's permission system.

## 📄 License

[MIT](LICENSE)
