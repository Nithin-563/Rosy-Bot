"""Base classes and dataclasses for tools."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("rosy.tools")


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict = field(default_factory=dict)


class Tool(ABC):
    """A single capability Rosy can invoke. Override :meth:`execute`."""

    name: str = "base"
    description: str = ""
    permission: str = "member"  # member | admin
    timeout: float = 15.0

    def __init__(self) -> None:
        self.log = logging.getLogger(f"rosy.tool.{self.name}")

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        raise NotImplementedError

    async def safe_execute(self, **kwargs: Any) -> str:
        try:
            self.log.debug("Executing %s", self.name)
            return await self.execute(**kwargs)
        except Exception as exc:  # noqa: BLE001
            self.log.exception("Tool %s failed", self.name)
            return f"[tool {self.name} error: {type(exc).__name__}]"
