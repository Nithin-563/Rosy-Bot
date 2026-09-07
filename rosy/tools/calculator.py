"""Safe, deterministic arithmetic calculator using AST evaluation.

Never uses eval/exec. Only allows numbers and a whitelist of binary/unary ops.
"""
from __future__ import annotations

import ast
import math
import operator
from typing import Any

from rosy.tools.base import BaseTool, ToolResult

_ALLOWED_BINOPS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY: dict[type[ast.unaryop], Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_eval_math(expr: str) -> float:
    """Evaluate a numeric arithmetic expression safely. Raises on invalid input."""
    tree = ast.parse(expr, mode="eval")

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            return _ALLOWED_BINOPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return _call_math(node.func.id, [_eval(a) for a in node.args])
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        raise ValueError("Unsupported expression.")

    return _eval(tree)


_MATH_FUNCS = {
    "sqrt": math.sqrt, "abs": abs, "ceil": math.ceil, "floor": math.floor,
    "round": round, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "log10": math.log10, "exp": math.exp, "factorial": math.factorial,
}


def _call_math(name: str, args: list[float]) -> float:
    if name not in _MATH_FUNCS:
        raise ValueError(f"Unknown function: {name}")
    return float(_MATH_FUNCS[name](*args))


class CalculatorTool(BaseTool):
    name = "calculate"
    description = "Perform a precise arithmetic calculation. Returns the numeric result."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A safe arithmetic expression, e.g. '(2 + 3) * 4' or 'sqrt(144)'.",
            }
        },
        "required": ["expression"],
    }

    async def run(self, arguments: dict[str, Any], context: dict[str, Any] | None = None) -> ToolResult:
        expr = str(arguments.get("expression", "")).strip()
        if not expr:
            return ToolResult(False, "", error="expression is required.")
        try:
            result = safe_eval_math(expr)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(False, "", error=f"Invalid expression: {exc}")
        return ToolResult(True, f"{expr} = {result:g}")
