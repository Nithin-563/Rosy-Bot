# Troubleshooting Rosy

## Bot won't start: "DISCORD_TOKEN is not set"

Set `DISCORD_TOKEN` in your environment (`.env` or Railway variables). See
`docs/DISCORD_SETUP.md`.

## Bot logs in but doesn't reply / can't read messages

The **Message Content Intent** is probably disabled. In the Discord Developer
Portal → your app → **Bot** → **Privileged Gateway Intents**, enable **Message
Content Intent** (and **Server Members Intent** for moderation). Then redeploy.

## "DATABASE_URL ... psycopg2 ... not installed" error

Rosy expects an async driver URL: `postgresql+asyncpg://…`. A plain
`postgresql://…` URL (like the raw `$POSTGRES_URL`) resolves to the sync
`psycopg2` driver, which isn't installed. Change the scheme to
`postgresql+asyncpg://…`. See `docs/DEPLOYMENT.md`.

## Migrations fail on startup

- Confirm the database is reachable and `DATABASE_URL` is correct.
- Run `alembic upgrade head` manually and check the error.
- If you manage migrations yourself, set `ROS_SKIP_MIGRATIONS=1`.

## "ENCRYPTION_KEY is not configured" when storing credentials

Set `ENCRYPTION_KEY` (a 64-char hex string). Keep it **stable** — changing it
after storing credentials makes the old ones unreadable.

## AI requests fail / no replies from the LLM

- Check `OPENROUTER_API_KEY` is set and valid.
- Confirm the provider/model in `.env` or `!setmodel` is valid for your key.
- Watch the logs for the HTTP status returned by the provider.

## Bot ignores messages but `!ping` works

Autonomous replies are off by default. To have Rosy reply without a mention,
an admin should run `!autonomous on`. She always answers direct mentions,
replies-to-her, and messages containing "Rosy".

## Moderation commands error with "permission"

The commands require the appropriate Discord permissions *for the command user*
(e.g. `Manage Messages`, `Ban Members`). Ensure the bot also has the matching
permissions in the server. Rosy never bypasses Discord's permission system.

## Rate limiting / spam

Rosy applies a per-channel cooldown between autonomous replies. If you want
less/more frequent autonomous chat, adjust the personality/cooldown or turn
autonomous replies off.

## Still stuck?

Enable debug logging by setting `LOG_LEVEL=DEBUG` and share the (non-secret)
log output. Never share your tokens or API keys.
