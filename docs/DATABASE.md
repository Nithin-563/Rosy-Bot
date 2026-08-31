# Database & migrations

Rosy uses **PostgreSQL** in production via SQLAlchemy 2.x async (asyncpg).
For local testing without Postgres you can point `DATABASE_URL` at SQLite
(`sqlite+aiosqlite:///./rosy.db`).

## Schema

Core tables (defined in `src/rosy/models/__init__.py`):

| Table | Purpose |
|---|---|
| `guilds`, `users` | Discord servers & users |
| `guild_settings` | Per-guild AI/personality/autonomous config |
| `user_preferences` | Per-user timezone, model preference |
| `provider_credentials` | Encrypted per-guild AI API keys |
| `memories` | Scoped memories (dm / guild / user_in_guild) |
| `conversations`, `messages` | Conversation context & trimmed history |
| `usage` | AI token usage & latency metrics |
| `reminders` | Persistent scheduled reminders |
| `moderation_records` | warn/timeout/kick/ban history |
| `custom_commands` | Server-defined commands |
| `knowledge` | Optional learned knowledge |
| `plugin_config` | Per-plugin toggles |
| `personality_state` | Per-guild adaptive personality |

Every per-guild table carries `guild_id`; authorization is enforced in the
service layer to keep guilds isolated.

## Running migrations

```bash
# From a terminal with the app's environment:
alembic upgrade head      # apply all migrations
alembic revision --autogenerate -m "describe change"   # generate a new one
alembic downgrade base    # roll back
```

`alembic/env.py` reads the database URL from the `DATABASE_URL` environment
variable (or `ROS_DATABASE_URL`).

> **First deploy:** the bot also calls `create_all()` on startup, so a fresh
> host works even before you run `alembic upgrade head`.

## Backups

Use your host's Postgres tooling (Railway provides automatic backups for its
Postgres service).