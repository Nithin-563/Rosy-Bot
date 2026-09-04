# Troubleshooting

## Bot is online but doesn't reply to messages
- **Missing Message Content Intent.** Enable it in the Developer Portal
  (Bot → Privileged Gateway Intents → Message Content Intent), then re-invite
  the bot.
- **Command prefix conflict.** Rosy ignores anything starting with `!` as a
  command. To chat, **mention** Rosy, **reply** to her, or say her name.

## "All providers failed" / AI errors
- Check `OPENROUTER_API_KEY` is set and valid.
- Check the model name in `OPENROUTER_DEFAULT_MODEL`.
- Check you have credits/allowance on OpenRouter.
- Look at the logs (enable `LOG_LEVEL=DEBUG`) — provider errors are logged.

## Database connection errors
- Ensure `DATABASE_URL` is the **async** form:
  `postgresql+asyncpg://user:pass@host:5432/rosy`
- Ensure the database is reachable from the host and migrations have run
  (`alembic upgrade head`).

## "ENCRYPTION_KEY is not configured"
- Set `ENCRYPTION_KEY` to a strong random string.
- **Important:** if you change it later, previously stored encrypted
  credentials cannot be decrypted. Generate once and keep it stable.

## Music says "Provide a direct audio URL"
- The optional `yt-dlp` extra is not installed, so search/YouTube lookup is
  unavailable. Either `pip install yt-dlp` (add to the image) or play a direct
  `.mp3`/audio URL.
- `ffmpeg` must be present on the host (the Dockerfile installs it).

## Voice says "Voice/TTS is not configured"
- Voice transport works (join/leave), but no TTS provider is wired by default.
  Implement a `TTSProvider` and pass it to `VoiceManager`.

## Redis of the whole project
If something else is broken, enable debug logging and check the startup logs.
Most failures are configuration (env vars), not code.

## Getting help
Open an issue on the repository with the **redacted** logs (never paste tokens
or API keys).
