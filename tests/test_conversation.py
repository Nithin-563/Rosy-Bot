"""Context builder + response decision tests."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rosy.ai.base import Message
from rosy.conversation.context import ContextBuilder
from rosy.conversation.decision import DecisionInput, ResponseDecider


def test_context_builds_system_and_history():
    cb = ContextBuilder()
    ctx = cb.build(
        mode="technical",
        recent_messages=[Message(role="user", content="hello"), Message(role="assistant", content="hi")],
        memories=["user likes rust"],
    )
    assert ctx.messages[0].role == "system"
    roles = [m.role for m in ctx.messages]
    assert "user" in roles and "assistant" in roles
    assert any("rust" in m.content for m in ctx.messages)


def test_context_respects_budget():
    cb = ContextBuilder()
    many = [Message(role="user", content="x" * 500) for _ in range(50)]
    ctx = cb.build(recent_messages=many)
    # Budget is bounded well below all 50 messages.
    assert ctx.estimated_tokens() <= 6000 + 100


def test_decision_triggers():
    d = ResponseDecider()
    assert d.decide(DecisionInput(mentions_bot=True)).should_reply is True
    assert d.decide(DecisionInput(is_dm=True)).should_reply is True
    assert d.decide(DecisionInput(is_reply_to_bot=True)).should_reply is True
    assert d.decide(DecisionInput(content="hey Rosy how are you")).should_reply is True


def test_decision_silence():
    d = ResponseDecider()
    assert d.decide(DecisionInput(content="hello there")).should_reply is False
    assert d.decide(DecisionInput(content="hi", autonomous=False)).should_reply is False
    assert d.decide(DecisionInput(rate_limited=True, is_dm=True)).should_reply is False
    assert d.decide(DecisionInput(channel_ai_enabled=False, is_dm=True)).should_reply is False


def test_decision_cooldown():
    d = ResponseDecider()
    assert d.decide(DecisionInput(content="hi", autonomous=True, cooldown_active=True)).should_reply is False


def test_decision_autonomous_recent():
    d = ResponseDecider()
    recent = datetime.now(timezone.utc) - timedelta(seconds=30)
    assert d.decide(DecisionInput(content="how's it going", autonomous=True, last_participation=recent)).should_reply is True
