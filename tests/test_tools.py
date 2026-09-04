"""Tool safety tests: deterministic math + rejection of unsafe input."""

from __future__ import annotations

import pytest

from rosy.tools.builtins import safe_eval_math
from rosy.tools import MathTool, ToolRegistry


@pytest.mark.asyncio
async def test_math_tool():
    tool = MathTool()
    result = await tool.execute(expression="2 + 3 * 4")
    assert "14" in result


@pytest.mark.asyncio
async def test_math_rejects_unsafe():
    tool = MathTool()
    with pytest.raises(Exception):
        await tool.execute(expression="__import__('os').system('id')")
    with pytest.raises(Exception):
        await tool.execute(expression="1; import os")


def test_safe_eval_math_basic():
    assert safe_eval_math("10 - 4") == 6
    assert safe_eval_math("(2 + 3) * 4") == 20


def test_registry_rejects_duplicate():
    reg = ToolRegistry()
    reg.register_class(MathTool())
    with pytest.raises(Exception):
        reg.register_class(MathTool())