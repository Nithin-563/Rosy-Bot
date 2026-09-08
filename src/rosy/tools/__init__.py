from rosy.tools.base import BaseTool, ToolRegistry, ToolSpec
from rosy.tools.builtins import Base64Tool, ChoiceTool, DiceTool, HashTool, JsonTool, MathTool, RandomTool, RegexTestTool, TimeTool, UrlTool
from rosy.tools.web import ExtractTextTool, WebFetchTool, WebSearchTool, WebTools

__all__ = ["BaseTool", "ToolRegistry", "ToolSpec", "MathTool", "TimeTool", "JsonTool", "HashTool", "RandomTool", "DiceTool", "UrlTool", "ChoiceTool", "Base64Tool", "RegexTestTool", "ExtractTextTool", "WebFetchTool", "WebSearchTool", "WebTools"]

def build_default_registry(http=None, files=None) -> ToolRegistry:
    reg = ToolRegistry()
    reg.register_class(MathTool())
    reg.register_class(TimeTool())
    reg.register_class(JsonTool())
    reg.register_class(HashTool())
    reg.register_class(RandomTool())
    reg.register_class(DiceTool())
    reg.register_class(UrlTool())
    reg.register_class(ChoiceTool())
    reg.register_class(Base64Tool())
    reg.register_class(RegexTestTool())
    WebTools.register(reg, http=http, files=files)
    return reg
