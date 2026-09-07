"""Deterministic date/time and timezone-conversion tool."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rosy.tools.base import BaseTool, ToolResult

_UTC = timezone.utc


class DateTimeTool(BaseTool):
    name = "get_time"
    description = "Get the current UTC time, or convert a UTC datetime to a named timezone."
    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "IANA timezone (e.g. 'America/New_York'). Optional.",
            },
            "iso_utc": {
                "type": "string",
                "description": "Optional ISO-8601 UTC datetime to convert. Defaults to now.",
            },
        },
        "required": [],
    }

    async def run(self, arguments: dict[str, Any], context: dict[str, Any] | None = None) -> ToolResult:
        tz_name = str(arguments.get("timezone") or "").strip()
        iso = str(arguments.get("iso_utc") or "").strip()
        try:
            if iso:
                dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=_UTC)
            else:
                dt = datetime.now(_UTC)
            if tz_name:
                dt = dt.astimezone(ZoneInfo(tz_name))
            return ToolResult(True, dt.isoformat())
        except ZoneInfoNotFoundError:
            return ToolResult(False, "", error=f"Unknown timezone: {tz_name}")
        except ValueError as exc:
            return ToolResult(False, "", error=f"Invalid input: {exc}")


class RelativeTimeTool(BaseTool):
    name = "relative_time"
    description = "Compute a datetime a given duration from now (e.g. 'in 30 minutes')."
    parameters = {
        "type": "object",
        "properties": {
            "delta_seconds": {
                "type": "integer",
                "description": "Seconds from now (positive = future, negative = past).",
            }
        },
        "required": ["delta_seconds"],
    }

    async def run(self, arguments: dict[str, Any], context: dict[str, Any] | None = None) -> ToolResult:
        try:
            delta = int(arguments.get("delta_seconds", 0))
        except (TypeError, ValueError):
            return ToolResult(False, "", error="delta_seconds must be an integer.")
        dt = datetime.now(_UTC) + timedelta(seconds=delta)
        return ToolResult(True, dt.isoformat())
