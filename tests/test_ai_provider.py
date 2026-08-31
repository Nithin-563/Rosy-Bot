from __future__ import annotations

import httpx
import pytest

from rosy.ai.base import ChatMessage, OpenAICompatProvider, ProviderConfig


@pytest.mark.asyncio
async def test_openai_compat_posts_and_uses_real_provider_name():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        assert request.headers["authorization"] == "Bearer secret"
        return httpx.Response(200, json={
            "choices": [{"message": {"content": "hello"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        })

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAICompatProvider(
        ProviderConfig("openrouter", "secret", "https://example.test/v1", "openrouter/free"),
        client,
    )
    result = await provider.chat([ChatMessage("user", "hi")])
    assert result.text == "hello"
    assert result.provider == "openrouter"
    assert result.model == "openrouter/free"
    await client.aclose()
