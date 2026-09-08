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
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and (abs(right) > 100 or abs(left) > 10_000):
                raise ValueError("Exponentiation is too large")
            value = op(left, right)
            if isinstance(value, (int, float)) and abs(value) > 10**100:
                raise ValueError("Result is too large")
            return value
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

class JsonTool(BaseTool):
    spec = ToolSpec(
        name="json_format",
        description="Parse JSON text and return a clean formatted representation.",
        parameters={"text": {"type": "string", "description": "JSON text."}},
    )
    async def execute(self, text: str = "", **kwargs) -> str:
        import json
        value = json.loads(text)
        return json.dumps(value, ensure_ascii=False, indent=2)[:12000]


class HashTool(BaseTool):
    spec = ToolSpec(
        name="text_hash",
        description="Hash text with a standard digest algorithm.",
        parameters={
            "text": {"type": "string", "description": "Text to hash."},
            "algorithm": {"type": "string", "description": "sha256, sha1 or md5."},
        },
    )
    async def execute(self, text: str = "", algorithm: str = "sha256", **kwargs) -> str:
        import hashlib
        algo = algorithm.lower().replace("-", "")
        if algo not in {"sha256", "sha1", "md5"}:
            raise ValueError("Unsupported hash algorithm")
        return getattr(hashlib, algo)(text.encode()).hexdigest()


class RandomTool(BaseTool):
    spec = ToolSpec(
        name="random_number",
        description="Generate a cryptographically strong random integer in a bounded range.",
        parameters={"minimum": {"type": "integer"}, "maximum": {"type": "integer"}},
    )
    async def execute(self, minimum: int = 1, maximum: int = 100, **kwargs) -> str:
        import secrets
        minimum, maximum = int(minimum), int(maximum)
        if minimum > maximum or maximum - minimum > 1_000_000:
            raise ValueError("Invalid range")
        return str(secrets.randbelow(maximum - minimum + 1) + minimum)


class DiceTool(BaseTool):
    spec = ToolSpec(
        name="roll_dice",
        description="Roll dice using notation such as 2d6 or 1d20.",
        parameters={"dice": {"type": "string"}},
    )
    async def execute(self, dice: str = "1d6", **kwargs) -> str:
        import random, re
        m = re.fullmatch(r"(\d{1,2})d(\d{1,4})", dice.strip().lower())
        if not m:
            raise ValueError("Use notation like 2d6")
        count, sides = map(int, m.groups())
        if count * sides > 100_000:
            raise ValueError("Roll too large")
        rolls = [random.randint(1, sides) for _ in range(count)]
        return f"{dice}: {rolls}; total={sum(rolls)}"


class UrlTool(BaseTool):
    spec = ToolSpec(
        name="url_encode",
        description="URL-encode text for use in a query or URL component.",
        parameters={"text": {"type": "string"}},
    )
    async def execute(self, text: str = "", **kwargs) -> str:
        from urllib.parse import quote
        return quote(text, safe="")


class ChoiceTool(BaseTool):
    spec = ToolSpec(
        name="random_choice",
        description="Choose one item from a short pipe-separated list.",
        parameters={"items": {"type": "string", "description": "Items separated by |."}},
    )
    async def execute(self, items: str = "", **kwargs) -> str:
        import secrets
        values = [x.strip() for x in items.split("|") if x.strip()]
        if not values or len(values) > 100:
            raise ValueError("Provide 1-100 items separated by |")
        return secrets.choice(values)


class Base64Tool(BaseTool):
    spec = ToolSpec(
        name="base64_encode",
        description="Base64 encode UTF-8 text.",
        parameters={"text": {"type": "string"}},
    )
    async def execute(self, text: str = "", **kwargs) -> str:
        import base64
        return base64.b64encode(text.encode()).decode()


class RegexTestTool(BaseTool):
    spec = ToolSpec(
        name="regex_test",
        description="Test a regular expression against text without executing arbitrary code.",
        parameters={"pattern": {"type": "string"}, "text": {"type": "string"}},
    )
    async def execute(self, pattern: str = "", text: str = "", **kwargs) -> str:
        import re
        if len(pattern) > 500 or len(text) > 10000:
            raise ValueError("Input too large")
        try:
            m = re.search(pattern, text)
        except re.error as exc:
            raise ValueError("Invalid regular expression") from exc
        return "match" if m else "no match"
