"""Tool framework + deterministic tool tests."""
from __future__ import annotations

import pytest

from rosy.tools.base import ToolCall, ToolRegistry
from rosy.tools.calculator import CalculatorTool, safe_eval_math
from rosy.tools.datetime_tool import DateTimeTool, RelativeTimeTool


def test_safe_calc():
    assert safe_eval_math("(2 + 3) * 4") == 20.0
    assert safe_eval_math("sqrt(144)") == 12.0
    assert safe_eval_math("10 / 4") == 2.5


def test_safe_calc_rejects_unsafe():
    with pytest.raises(Exception):
        safe_eval_math("__import__('os').system('ls')")
    with pytest.raises(Exception):
        safe_eval_math("1; import os")


@pytest.mark.asyncio
async def test_calculator_tool():
    t = CalculatorTool()
    r = await t.run({"expression": "2 ** 10"})
    assert r.ok and "1024" in r.output
    r2 = await t.run({"expression": "raise(1)"})
    assert r2.ok is False


@pytest.mark.asyncio
async def test_datetime_tool():
    t = DateTimeTool()
    r = await t.run({})
    assert r.ok and r.output
    r2 = await t.run({"timezone": "Not/AZone"})
    assert r2.ok is False


@pytest.mark.asyncio
async def test_relative_time_tool():
    t = RelativeTimeTool()
    r = await t.run({"delta_seconds": 3600})
    assert r.ok


def test_registry_dispatch_unknown():
    reg = ToolRegistry()
    reg.register(CalculatorTool())
    r = None
    import asyncio
    r = asyncio.run(reg.dispatch(ToolCall(id="1", name="does_not_exist", arguments={})))
    assert r.ok is False


@pytest.mark.asyncio
async def test_registry_dispatch_ok():
    reg = ToolRegistry()
    reg.register(CalculatorTool())
    r = await reg.dispatch(ToolCall(id="1", name="calculate", arguments={"expression": "6*7"}))
    assert r.ok and "42" in r.output


def test_registry_tool_defs():
    reg = ToolRegistry()
    reg.register(CalculatorTool())
    defs = reg.tool_defs()
    assert any(d.name == "calculate" for d in defs)
    assert "expression" in defs[0].parameters["properties"]
