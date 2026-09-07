# Deployment

Rosy is containerized and ready for **Railway**. It runs from environment
variables only — nothing is hard-coded.

## Deploying to Railway

1. **Push the repo to GitHub.**
2. In [Railway](https://railway.app), click **New Project → Deploy from GitHub
   repo** and select this repository.
3. Add a **PostgreSQL** plugin:
   - Railway → your project → **New → Database → PostgreSQL**.
   - The plugin provides a `DATABASE_URL` connection string.
4. Under **Variables**, set at minimum:
   - `DISCORD_TOKEN` — your bot token
   - `OPENROUTER_API_KEY` — your OpenRouter key
   - `ENCRYPTION_KEY` — a strong random string
     (`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`)
   - `DATABASE_URL` — the Railway Postgres connection string. You can paste it
     **exactly as Railway provides it** (e.g. `postgresql://user:pass@host:5432/rosy`);
     Rosy auto-normalizes the sync `postgresql://` URL to the async `asyncpg`
     driver, so you don't need to edit it manually.
   - `LOG_LEVEL=INFO`
5. Railway builds the `Dockerfile` and runs:
   `alembic upgrade head && python -m rosy.main`
   which applies migrations and starts the bot.

### Ports
Rosy is a WebSocket/API *client*; it does not expose an HTTP server, so no
public port mapping is required on Railway.

## Moving to another host
Because all configuration is environmental, moving hosts is trivial:
- Point `DATABASE_URL` at any PostgreSQL instance.
- Provide the same environment variables.
- The Dockerfile works on any container platform (Fly.io, Render, ECS, …).

## Local development
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # fill in keys
alembic upgrade head
rosy
```
