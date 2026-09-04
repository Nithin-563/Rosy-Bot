"""Tests for the deterministic calculation tool."""

import pytest

from rosy.tools.math_tool import CalculateTool


@pytest.mark.asyncio
async def test_basic_arithmetic():
    tool = CalculateTool()
    assert "= 8" in await tool.execute(expression="2 + 3 * 2")


@pytest.mark.asyncio
async def test_parens_and_pow():
    tool = CalculateTool()
    assert "= 20" in await tool.execute(expression="(2 + 3) * 4")
    assert "= 8" in await tool.execute(expression="2 ** 3")


@pytest.mark.asyncio
async def test_unsafe_rejected():
    tool = CalculateTool()
    result = await tool.execute(expression="__import__('os').system('ls')")
    assert "error" in result.lower() or "not allowed" in result.lower()
