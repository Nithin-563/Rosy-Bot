# Troubleshooting

## The bot doesn't come online
- **Missing token**: confirm `ROS_DISCORD_TOKEN` is set. Check deploy logs for
  a token-related error.
- **Wrong gateway URL / corporate network**: some networks block Discord's
  WebSocket gateway. Allow `gateway.discord.gg` and `discord.com`.

## Slash commands don't appear
- Wait a few seconds after startup for command registration.
- Restart the bot. For instant registration in one server, set
  `ROS_DEV_GUILD_IDS` to that guild's ID.
- Make sure the bot has the `applications.commands` OAuth scope and permission
  to create commands in the server.

## AI replies say "not configured"
- Set the AI key: `ROS_OPENROUTER_API_KEY` (or another provider's key), then
  restart.
- If you set a per-guild provider in `/set_provider` without storing a key,
  Rosy falls back to the default provider — check `ROS_DEFAULT_PROVIDER`.

## Memory/reminders don't persist across restarts
- They're stored in PostgreSQL. Confirm `DATABASE_URL` is set and reachable.
- If you didn't set `ROS_ENCRYPTION_KEY`, stored provider credentials are
  encrypted with an ephemeral key and do **not** survive restarts — set a
  stable key (see Deployment docs).

## Music doesn't play
- The `voice`/`yt-dlp` extra and `ffmpeg` must be installed. In the Docker
  image they are bundled. Chat, games, and tools still work without them.
- Make sure the bot has the **Connect** and **Speak** permissions.

## Everything else
- Enable verbose logs: `ROS_LOG_LEVEL=DEBUG`.
- Check the **Deployments** logs. If you still need help, share the logs with
  the platform (avoid posting bot tokens or API keys).