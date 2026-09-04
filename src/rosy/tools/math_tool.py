"""Deterministic calculation tool.

We prefer deterministic evaluation over asking an LLM to guess arithmetic. The
expression parser is a tiny, safe subset — no imports, no attribute access.
"""

import ast
import operator

from .base import Tool

_ALLOWED_NODES = (
    ast.Expression,
    ast.Constant,
    ast.BinOp,
    ast.UnaryOp,
    ast.Name,
    ast.Load,
    ast.Pow,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.USub,
    ast.UAdd,
)

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}


class _SafeEval(ast.NodeVisitor):
    def visit_Constant(self, node: ast.Constant) -> float:
        if not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed.")
        return float(node.value)

    def visit_Name(self, node: ast.Name) -> float:
        raise ValueError(f"Variables are not allowed ({node.id}).")

    def visit_BinOp(self, node: ast.BinOp) -> float:
        if type(node.op) not in _BINOPS:
            raise ValueError("Unsupported operator.")
        return _BINOPS[type(node.op)](self.visit(node.left), self.visit(node.right))

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        if type(node.op) not in _UNARY:
            raise ValueError("Unsupported unary operator.")
        return _UNARY[type(node.op)](self.visit(node.operand))

    def visit_Expression(self, node: ast.Expression) -> float:
        return self.visit(node.body)


class CalculateTool(Tool):
    name = "calculate"
    description = "Evaluate a safe arithmetic expression and return the result."
    parameters = {
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "Math expression, e.g. (2 + 3) * 4"}},
        "required": ["expression"],
    }

    async def execute(self, expression: str = "") -> str:
        if not expression:
            return "Provide an expression."
        try:
            tree = ast.parse(expression, mode="eval")
            for node in ast.walk(tree):
                if not isinstance(node, _ALLOWED_NODES):
                    raise ValueError("Expression contains unsupported constructs.")
            result = _SafeEval().visit(tree)
            return f"{expression} = {result}"
        except (ValueError, SyntaxError, ZeroDivisionError) as exc:
            return f"Error evaluating expression: {exc}"
