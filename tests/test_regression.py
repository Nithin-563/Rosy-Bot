"""Regression tests for command syncing and persistent conversation memory.

Two production bugs are locked in here:
1. main.py used to override on_ready via @bot.event, which shadowed
   RosyBot.on_ready and meant sync_commands() never ran -> slash commands never
   registered. We assert main.py does NOT register an on_ready event handler.
2. The conversation store must replay prior messages into context so Rosy
   remembers across turns."""

import asyncio

from rosy.conversation.engine import ConversationEngine, extract_facts
from rosy.core.db import Database
from rosy.config import Settings
from rosy.conversation.store import ConversationStore


def _settings():
    return Settings(_env_file=None, discord_token="fake",
                    database_url="sqlite+aiosqlite:///:memory:")


def test_main_does_not_override_on_ready():
    import inspect

    import rosy.main as main_mod

    src = inspect.getsource(main_mod)
    # A @bot.event handler named on_ready would shadow RosyBot.on_ready and
    # prevent command syncing. It must NOT exist in main.py.
    if "@bot.event" in src:
        segment = src.split("@bot.event", 1)[1][:200]
        assert "on_ready" not in segment, "main.py must not override on_ready"
    # Our key line must be present: we hand the ready_event to the bot.
    assert "ready_event" in src


def test_extract_facts_captures_name_and_likes():
    facts = extract_facts("hi my name is Bob and i love python")
    joined = " ".join(facts)
    assert "name is Bob" in joined
    assert "likes python" in joined


def test_extract_facts_ignores_plain_chat():
    assert extract_facts("what is the weather today") == []


def test_conversation_memory_replays_prior_exchange():
    class FakeAI:
        def __init__(self):
            self.db = None
            self.calls = []

        async def chat(self, messages, **kw):
            self.calls.append(messages)
            return type("R", (), {
                "text": "replied", "provider": "fake", "model": "m",
                "usage": {}, "prompt_tokens": 0, "completion_tokens": 0,
            })()

    async def run():
        db = Database.from_settings(_settings())
        await db.create_all()
        ai = FakeAI()
        eng = ConversationEngine(_settings(), ai, None)
        eng.store = ConversationStore(db)
        await eng.generate(user_text="my name is Bob", user_id=7,
                           guild_id=1, channel_id=99, is_dm=False)
        await eng.generate(user_text="what is my name", user_id=7,
                           guild_id=1, channel_id=99, is_dm=False)
        body = [m.content for m in ai.calls[-1] if m.role == "user"]
        assert "my name is Bob" in body

    asyncio.run(run())