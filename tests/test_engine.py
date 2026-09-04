"""Conversation engine: response-decision tests."""

from rosy.ai.manager import AIProviderManager
from rosy.conversation.engine import ConversationEngine
from rosy.conversation.personality import Personality


def _engine():
    return ConversationEngine(provider_manager=AIProviderManager())


def test_direct_mention_replies():
    e = _engine()
    d = e.decide(content="Rosy what's up?", is_mention=True, is_reply_to_bot=False,
                 has_bot_name=True, allow_autonomous=False, channel_id=1)
    assert d.should_reply is True


def test_reply_to_bot_replies():
    e = _engine()
    d = e.decide(content="sure", is_mention=False, is_reply_to_bot=True,
                 has_bot_name=False, allow_autonomous=False, channel_id=1)
    assert d.should_reply is True


def test_no_reply_when_autonomous_disabled():
    e = _engine()
    d = e.decide(content="what's up everyone", is_mention=False, is_reply_to_bot=False,
                 has_bot_name=False, allow_autonomous=False, channel_id=1)
    assert d.should_reply is False


def test_autonomous_question():
    e = _engine()
    d = e.decide(content="what time is it?", is_mention=False, is_reply_to_bot=False,
                 has_bot_name=False, allow_autonomous=True, channel_id=1)
    assert d.should_reply is True


def test_cooldown_blocks_autonomous():
    e = _engine()
    assert e.decide(content="hey?", is_mention=False, is_reply_to_bot=False,
                    has_bot_name=False, allow_autonomous=True, channel_id=1, now=100.0).should_reply is True
    # Second attempt within cooldown window.
    d = e.decide(content="another?", is_mention=False, is_reply_to_bot=False,
                 has_bot_name=False, allow_autonomous=True, channel_id=1, now=101.0)
    assert d.should_reply is False


def test_personality_adaptation():
    p = Personality("casual")
    inferred = p.infer_mode_from_text("this bug keeps crashing, how do I fix it in python?")
    assert inferred == "technical"
