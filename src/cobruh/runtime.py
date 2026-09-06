"""Recursive target resolution and allowlisted construction."""

from __future__ import annotations

import builtins
import copy
import importlib
import inspect
import sys
from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from typing import Any

from cobruh.errors import TargetError

_RESERVED_KEYS = {"_target_", "_args_", "_partial_", "_recursive_"}


def normalize_allowed_targets(allowed_targets: Sequence[str]) -> tuple[str, ...]:
    """Validate and normalize exact targets and ``module.*`` prefixes."""
    if isinstance(allowed_targets, (str, bytes, bytearray)):
        raise TargetError("Allowed targets must be a sequence of target rules, not a string")
    normalized: list[str] = []
    for entry in allowed_targets:
        if not isinstance(entry, str) or not entry.strip():
            raise TargetError(f"Invalid empty allowed target rule: {entry!r}")
        rule = entry.strip()
        if rule == "*":
            raise TargetError("Bare '*' is not a valid allowed target rule")
        wildcard = rule.endswith(".*")
        base = rule[:-2] if wildcard else _normalize_configured_name(rule)
        if "*" in base or not base or any(not part.isidentifier() for part in base.split(".")):
            raise TargetError(
                f"Invalid allowed target rule '{entry}': expected a fully qualified target "
                "or a prefix ending in '.*'"
            )
        normalized.append(f"{base}.*" if wildcard else base)
    return tuple(normalized)


