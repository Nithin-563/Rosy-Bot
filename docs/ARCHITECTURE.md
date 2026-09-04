# Architecture notes

Rosy is an **AI platform whose primary interface is Discord**. The design goal
is extensibility: adding a capability must not require rewriting the app.

## Layers
```
Discord layer            rosy/cogs/            commands + listeners
Event/Command layer      rosy/bot.py           composition root, dispatch
Conversation & Services  rosy/conversation/, rosy/reminders/, rosy/moderation/...
AI/Tool layer            rosy/ai/, rosy/tools/ provider + tool abstraction
Memory/Knowledge layer   rosy/memory/, rosy/knowledge/
Database layer           rosy/db/, rosy/migrations/
```

## Key abstractions

### AI provider
`BaseProvider` defines `complete(messages, tools, ...) -> ChatResponse`.
- `OpenAICompatProvider` handles OpenRouter, OpenAI, Groq, Mistral, and Gemini
  (same wire format).
- `AnthropicProvider` handles Claude's native API.
- `ProviderRouter` resolves the active provider per guild, caches instances,
  and fails over across providers.

### Tools
`BaseTool` exposes `name`, `description`, `parameters` (JSON Schema), and
`run(arguments, context)`. `ToolRegistry` validates names, executes within
timeouts, and catches errors so a failing tool never crashes the loop.
Deterministic operations (calculator, dates) use deterministic code — not LLM
guessing.

### Memory isolation
`MemoryKey(scope, owner_user_id, guild_id)` determines visibility:
- `dm`: owner only, no guild
- `guild`: guild-wide
- `user_in_guild`: a specific user within a guild

All queries filter by the full key, so one guild can never read another's
memory.

### Response decision
`ResponseDecider` gates every potential reply by mention / reply-to-bot / name /
DM / autonomous participation, plus cooldowns and rate limits. Rosy does not
reply to everything.

## Reliability & security
- All network I/O is async; the event loop is never blocked.
- Exponential-backoff-ish behavior via retries only where appropriate; no retry
  storms (provider fallback is a bounded list).
- Credentials are encrypted at rest with a Fernet key derived from
  `ENCRYPTION_KEY`.
- No secrets in logs; errors shown to Discord users are sanitized (no stack
  traces).
- Tools are validated before execution; there is no arbitrary shell execution.

## Adding a feature
1. Add a service under its own package (e.g. `rosy/wikipedia/`).
2. Expose it on `RosyBot` in `rosy/bot.py`.
3. Add a cog under `rosy/cogs/` and register it in `rosy/cogs/__init__.py`.
4. Add tests in `tests/`.
