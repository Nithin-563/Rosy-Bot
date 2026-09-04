"""AI provider factory + router tests (mocked HTTP, no real keys)."""
from __future__ import annotations

import pytest

from rosy.ai.base import Message, ProviderError, ToolDef
from rosy.ai.factory import ProviderRegistry
from rosy.ai.openai_compat import parse_arguments
from rosy.ai.router import ProviderRouter


def test_parse_arguments():
    assert parse_arguments('{"a": 1}') == {"a": 1}
    assert parse_arguments("not json") == {}
    assert parse_arguments("") == {}


def test_factory_unknown_provider():
    with pytest.raises(ValueError):
        ProviderRegistry().build("does-not-exist")


def test_router_resolve_builds_and_caches():
    router = ProviderRouter()
    p1 = router.resolve(provider="openrouter", model="m")
    p2 = router.resolve(provider="openrouter", model="m")
    assert p1 is p2  # cached


class _FakeProvider:
    """Minimal provider double for router fallback testing."""

    def __init__(self, name, should_fail=False):
        self.name = name
        self.should_fail = should_fail
        self.calls = 0

    async def complete(self, messages, **kwargs):
        self.calls += 1
        if self.should_fail:
            raise ProviderError(f"{self.name} down")
        from rosy.ai.base import ChatResponse
        return ChatResponse(content=f"from-{self.name}", model=kwargs.get("model") or "", provider=self.name)


def test_router_fallback_on_error(monkeypatch):
    router = ProviderRouter()

    primary = _FakeProvider("primary", should_fail=True)
    fallback = _FakeProvider("fallback")

    def fake_resolve(*, provider=None, model=None, api_key=None, base_url=None, guild_id=None):
        return primary if provider is None else fallback

    monkeypatch.setattr(router, "resolve", fake_resolve)

    import asyncio
    resp = asyncio.run(router.complete([Message(role="user", content="hi")], fallbacks=["openai"]))
    assert resp.content == "from-fallback"
    assert primary.calls == 1
    assert fallback.calls == 1


def test_all_fail_raises(monkeypatch):
    router = ProviderRouter()
    primary = _FakeProvider("primary", should_fail=True)
    monkeypatch.setattr(router, "resolve", lambda **kw: primary)
    import asyncio
    with pytest.raises(ProviderError):
        asyncio.run(router.complete([Message(role="user", content="hi")]))
