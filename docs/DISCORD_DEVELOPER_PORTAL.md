# Setting up the Discord application & bot

Rosy is an **official Discord bot** using Discord's supported Bot API. Follow
these steps to create it, get its token, and invite it to your server. **Do not
automate a normal user account (self-bot)** — that violates Discord's ToS.

## 1. Create the application

1. Go to <https://discord.com/developers/applications>.
2. Click **New Application**, name it **Rosy**, and create it.

## 2. Create the bot

1. Open your application → **Bot** tab (left sidebar).
2. Click **Add Bot** → **Yes, do it!**.
3. Under **Privileged Gateway Intents**, enable:
   - **Message Content Intent** — required for Rosy to read messages.
   - **Server Members Intent** — required for member-based features.
   - (Voice State Intent is enabled by default.)
4. Copy the **Token** (click **Reset** if not shown). This is your
   `ROS_DISCORD_TOKEN`. **Treat it as a secret — never commit it.**

> Only enable the intents Rosy needs. The bot itself already requests only the
> intents enabled in your env config (`ROS_ENABLE_*`), so keep the portal
> settings aligned.

## 3. Enable the OAuth2 scopes & permissions

1. Open the **OAuth2 → General** tab. Add the **bot** scope.
2. Open **OAuth2 → URL Generator** (or use the tab). Select:
   - Scopes: `bot`, `applications.commands`
   - Bot permissions (recommended set):
     - `Send Messages`, `Send Messages in Threads`
     - `Read Message History`, `View Channels`
     - `Embed Links`, `Attach Files`, `Add Reactions`
     - `Manage Messages`, `Moderate Members`, `Kick Members`, `Ban Members`
       (moderation — optional, grant only if you want those features)
     - `Connect`, `Speak` (voice/music — optional)
3. Copy the generated **invite URL**.

## 4. Invite Rosy

1. Open the invite URL in a browser.
2. Pick a server, and click **Authorize**.
3. Rosy joins the server. Verify she appears in the member list.

## 5. Configure the bot

Set the environment variables (see README / `.env.example`). At minimum:

- `ROS_DISCORD_TOKEN` = the bot token
- `ROS_OPENROUTER_API_KEY` = your OpenRouter key (default AI provider)

Then start the bot (locally or on Railway). Slash commands are registered
automatically on startup.

> **Troubleshooting:** If slash commands don't appear, wait a few seconds for
> Discord to register them, or restart the bot. If you only test in one server,
> set `ROS_DEV_GUILD_IDS` to that guild's ID for instant registration.