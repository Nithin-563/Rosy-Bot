"""Regression test: provider chat path must call _handle_status, not a missing
_post_status method. This was the production crash where every AI reply raised
AttributeError even though OpenRouter returned HTTP 200."""

import asyncio

from rosy.ai.base import ChatMessage, OpenAICompatProvider, ProviderConfig


class _FakeResp:
    status_code = 200
    text = "{}"

    def raise_for_status(self):
        pass

    def json(self):
        return {
            "choices": [{"message": {"content": "hello"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }


class _FakeHTTP:
    async def post(self, *args, **kwargs):
        return _FakeResp()


def test_provider_chat_success_does_not_call_missing_post_status():
    cfg = ProviderConfig(provider="openrouter", api_key="k", base_url="https://x/v1", model="m")
    prov = OpenAICompatProvider(cfg, _FakeHTTP())

    result = asyncio.run(prov.chat([ChatMessage(role="user", content="hi")]))
    assert result.text == "hello"


def test_provider_chat_raises_ai_error_on_400():
    class _BadResp(_FakeResp):
        status_code = 400
        text = '{"error":"model not found"}'

        def raise_for_status(self):
            raise _FakeResp  # pragma: no cover - not reached

        def json(self):  # pragma: no cover
            return {}

    class _BadHTTP:
        async def post(self, *args, **kwargs):
            return _BadResp()

    from rosy.core.errors import AIProviderError

    cfg = ProviderConfig(provider="openrouter", api_key="k", base_url="https://x/v1", model="m")
    prov = OpenAICompatProvider(cfg, _BadHTTP())
    try:
        asyncio.run(prov.chat([ChatMessage(role="user", content="hi")]))
        assert False, "expected AIProviderError"
    except AIProviderError:
        pass