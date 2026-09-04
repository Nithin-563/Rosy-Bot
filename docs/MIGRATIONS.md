# Database & migrations

Rosy uses **PostgreSQL** in production with SQLAlchemy 2.x async and Alembic.

## How migrations work

- The schema is defined by models in `rosy/db/models/` (the single source of
  truth).
- Alembic tracks versions in `migrations/versions/`.
- `alembic.ini` + `migrations/env.py` read the `DATABASE_URL` from your
  environment automatically — never hard-code it.

## Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration from model changes
alembic revision --autogenerate -m "add widget table"

# Roll back one step
alembic downgrade -1

# Show current revision
alembic current
```

## First boot fallback
`RosyBot.setup_hook()` runs `Base.metadata.create_all` as a safety net so the
bot can always boot even if migrations haven't been run. In production you
should rely on `alembic upgrade head` (the Dockerfile does this).

## Connection pooling
For PostgreSQL, the engine uses a size-10 pool (overflow 20) with
`pool_pre_ping=True` and a 30-minute recycle. Transactions are short-lived and
managed per-operation.

## Isolating data
Every table that is guild- or user-scoped carries `guild_id` / `owner_user_id`
columns, and all queries filter by those keys. DMs use `guild_id IS NULL`, so
DM data is never mixed with guild data.
