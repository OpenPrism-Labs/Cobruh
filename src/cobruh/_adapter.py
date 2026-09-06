"""Shared CLI and MCP adapter helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from cobruh.errors import ConfigError


def select_value(data: Mapping[str, Any], node: str) -> Any:
    """Select any value at a dotted path from composed data."""
    if not node:
        return data
    cursor: Any = data
    traversed: list[str] = []
    for part in node.split("."):
        if not part:
            raise ConfigError(f"Invalid empty component in node path '{node}'")
        traversed.append(part)
        if not isinstance(cursor, Mapping) or part not in cursor:
            raise ConfigError(f"Node path '{node}' does not exist at '{'.'.join(traversed)}'")
        cursor = cursor[part]
    return cursor


def select_mapping(data: Mapping[str, Any], node: str) -> Mapping[str, Any]:
    """Select a dotted node and require a runtime target mapping."""
    selected = select_value(data, node)
    if not isinstance(selected, Mapping):
        raise ConfigError(f"Node path '{node}' must select a mapping")
    return selected


def result_envelope(result: Any) -> dict[str, Any]:
    """Describe a runtime result with bounded, optionally serialized output."""
    result_type = type(result)
    envelope: dict[str, Any] = {
        "type": f"{result_type.__module__}.{result_type.__qualname__}",
        "repr": repr(result)[:4096],
    }
    try:
        json.dumps(result)
    except (TypeError, ValueError, OverflowError):
        pass
    else:
        envelope["value"] = result
    return envelope
