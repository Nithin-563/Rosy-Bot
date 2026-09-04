"""Conversation engine — orchestrates provider calls, tool dispatch, memory.""" 
from __future__ import annotations

import json
import logging
from typing import Any

from rosy.ai.base import ChatResponse, Message, ProviderError
from rosy.ai.openai_compat import parse_arguments
from rosy.ai.router import ProviderRouter
from rosy.conversation.context import ContextBuilder
from rosy.conversation.decision import ResponseDecider
from rosy.personality.manager import PersonalityManager
from rosy.tools.base import ToolCall, ToolRegistry

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4


class ConversationEngine:
    def __init__(
        self,
        router: ProviderRouter,
        registry: ToolRegistry,
        context_builder: ContextBuilder | None = None,
        personality: PersonalityManager | None = None,
        decider: ResponseDecider | None = None,
    ) -> None:
        self.router = router
        self.registry = registry
        self.personality = personality or PersonalityManager()
        self.context_builder = context_builder or ContextBuilder(self.personality)
        self.decider = decider or ResponseDecider()

    async def respond(
        self,
        *,
        recent_messages: list[Message],
        memories: list[str] | None = None,
        summary: str = "",
        guild_id: int | None = None,
        user_id: int | None = None,
        mode: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        tool_context: dict[str, Any] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        tool_context = tool_context or {}
        ctx = self.context_builder.build(
            mode=mode,
            recent_messages=recent_messages,
            summary=summary,
            memories=memories,
        )

        working: list[Message] = list(ctx.messages)
        tool_defs = self.registry.tool_defs()

        for _round in range(MAX_TOOL_ROUNDS):
            resp = await self.router.complete(
                working,
                tools=tool_defs or None,
                provider=provider,
                model=model,
                guild_id=guild_id,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if not resp.tool_calls:
                return resp

            working.append(
                Message(role="assistant", content=resp.content, tool_calls=resp.tool_calls)
            )
            for tc in resp.tool_calls:
                args = parse_arguments(tc.get("arguments") or "")
                call = ToolCall(id=tc.get("id"), name=tc.get("name", ""), arguments=args)
                result = await self.registry.dispatch(call, tool_context)
                working.append(
                    Message(
                        role="tool",
                        name=call.id,
                        content=json.dumps(
                            {"ok": result.ok, "output": result.output, "error": result.error},
                            ensure_ascii=False,
                        ),
                    )
                )

        # Tool loop exhausted without a final text answer — return last response.
        return resp
