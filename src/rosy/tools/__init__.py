from rosy.tools.base import BaseTool, ToolRegistry, ToolSpec
from rosy.tools.builtins import MathTool, TimeTool
from rosy.tools.web import ExtractTextTool, WebFetchTool, WebSearchTool, WebTools

__all__ = ["BaseTool", "ToolRegistry", "ToolSpec", "MathTool", "TimeTool", "ExtractTextTool", "WebFetchTool", "WebSearchTool", "WebTools"]

def build_default_registry(http=None, files=None) -> ToolRegistry:
    reg = ToolRegistry()
    reg.register_class(MathTool())
    reg.register_class(TimeTool())
    WebTools.register(reg, http=http, files=files)
    return reg
