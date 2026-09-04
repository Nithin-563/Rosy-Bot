"""AI provider manager + context builder tests (no real API keys)."""

import pytest

from rosy.ai.base import ChatMessage, ChatResult, ChatProvider
from rosy.ai.manager import AIProviderManager
from rosy.conversation.context import ContextBuilder
from rosy.conversation.personality import Personality


class FakeProvider(ChatProvider):
    name = "fake"

    async def chat(self, messages, **kwargs):
        return ChatResult(
            content="Hi there!",
            model=self.model,
            provider=self.name,
            usage={"total_tokens": 5},
        )


@pytest.mark.asyncio
async def test_manager_chat_uses_provider():
    mgr = AIProviderManager()
    provider = FakeProvider(api_key="", model="test-model")
    result = await mgr.chat([ChatMessage(role="user", content="hi")], provider=provider)
    assert result.content == "Hi there!"
    assert result.model == "test-model"


def test_context_builder_bounds_messages():
    cb = ContextBuilder(Personality("casual"), max_tokens=4000)
    bundle = cb.build(
        message_text="hello world",
        author_name="Alice",
        memories=[],
        guild_name="Test Guild",
    )
    assert bundle.system
    assert bundle.user_messages[-1].content.startswith("Alice:")


def test_context_includes_memories():
    class M:
        memory_type = "fact"
        key = "likes"
        value = "coffee"

    cb = ContextBuilder(Personality("casual"))
    bundle = cb.build(
        message_text="hello", author_name="Bob", memories=[M()], guild_name="G"
    )
    assert "coffee" in bundle.system
