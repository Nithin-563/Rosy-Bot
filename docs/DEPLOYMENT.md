# Deployment

## Railway (recommended)

1. Push this repo to a GitHub repository.
2. In Railway, **New Project → Deploy from GitHub**, select the repo.
3. Railway reads `railway.json` and the `Dockerfile` automatically.
4. Add a **PostgreSQL** service (New → Database → PostgreSQL) to the project.
5. Go to the deployed service → **Variables** and add:
   - `ROS_DISCORD_TOKEN` — your bot token
   - `ROS_OPENROUTER_API_KEY` — your OpenRouter key
   - `ROS_ENCRYPTION_KEY` — a stable key (optional but recommended)
6. **Deploy**. Railway injects `DATABASE_URL` automatically.
7. Railway runs the health check against port `8080` (the bot serves `/`).

Slash commands register on startup. Check **Deployments** logs for `Logged in as
Rosy` to confirm a clean start.

## Other hosts

Because the project reads everything from env vars and runs via
`python -m rosy.main`, moving it is trivial:

- **Docker / Fly.io / Render / Heroku**: use the same `Dockerfile` (or the
  `CMD ["python", "-m", "rosy.main"]`), provide the same env vars and a
  PostgreSQL instance.
- **Systemd / bare metal**: `pip install .` then run
  `ROS_DISCORD_TOKEN=... python -m rosy.main`.

## Database migrations on a fresh host

On first start the bot auto-creates all tables (`create_all`). For formal
migrations run:

```bash
alembic upgrade head
```

## Generating an encryption key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set the output as `ROS_ENCRYPTION_KEY`. Keep it stable; changing it invalidates
previously stored provider credentials.