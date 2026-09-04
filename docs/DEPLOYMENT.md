# Deploying Rosy to Railway

Rosy is fully containerised. Railway builds the included `Dockerfile` and runs
the `rosy` command, which applies database migrations automatically on startup.

---

## 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

The `.gitignore` already prevents `.env`, tokens and secrets from being
committed.

## 2. Create the project on Railway

1. Go to [Railway.app](https://railway.app) and log in.
2. Click **New Project → Deploy from GitHub repo**.
3. Choose your repository and branch. Railway detects the `Dockerfile` via
   `railway.json` (builder = `DOCKERFILE`).

## 3. Add a PostgreSQL database

1. Click **+ New → Database → PostgreSQL**.
2. Railway provisions a Postgres instance and exposes a `$POSTGRES_URL`
   connection string (already `postgresql://…`).

## 4. Set the environment variables

In your service's **Variables** tab, add:

| Variable | Value |
|----------|-------|
| `DISCORD_TOKEN` | Your bot token (see `docs/DISCORD_SETUP.md`). |
| `DATABASE_URL` | `$POSTGRES_URL` (Railway can reference the variable, or paste the URL with `+asyncpg` added: `postgresql+asyncpg://…`). |
| `ENCRYPTION_KEY` | A 64-char hex key — generate with `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `OPENROUTER_API_KEY` | Your OpenRouter key. |

Mark `DISCORD_TOKEN`, `ENCRYPTION_KEY` and `OPENROUTER_API_KEY` as **locked**
(secret) in Railway.

### DATABASE_URL note

If you reference `$POSTGRES_URL`, note the driver: Rosy expects an async driver
(`postgresql+asyncpg://…`). `$POSTGRES_URL` is `postgresql://…`, which
SQLAlchemy will treat as `psycopg2` (sync) and fail. Either:
- set `DATABASE_URL = postgresql+asyncpg://${{POSTGRES_URL...}}` style, or
- simpler: copy the actual `$POSTGRES_URL` value and change the scheme prefix to
  `postgresql+asyncpg://`.

## 5. Deploy

- Railway auto-deploys on every push to the branch.
- On startup Rosy runs `alembic upgrade head`, then connects to Discord.
- Watch the **Deploy Logs** for `Rosy is online as …`.

## 6. Verify

In your Discord server:

- `!ping` → responds with latency.
- `!info` → shows provider/model/servers.
- Ask Rosy a question (mention or `@Rosy hello`).

---

## Moving to another host

Rosy only depends on environment variables, so moving hosts is straightforward:

- Set the same env vars on the new host.
- Provide a PostgreSQL database.
- Run `alembic upgrade head` (Rosy also does this on startup) and then `rosy`.

No code changes are required.

## Health check

The Dockerfile includes a `HEALTHCHECK` that verifies the `rosy` package imports
correctly. Discord bots do not expose an HTTP endpoint, so a web-based health
check is not applicable.
