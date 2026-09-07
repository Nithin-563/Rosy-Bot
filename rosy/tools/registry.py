"""Default tool registry assembly."""
from __future__ import annotations

from rosy.tools.base import ToolRegistry
from rosy.tools.calculator import CalculatorTool
from rosy.tools.datetime_tool import DateTimeTool, RelativeTimeTool
from rosy.tools.memory_tools import RecallTool, RememberTool
from rosy.tools.web_search import WebSearchTool


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(DateTimeTool())
    registry.register(RelativeTimeTool())
    registry.register(WebSearchTool())
    registry.register(RememberTool())
    registry.register(RecallTool())
    return registry
