"""Deterministic utility tools: math, conversions, date/time.

Deterministic calculations are done with real code, not left to the LLM to
guess.
"""

from __future__ import annotations

import ast
import operator
from datetime import UTC

from rosy.tools.base import BaseTool, ToolSpec

ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
}


class _SafeCalc(ast.NodeVisitor):
    """Evaluate a limited arithmetic AST (numbers + operators only)."""

    def visit_Constant(self, node: ast.Constant) -> float | int:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers allowed")
    def visit_Name(self, node: ast.Name) -> float:
        raise ValueError(f"Unknown symbol: {node.id}")
    def generic_visit(self, node: ast.AST) -> None:
        raise ValueError(f"Unsupported: {type(node).__name__}")


def safe_eval_math(expression: str) -> str:
    """Evaluate a restricted arithmetic expression safely."""
    tree = ast.parse(expression, mode="eval")

    def visit(node: ast.AST) -> float | int:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op = ALLOWED_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Operator not allowed: {type(node.op).__name__}")
            return op(visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp):
            op = ALLOWED_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unary not allowed: {type(node.op).__name__}")
            return op(visit(node.operand))
        raise ValueError(f"Unsupported syntax: {type(node).__name__}")

    result = visit(tree)
    return result


class MathTool(BaseTool):
    spec = ToolSpec(
        name="math",
        description="Perform a safe arithmetic calculation. Accepts an expression like '2 + 3 * 4'.",
        parameters={
            "expression": {"type": "string", "description": "Arithmetic expression to evaluate."}
        },
    )

    async def execute(self, expression: str = "") -> str:
        if not expression or len(expression) > 200:
            raise ValueError("Invalid expression")
        val = visit_eval(expression)
        return f"{expression} = {val}"


class TimeTool(BaseTool):
    spec = ToolSpec(
        name="current_time",
        description="Get the current UTC date and time.",
        parameters={"timezone": {"type": "string", "description": "Optional IANA timezone, default UTC."}},
    )

    async def execute(self, timezone: str = "UTC", **kwargs) -> str:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        try:
            zone = ZoneInfo(timezone) if timezone and timezone != "UTC" else UTC
        except Exception:
            zone = UTC
        now = datetime.now(zone)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")


def visit_eval(expression: str) -> float | int:
    return safe_eval_math(expression)