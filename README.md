# 🌹 Rosy - AI Discord Bot

A production-quality AI Discord bot with multi-server support, persistent memory, and modular architecture. Built with Python 3.12+, Discord.py, and PostgreSQL.

## ✨ Features

### Core Features
- **AI-Powered Conversations** - Chat with Rosy by mentioning her or using slash commands
- **Multi-Server Support** - Each server has its own configuration, memories, and settings
- **Persistent Memory** - Remembers important information about users and servers
- **Adaptive Personality** - Configurable personality that adapts to conversation context
- **Slash Commands** - Modern command interface with `/` commands

### AI Integration
- **OpenRouter Support** - Default provider with free model routing
- **Provider Abstraction** - Easy to add new AI providers (OpenAI, Anthropic, Gemini, etc.)
- **Conversation Context** - Maintains chat history and context

### Admin Features
- **Server Configuration** - Admins can configure personality, response length, humor level
- **Provider Management** - Set custom AI providers and API keys
- **Model Selection** - Choose different AI models per server

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL database
- Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)
- OpenRouter API key from [OpenRouter](https://openrouter.ai)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/rosy-bot.git
cd rosy-bot
```

2. **Install dependencies with uv**
```bash
uv sync
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Configure your `.env` file**
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
OPENROUTER_API_KEY=your_openrouter_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/rosy_bot
ENCRYPTION_SECRET=your_32_character_hex_secret
BOT_OWNER_ID=your_discord_user_id
```

5. **Run database migrations**
```bash
uv run alembic upgrade head
```

6. **Start the bot**
```bash
uv run python main.py
```

## 📁 Project Structure

```
rosy-bot/
├── bot/                 # Discord bot core
│   ├── client.py       # Main bot client
│   └── service.py      # Bot lifecycle service
├── ai/                  # AI integration
├── memory/              # Conversation and persistent memory
│   ├── manager.py      # Memory operations
│   └── context.py      # Context building
├── database/            # Database models and session
│   ├── models.py       # SQLAlchemy models
│   └── session.py      # Async session management
├── commands/            # Slash commands
│   ├── core.py         # Basic commands
│   ├── memory.py       # Memory commands
│   └── admin.py        # Admin commands
├── events/              # Discord event handlers
├── providers/           # AI provider abstraction
│   ├── base.py        # Provider interface
│   ├── openrouter.py   # OpenRouter implementation
│   └── factory.py      # Provider factory
├── services/            # Business logic services
├── utils/               # Utilities
│   ├── logging.py     # Structured logging
│   ├── encryption.py   # API key encryption
│   └── validation.py  # Input validation
├── config/              # Configuration management
├── alembic/             # Database migrations
└── main.py             # Entry point
```

## 🎮 Commands

### Basic Commands
| Command | Description |
|---------|-------------|
| `/ping` | Check if the bot is responding |
| `/help` | Get help with bot commands |
| `/about` | Learn about Rosy |

### Memory Commands
| Command | Description |
|---------|-------------|
| `/memory` | View your stored memories |
| `/clear_memory` | Clear history or memories |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/settings` | Configure bot settings |
| `/provider` | Manage AI provider |
| `/model` | Set AI model |

## 🛠️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Discord bot token |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key |
| `DATABASE_URL` | Auto | Railway provides automatically |
| `ENCRYPTION_SECRET` | No | Optional - for encrypting stored API keys |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `BOT_OWNER_ID` | No | Discord user ID of bot owner |

## 🚢 Deployment

### Railway (Recommended)

1. **Fork this repository** to your GitHub account

2. **Create a new Railway project**
   - Go to [Railway](https://railway.app) and sign in
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your forked repository

3. **Add PostgreSQL database**
   - In your Railway project, click "Add Plugin" → "PostgreSQL"
   - Railway will automatically set `DATABASE_URL` environment variable

4. **Add environment variables** in Railway Dashboard → Variables:
   ```
   DISCORD_BOT_TOKEN = your_discord_bot_token
   OPENROUTER_API_KEY = your_openrouter_api_key
   ```
   (Other variables are optional - Railway auto-detects settings)

5. **Deploy**
   - Railway will auto-detect Python and build automatically
   - Click "Deploy" to start

**Railway will automatically:**
- Detect Python from `pyproject.toml`
- Install dependencies from `uv.lock`
- Set up health checks from `railway.json`

### Railway Variables (Add in Dashboard)

**Important:** When you add PostgreSQL in Railway, it automatically creates a `DATABASE_URL` environment variable. Use that exact URL - do NOT change it!

| Variable | Required | Where to Get |
|----------|----------|--------------|
| `DISCORD_BOT_TOKEN` | Yes | Discord Developer Portal → Your App → Bot → Token |
| `OPENROUTER_API_KEY` | Yes | [openrouter.ai](https://openrouter.ai/keys) → Create API Key |
| `DATABASE_URL` | Auto | Railway provides this automatically when you add PostgreSQL plugin |
| `ENCRYPTION_SECRET` | No | Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |

**PostgreSQL Setup in Railway:**
1. In your Railway project → "Add Plugin" → "PostgreSQL"
2. Railway will automatically create `DATABASE_URL`
3. Copy that URL and paste it in your Variables section (or it should auto-populate)
4. The URL looks like: `postgres://user:password@host:port/database`

### Local Development

```bash
# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start the bot
uv run python main.py
```

## 🔒 Security

- API keys are encrypted before storage using Fernet encryption
- All user input is validated and sanitized
- Admin commands require Discord permissions
- Secrets are never logged or exposed

## 📝 Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## 🧪 Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=.
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Discord.py](https://discordpy.readthedocs.io/)
- AI powered by [OpenRouter](https://openrouter.ai/)
- Database powered by [PostgreSQL](https://www.postgresql.org/)

---

Made with ❤️ for Discord communities