def instantiate(
    project_root: Path,
    allowed_targets: tuple[str, ...],
    config: Mapping[str, Any],
    /,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Instantiate a target mapping with project-local imports available."""
    if not isinstance(config, Mapping):
        raise TargetError(
            f"Target config at '<root>' must be a mapping, got {type(config).__name__}"
        )

    original_path = sys.path[:]
    sys.path.insert(0, str(project_root))
    try:
        return _instantiate_target(
            config,
            "<root>",
            allowed_targets,
            args or None,
            kwargs or None,
        )
    finally:
        sys.path[:] = original_path


def _instantiate_target(
    config: Mapping[str, Any],
    path: str,
    allowed_targets: tuple[str, ...],
    explicit_args: tuple[Any, ...] | None = None,
    explicit_kwargs: Mapping[str, Any] | None = None,
) -> Any:
    target_value = config.get("_target_")
    if not isinstance(target_value, str) or not target_value.strip():
        raise TargetError(f"Target config at '{path}' requires a nonempty string '_target_'")
    configured_name = target_value.strip()
    normalized_name = _normalize_configured_name(configured_name)

    unknown_reserved = sorted(
        key
        for key in config
        if isinstance(key, str) and key.startswith("_") and key not in _RESERVED_KEYS
    )
    if unknown_reserved:
        raise TargetError(
            f"Target '{configured_name}' at '{path}' has unsupported reserved field "
            f"'{unknown_reserved[0]}'"
        )

    configured_args = config.get("_args_", ())
    if not isinstance(configured_args, Sequence) or isinstance(
        configured_args, (str, bytes, bytearray)
    ):
        raise TargetError(
            f"Target '{configured_name}' at '{path}' requires '_args_' to be a sequence"
        )
    partial_value = config.get("_partial_", False)
    if not isinstance(partial_value, bool):
        raise TargetError(
            f"Target '{configured_name}' at '{path}' requires '_partial_' to be a boolean"
        )
    recursive = config.get("_recursive_", True)
    if not isinstance(recursive, bool):
        raise TargetError(
            f"Target '{configured_name}' at '{path}' requires '_recursive_' to be a boolean"
        )

    _require_allowed(configured_name, normalized_name, path, allowed_targets)
    try:
        target = _resolve_target(normalized_name)
    except Exception as exc:
        if isinstance(exc, TargetError):
            raise
        raise TargetError(f"Cannot resolve target '{configured_name}' at '{path}': {exc}") from exc
    if not callable(target):
        raise TargetError(f"Resolved target '{configured_name}' at '{path}' is not callable")
    canonical_name = _canonical_target_name(target, normalized_name)
    _require_allowed(configured_name, canonical_name, path, allowed_targets)

    positional_source: Sequence[Any] = configured_args if explicit_args is None else explicit_args
    if recursive:
        positional = [
            _instantiate_value(value, f"{path}._args_[{index}]", allowed_targets)
            for index, value in enumerate(positional_source)
        ]
        configured_kwargs = {
            key: _instantiate_value(value, f"{path}.{key}", allowed_targets)
            for key, value in config.items()
            if key not in _RESERVED_KEYS
        }
    else:
        positional = copy.deepcopy(list(positional_source))
        configured_kwargs = {
            key: copy.deepcopy(value) for key, value in config.items() if key not in _RESERVED_KEYS
        }

    if explicit_kwargs:
        for key, value in explicit_kwargs.items():
            configured_kwargs[key] = (
                _instantiate_value(value, f"{path}.{key}", allowed_targets) if recursive else value
            )

    try:
        if partial_value:
            try:
                inspect.signature(target).bind_partial(*positional, **configured_kwargs)
            except ValueError:
                pass
            return partial(target, *positional, **configured_kwargs)
        return target(*positional, **configured_kwargs)
    except Exception as exc:
        raise TargetError(
            f"Failed constructing target '{configured_name}' at '{path}': {exc}"
        ) from exc


def _instantiate_value(value: Any, path: str, allowed_targets: tuple[str, ...]) -> Any:
    if isinstance(value, Mapping):
        if "_target_" in value:
            return _instantiate_target(value, path, allowed_targets)
        return {
            key: _instantiate_value(child, f"{path}.{key}", allowed_targets)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [
            _instantiate_value(child, f"{path}[{index}]", allowed_targets)
            for index, child in enumerate(value)
        ]
    if isinstance(value, tuple):
        return tuple(
            _instantiate_value(child, f"{path}[{index}]", allowed_targets)
            for index, child in enumerate(value)
        )
    return copy.deepcopy(value)


def _normalize_configured_name(target_name: str) -> str:
    if "." not in target_name and hasattr(builtins, target_name):
        return f"builtins.{target_name}"
    return target_name


def _require_allowed(
    configured_name: str,
    canonical_name: str,
    path: str,
    allowed_targets: tuple[str, ...],
) -> None:
    if any(_rule_matches(rule, canonical_name) for rule in allowed_targets):
        return
    raise TargetError(
        f"Target at '{path}' is not allowed: configured '{configured_name}', "
        f"canonical '{canonical_name}'"
    )


def _rule_matches(rule: str, target_name: str) -> bool:
    if rule.endswith(".*"):
        return target_name.startswith(rule[:-1])
    return target_name == rule


def _canonical_target_name(target: Any, fallback: str) -> str:
    module = getattr(target, "__module__", None)
    qualname = getattr(target, "__qualname__", None)
    if isinstance(module, str) and isinstance(qualname, str):
        return f"{module}.{qualname}"
    return fallback


def _resolve_target(target_name: str) -> Any:
    parts = target_name.split(".")
    if any(not part for part in parts):
        raise ImportError("target path contains an empty component")
    last_error: Exception | None = None
    for split_at in range(len(parts) - 1, 0, -1):
        module_name = ".".join(parts[:split_at])
        try:
            value: Any = importlib.import_module(module_name)
        except ImportError as exc:
            last_error = exc
            continue
        try:
            for attribute in parts[split_at:]:
                value = getattr(value, attribute)
        except AttributeError as exc:
            raise ImportError(
                f"attribute path '{'.'.join(parts[split_at:])}' does not exist in '{module_name}'"
            ) from exc
        return value
    raise ImportError(f"module for '{target_name}' could not be imported") from last_error
