"""Generic tool framework.

Each tool has a name, description, JSON schema, permission requirements,
execution method, timeout and error handling. Tools are validated before
execution and never grant unrestricted system access.
"""

from __future__ import annotations

import abc
import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from rosy.core.errors import ToolError

logger = logging.getLogger("rosy.tools")


@dataclass
class ToolSpec:
    """A concrete tool definition/registration."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON-schema-ish
    required_permission: str = "use_tools"  # coarse permission bucket
    timeout_seconds: float = 15.0
    handler: Callable[..., Any] | None = None
    async_handler: Callable[..., Coroutine[Any, Any, Any]] | None = None

    def to_llm_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": [],
                },
            },
        }


class BaseTool(abc.ABC):
    """Implement `execute` and expose `spec`."""

    spec: ToolSpec

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._handlers: dict[str, Any] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ToolError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = spec
        self._handlers[spec.name] = spec.handler or spec.async_handler

    def register_class(self, tool: BaseTool) -> None:
        spec = tool.spec
        spec.async_handler = tool.execute
        self.register(spec)

    def get(self, name: str) -> ToolSpec:
        spec = self._tools.get(name)
        if spec is None:
            raise ToolError(f"Unknown tool: {name}")
        return spec

    def specs(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def llm_schemas(self) -> list[dict[str, Any]]:
        return [t.to_llm_schema() for t in self._tools.values()]

    async def run(self, name: str, arguments: dict[str, Any], *, permission: str = "use_tools") -> str:
        spec = self.get(name)
        if spec.required_permission and permission != spec.required_permission:
            raise PermissionError(f"Missing permission '{spec.required_permission}' for tool '{name}'")
        handler = self._handlers.get(name)
        if handler is None:
            raise ToolError(f"Tool '{name}' has no handler.")
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await asyncio.wait_for(handler(**arguments), timeout=spec.timeout_seconds)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(handler, **arguments), timeout=spec.timeout_seconds
                )
        except TimeoutError as exc:
            raise ToolError(f"Tool '{name}' timed out.") from exc
        except Exception as exc:
            logger.warning("Tool '%s' failed: %s", name, exc)
            raise ToolError(f"Tool '{name}' failed.") from exc
        return self._stringify(result)

    @staticmethod
    def _stringify(result: Any) -> str:
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        import json

        return json.dumps(result, default=str)