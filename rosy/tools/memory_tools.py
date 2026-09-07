"""Memory tools — let the AI store and recall memories via tool calls."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rosy.memory.scope import MemoryKey, parse_duration
from rosy.memory.service import MemoryService
from rosy.tools.base import BaseTool, ToolResult


def _key_from_context(context: dict[str, Any] | None, explicit_scope: str | None) -> MemoryKey | None:
    if not context:
        return None
    user_id = context.get("user_id")
    guild_id = context.get("guild_id")
    scope = explicit_scope or context.get("scope") or ("guild" if guild_id else "dm")
    if scope == "dm":
        if not user_id:
            return None
        return MemoryKey(scope="dm", owner_user_id=user_id)
    if scope == "guild":
        if not guild_id:
            return None
        return MemoryKey(scope="guild", guild_id=guild_id)
    if scope == "user_in_guild":
        if not user_id or not guild_id:
            return None
        return MemoryKey(scope="user_in_guild", owner_user_id=user_id, guild_id=guild_id)
    return None


def _session_from_context(context: dict[str, Any] | None) -> async_sessionmaker[AsyncSession] | None:
    return context.get("session_factory") if context else None


class RememberTool(BaseTool):
    name = "remember"
    description = (
        "Store a fact or preference about the current user or guild so it can be recalled later. "
        "Use for durable information the user explicitly wants remembered."
    )
    parameters = {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "What to remember."},
            "scope": {
                "type": "string",
                "enum": ["auto", "dm", "guild", "user_in_guild"],
                "description": "Where to store it. 'auto' picks guild vs dm from context.",
            },
            "ttl": {
                "type": "string",
                "description": "Optional expiry, e.g. '1d', '2h'. Omit to keep indefinitely.",
            },
        },
        "required": ["content"],
    }
    timeout_seconds = 10.0

    async def run(self, arguments: dict[str, Any], context: dict[str, Any] | None = None) -> ToolResult:
        content = str(arguments.get("content", "")).strip()
        if not content:
            return ToolResult(False, "", error="content is required.")
        session_factory = _session_from_context(context)
        if session_factory is None:
            return ToolResult(False, "", error="No database session available.")
        key = _key_from_context(context, arguments.get("scope"))
        if key is None:
            return ToolResult(False, "", error="Could not determine memory scope.")
        ttl = parse_duration(str(arguments.get("ttl") or ""))
        expires = None
        if ttl is not None:
            from datetime import datetime, timezone
            expires = datetime.now(timezone.utc) + ttl
        svc = MemoryService()
        async with session_factory() as session:
            await svc.remember(session, key, content, kind="fact", expires_at=expires)
            await session.commit()
        return ToolResult(True, f"Remembered in scope '{key.scope}'.")


class RecallTool(BaseTool):
    name = "recall"
    description = "Recall stored memories about the current user or guild."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Optional keyword to search by."},
            "scope": {"type": "string", "enum": ["auto", "dm", "guild", "user_in_guild"]},
        },
        "required": [],
    }
    timeout_seconds = 10.0

    async def run(self, arguments: dict[str, Any], context: dict[str, Any] | None = None) -> ToolResult:
        session_factory = _session_from_context(context)
        if session_factory is None:
            return ToolResult(False, "", error="No database session available.")
        key = _key_from_context(context, arguments.get("scope"))
        if key is None:
            return ToolResult(False, "", error="Could not determine memory scope.")
        svc = MemoryService()
        async with session_factory() as session:
            query = str(arguments.get("query") or "").strip()
            if query:
                rows = await svc.search(session, key, query)
            else:
                rows = await svc.list_memories(session, key, limit=10)
            await session.commit()
        if not rows:
            return ToolResult(True, "[recall] No memories found.")
        lines = [f"[memories in scope {key.scope}]"]
        for m in rows:
            lines.append(f"- ({m.kind}) {m.content}")
        return ToolResult(True, "\n".join(lines))
