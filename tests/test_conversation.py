"""Decision engine and context builder tests."""

from __future__ import annotations

from rosy.config import Settings
from rosy.conversation.decision import DecisionEngine, DecisionInput
from rosy.conversation.context import Context, ContextBuilder
from rosy.ai.base import ChatMessage


def _decision(**kw):
    base = dict(bot_id=1, author_id=2, content="hi", is_dm=False)
    base.update(kw)
    return DecisionEngine().should_respond(DecisionInput(**base))


def test_never_respond_to_bots():
    assert _decision(is_bot=True).should is False


def test_always_respond_dm():
    assert _decision(is_dm=True).should is True


def test_mention_triggers():
    assert _decision(mentions_me=True).should is True


def test_name_usage_triggers():
    assert _decision(content="rosy, what's up").should is True


def test_autonomous_disabled():
    assert _decision(autonomous_enabled=False).should is False


def test_cooldown_blocks_autonomous():
    d = _decision(last_response_at=1e18)
    assert d.reason == "cooldown"


def test_autonomous_not_triggered_by_default():
    # probability 0 -> never autonomous unless explicitly mentioned
    d = _decision(content="just talking about weather", autonomous_probability=0.0)
    assert d.should is False


def test_context_builder_system_and_messages():
    settings = Settings(_env_file=None, discord_token="x", database_url="sqlite+aiosqlite://")
    cb = ContextBuilder(settings)
    ctx = Context(
        guild_name="Test Guild",
        user_name="Alice",
        personality_mode="friendly",
        history=[ChatMessage(role="user", content="hi")],
        memories=[],
    )
    msgs = cb.build_messages(ctx)
    assert msgs[0].role == "system"
    assert "Test Guild" in msgs[0].content
    assert "Alice" in msgs[0].content
    assert msgs[-1].content == "hi"