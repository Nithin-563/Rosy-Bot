# Discord Developer Portal setup

Follow these steps exactly to create Rosy as an official Discord bot.

## 1. Create the application
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application**, name it **Rosy**, and create it.
3. (Optional) Add an icon and a description on the **General Information** page.

## 2. Create the bot user
1. Open the **Bot** tab on the left.
2. Click **Add Bot** → confirm **Yes, do it!**.
3. Click **Reset Token** and copy the token. Keep it secret — this is your
   `DISCORD_TOKEN`.

## 3. Enable the required intents (IMPORTANT)
Rosy reads message content and member data, which require privileged intents:
- Under **Bot → Privileged Gateway Intents**, enable:
  - ✅ **Message Content Intent** *(required for AI responses to message text)*
  - ✅ **Server Members Intent** *(required for moderation/member lookups)*
- **Presence Intent** is not required.

Without the Message Content Intent, the bot cannot see what users type.

## 4. Configure permissions
Under **Bot → Authorization Flow**, ensure **Require OAuth2 Code Grant** is
**OFF**. In **Bot Permissions** select:
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Add Reactions
- Manage Messages (moderation)
- Kick Members, Ban Members (moderation)
- Moderate Members / Timeout
- Connect, Speak, Use Voice Activity (voice/music)
- Use Slash Commands (if you later enable them)

## 5. Generate the invite URL
1. Open the **OAuth2 → URL Generator** page.
2. Under **Scopes**, check **bot** (and **applications.commands** if you want
   slash commands).
3. Under **Bot Permissions**, select the same permissions as above.
4. Copy the generated URL at the bottom and open it in a browser.

## 6. Invite Rosy to a server
1. Open the invite URL and choose a server where you have **Manage Server**.
2. Click **Authorize** (and optionally verify you're human).
3. Rosy appears in the member list.

## 7. Configure environment variables
Set these on your host (see `.env.example`):
- `DISCORD_TOKEN` — the token from step 2.
- `OPENROUTER_API_KEY` — from [OpenRouter](https://openrouter.ai).
- `ENCRYPTION_KEY` — a strong random string.
- `DATABASE_URL` — your PostgreSQL connection.

## 8. Verify
In a channel, send `!ping`. Rosy should reply with her latency. If not, check
the bot is online and that the Message Content Intent is enabled.
