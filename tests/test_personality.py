"""Personality engine tests."""

from rosy.conversation.personality import Personality


def test_default_mode():
    p = Personality()
    assert p.mode == "casual"
    assert "Rosy" in p.system_prompt
    assert "human" in p.system_prompt.lower()  # honest about being AI


def test_set_mode_valid_and_invalid():
    p = Personality("casual")
    assert p.set_mode("technical") is True
    assert p.mode == "technical"
    assert p.set_mode("not_a_mode") is False
    assert p.mode == "technical"


def test_infer_mode():
    assert Personality.infer_mode_from_text("how do I fix this bug in python?") == "technical"
    assert Personality.infer_mode_from_text("lol that is funny xd") == "playful"
    assert Personality.infer_mode_from_text("why is the sky blue?") == "curious"
    assert Personality.infer_mode_from_text("just a normal chat") is None
