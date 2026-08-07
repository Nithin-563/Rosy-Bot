# Rosy Bot Setup Guide

This guide will walk you through setting up Rosy Discord Bot from scratch.

## Prerequisites

- Python 3.12 or higher
- PostgreSQL database (local or hosted)
- Discord account with a bot token
- OpenRouter API key

## Step 1: Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "Rosy")
3. Go to the "Bot" tab on the left sidebar
4. Click "Add Bot" to create a bot user
5. **Important**: Under "Privileged Gateway Intents", enable:
   - ✅ Message Content Intent
   - ✅ Server Members Intent
6. Copy the bot token (click "Reset Token" if needed)

## Step 2: Get OpenRouter API Key

1. Go to [OpenRouter](https://openrouter.ai)
2. Sign up or log in
3. Go to [Keys](https://openrouter.ai/keys)
4. Create a new API key
5. Copy the key (you won't be able to see it again)

## Step 3: Set Up PostgreSQL

### Option A: Local PostgreSQL

1. Install PostgreSQL on your machine
2. Create a database:
```sql
CREATE DATABASE rosy_bot;
CREATE USER rosy_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE rosy_bot TO rosy_user;
```

### Option B: Cloud PostgreSQL (Recommended for Production)

Use a hosted PostgreSQL service:
- [Neon](https://neon.tech) - Free tier available
- [Supabase](https://supabase.com) - Free tier available
- [Railway](https://railway.app) - Native PostgreSQL

## Step 4: Generate Encryption Secret

Run this command to generate a secure encryption key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output - you'll need it for the next step.

## Step 5: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your values:
```env
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
DATABASE_URL=postgresql://postgres:password@localhost:5432/rosy_bot
ENCRYPTION_SECRET=your_32_character_hex_secret_here

# Optional but recommended
BOT_OWNER_ID=your_discord_user_id_here
LOG_LEVEL=INFO
```

3. Get your Discord User ID:
   - Enable Developer Mode in Discord settings
   - Right-click on your username
   - Click "Copy User ID"

## Step 6: Install Dependencies

We use `uv` for dependency management:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

## Step 7: Run Database Migrations

```bash
uv run alembic upgrade head
```

This creates all the necessary database tables.

## Step 8: Invite the Bot to Your Server

1. Go to the Discord Developer Portal
2. Select your application
3. Go to "OAuth2" → "URL Generator"
4. Check these scopes:
   - ✅ bot
   - ✅ applications.commands
5. In "Bot Permissions", check:
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Use Slash Commands
   - (any other permissions you need)
6. Copy the generated URL
7. Paste it in your browser and authorize the bot

## Step 9: Start the Bot

```bash
uv run python main.py
```

You should see output like:
```
INFO - Starting Rosy Discord Bot
INFO - Database initialized successfully
INFO - Bot connected as Rosy#1234
INFO - Slash commands registered
INFO - Slash commands synced
```

## Step 10: Test the Bot

1. Go to any server where you invited the bot
2. Type `/ping` - you should get a response
3. Mention the bot (@Rosy) with a question
4. The bot should respond!

## Deployment on Railway

### Using Railway CLI

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login:
```bash
railway login
```

3. Initialize project:
```bash
railway init
```

4. Add PostgreSQL:
```bash
railway add
```

5. Set environment variables:
```bash
railway variables set DISCORD_BOT_TOKEN=your_token
railway variables set OPENROUTER_API_KEY=your_key
railway variables set DATABASE_URL=$DATABASE_URL
railway variables set ENCRYPTION_SECRET=your_secret
```

6. Deploy:
```bash
railway up
```

### Using Railway Dashboard

1. Create project on Railway
2. Add PostgreSQL plugin
3. Set environment variables in Variables tab
4. Deploy from GitHub

## Troubleshooting

### Bot won't connect
- Check your bot token is correct
- Ensure Message Content Intent is enabled
- Check your network/firewall

### Database connection errors
- Verify DATABASE_URL format
- Check database is running
- Verify credentials

### Commands not showing up
- Wait a few minutes for Discord to sync
- Try `/ping` to see if the bot responds to any command
- Check bot has proper permissions

### API errors
- Verify OpenRouter API key is valid
- Check your API key has credits
- Look at logs for specific error messages

## Getting Help

If you encounter issues:
1. Check the logs in the console
2. Verify all environment variables are set
3. Make sure migrations ran successfully
4. Open an issue on GitHub

## Next Steps

Once the bot is running:
1. Configure personality with `/settings personality friendly`
2. Set a custom model with `/model set openai/gpt-4`
3. Configure the AI provider with `/provider set openai your_api_key`
4. Add the bot to more servers!

Happy botting! 🌹
