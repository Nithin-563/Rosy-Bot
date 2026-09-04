# Setting up Rosy on the Discord Developer Portal

This guide walks through creating the Discord application, the bot, getting its
token, enabling intents, and generating an invite URL. Follow it exactly — the
bot will not function if the required intents are missing.

---

## 1. Create the application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application**.
3. Name it **Rosy** (or anything you like) and click **Create**.
4. (Optional) Fill in a description and a profile picture on the **General
   Information** tab.

## 2. Create the bot user

1. On the left, open the **Bot** tab.
2. Click **Add Bot** → confirm **Yes, do it!**.
3. A bot user is now created for your application.

## 3. Obtain the bot token

1. Still on the **Bot** tab, click **Reset Token** and confirm.
2. Copy the token — this is your `DISCORD_TOKEN`. Treat it like a password.
   Anyone with it can control your bot. Never share it or commit it to git.
3. If you lose it, reset it again to get a new one.

## 4. Enable the required intents

On the **Bot** tab, scroll to **Privileged Gateway Intents** and enable:

- **Message Content Intent** — required so Rosy can read what people send.
- **Server Members Intent** — required so Rosy can see member names and
  perform moderation reliably.

Toggle both **ON** and click **Save Changes**.

> These intents are required by the code (they are set in `rosy_bot.py`). If
> they are not enabled, Rosy will not receive message contents and will appear
> unable to talk or moderate.

## 5. Configure OAuth2 scopes & permissions (generate invite URL)

1. On the left, open **OAuth2 → URL Generator**.
2. Under **Scopes**, check:
   - `bot`
   - `applications.commands` (for future slash commands)
3. Under **Bot Permissions**, check a sensible set, e.g.:
   - `Send Messages`
   - `Read Messages / View Channels`
   - `Embed Links`
   - `Attach Files`
   - `Manage Messages` (moderation)
   - `Kick Members` and `Ban Members` (moderation)
   - `Manage Roles` (moderation)
   - `Use External Emojis`
4. Copy the generated URL at the bottom of the page.

## 6. Invite Rosy to your server

1. Open the invite URL in a browser.
2. Choose the server you want to add Rosy to.
3. Authorize. The bot will appear in the member list (offline until it starts).

---

## 7. Configure environment variables

Once Rosy is invited, set these in your environment (see `.env.example`):

| Variable | From |
|----------|------|
| `DISCORD_TOKEN` | The token you copied in step 3. |
| `DATABASE_URL` | A PostgreSQL connection string. |
| `ENCRYPTION_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `OPENROUTER_API_KEY` | Your key from [openrouter.ai](https://openrouter.ai). |

Never hard-code or share these values.
