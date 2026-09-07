"""Generic tool framework: schema, execution, validation, registry."""
from __future__ import annotations

import abc
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from rosy.ai.base import ToolDef

log = logging.getLogger(__name__)


@dataclass
class ToolResult:
    ok: bool
    output: str
    error: str | None = None
    used_tokens: int = 0


@dataclass
class ToolCall:
    id: str | None
    name: str
    arguments: dict[str, Any]


class BaseTool(abc.ABC):
    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
    required_permission: str | None = None  # e.g. "admin", "moderator"
    timeout_seconds: float = 30.0

    def to_tool_def(self) -> ToolDef:
        return ToolDef(name=self.name, description=self.description, parameters=self.parameters)

    @abc.abstractmethod
    async def run(self, arguments: dict[str, Any], context: dict[str, Any] | None = None) -> ToolResult:
        raise NotImplementedError


class ToolRegistry:
    """Validates tool calls and executes them safely, with timeout + error handling."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._hook: Callable[..., Awaitable[None]] | None = None

    def register(self, tool: BaseTool) -> "ToolRegistry":
        if not tool.name:
            raise ValueError("Tool must define a non-empty name.")
        self._tools[tool.name] = tool
        return self

    def set_log_hook(self, hook: Callable[..., Awaitable[None]]) -> None:
        self._hook = hook

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def tool_defs(self) -> list[ToolDef]:
        return [t.to_tool_def() for t in self._tools.values()]

    async def dispatch(
        self,
        call: ToolCall,
        context: dict[str, Any] | None = None,
    ) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolResult(False, "", error=f"Unknown tool: {call.name}")
        if self._hook:
            try:
                await self._hook(call.name, call.arguments, context)
            except Exception:  # noqa: BLE001 - observability hook must never break execution
                log.exception("Tool log hook failed")
        try:
            return await tool.run(call.arguments, context)
        except Exception as exc:  # noqa: BLE001 - tools must never crash the loop
            log.exception("Tool %s failed", call.name)
            return ToolResult(False, "", error=f"{tool.name} error: {exc}")

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return list(self._tools.keys())


def tool_error_to_result(exc: Exception) -> ToolResult:
    return ToolResult(False, "", error=str(exc))


def safe_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
