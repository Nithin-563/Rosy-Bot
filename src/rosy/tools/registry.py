"""Tool registry and permission gating."""

from typing import Optional

from .base import Tool
from .math_tool import CalculateTool
from .web import WebSearchTool


class ToolRegistry:
    """Holds all available tools and applies per-guild enablement."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def register_defaults(self) -> None:
        self.register(CalculateTool())
        self.register(WebSearchTool())

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def schemas(self, *, is_admin: bool = False, enabled: set[str] | None = None) -> list[dict]:
        out = []
        for tool in self._tools.values():
            if enabled is not None and tool.name not in enabled:
                continue
            if tool.permission == "admin" and not is_admin:
                continue
            out.append(tool.schema())
        return out

    async def invoke(self, name: str, *, is_admin: bool = False, **kwargs) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"[unknown tool: {name}]"
        if tool.permission == "admin" and not is_admin:
            return "[permission denied: this tool requires admin]"
        return await tool.safe_execute(**kwargs)
