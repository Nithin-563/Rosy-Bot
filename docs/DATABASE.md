# Rosy Database Schema & Migrations

Rosy uses **PostgreSQL** with **SQLAlchemy 2.x async** and **Alembic**
migrations. The ORM models live in `src/rosy/db/models.py`; migrations live in
`alembic/versions/`.

## Tables

| Table | Purpose |
|-------|---------|
| `guilds` | Per-server settings (personality, autonomous replies, AI provider/model). |
| `users` | Discord users (id, display name, preferences). |
| `channels` | Channel records and per-channel autonomous-reply flags. |
| `conversations` / `messages` | Conversation history for context. |
| `memories` | Scoped memory records (preference/fact/summary…). |
| `ai_providers` | Per-guild provider credentials (API key stored **encrypted**). |
| `usage_stats` | Token/request usage metrics. |
| `reminders` | User reminders (timezone-aware, persist across restarts). |
| `scheduled_tasks` | Recurring scheduled jobs. |
| `moderation_records` | Warnings/timeouts/kicks/bans history. |
| `custom_commands` | Guild-specific commands. |
| `knowledge` | Knowledge/learning records (future semantic search). |
| `guild_config` | Generic per-guild key/value settings. |

## Isolation

Guild-scoped tables are keyed by `guild_id`. DM data uses `guild_id = NULL`,
and memories carry a `scope` column (`dm` / `guild` / `user_guild`). All query
paths filter by the caller's scope, so no guild can read another's data.

## Snowflake ids (important)

Discord ids are 64-bit snowflakes. All snowflake columns are **BIGINT** on
PostgreSQL (a 32-bit INTEGER overflows and breaks every query). Migration
`b2f8c1a4d9e5` converts any columns created as INTEGER to BIGINT. The ORM uses a
`Snowflake = BigInteger().with_variant(Integer, "sqlite")` type so local SQLite
tests still get auto-incrementing primary keys.

## Applying migrations

```bash
# From the project root (Python 3.12+ with deps installed):
alembic upgrade head
```

Rosy also runs `alembic upgrade head` automatically on startup, so a fresh
deploy to Railway is migrated for you. Set `ROS_SKIP_MIGRATIONS=1` to disable
that behaviour if you manage migrations separately.

## Creating a new migration

After editing `src/rosy/db/models.py`:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Review the generated file under `alembic/versions/` before committing.

> Autogenerate against the S3-backed workspace filesystem can fail for SQLite
> (disk I/O). Point `DATABASE_URL` at a local or remote PostgreSQL instance (or
> a local-disk SQLite path) when generating migrations.
