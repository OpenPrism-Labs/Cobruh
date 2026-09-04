"""Recursive target resolution and construction."""

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


def instantiate(
    project_root: Path,
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
        return _instantiate_target(config, "<root>", args or None, kwargs or None)
    finally:
        sys.path[:] = original_path


def _instantiate_target(
    config: Mapping[str, Any],
    path: str,
    explicit_args: tuple[Any, ...] | None = None,
    explicit_kwargs: Mapping[str, Any] | None = None,
) -> Any:
    target_value = config.get("_target_")
    if not isinstance(target_value, str) or not target_value.strip():
        raise TargetError(f"Target config at '{path}' requires a nonempty string '_target_'")
    target_name = target_value.strip()

    unknown_reserved = sorted(
        key
        for key in config
        if isinstance(key, str) and key.startswith("_") and key not in _RESERVED_KEYS
    )
    if unknown_reserved:
        raise TargetError(
            f"Target '{target_name}' at '{path}' has unsupported reserved field "
            f"'{unknown_reserved[0]}'"
        )

    configured_args = config.get("_args_", ())
    if not isinstance(configured_args, Sequence) or isinstance(
        configured_args, (str, bytes, bytearray)
    ):
        raise TargetError(f"Target '{target_name}' at '{path}' requires '_args_' to be a sequence")
    partial_value = config.get("_partial_", False)
    if not isinstance(partial_value, bool):
        raise TargetError(
            f"Target '{target_name}' at '{path}' requires '_partial_' to be a boolean"
        )
    recursive = config.get("_recursive_", True)
    if not isinstance(recursive, bool):
        raise TargetError(
            f"Target '{target_name}' at '{path}' requires '_recursive_' to be a boolean"
        )

    positional_source: Sequence[Any] = configured_args if explicit_args is None else explicit_args
    if recursive:
        positional = [
            _instantiate_value(value, f"{path}._args_[{index}]")
            for index, value in enumerate(positional_source)
        ]
        configured_kwargs = {
            key: _instantiate_value(value, f"{path}.{key}")
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
                _instantiate_value(value, f"{path}.{key}") if recursive else value
            )

    try:
        target = _resolve_target(target_name)
    except Exception as exc:
        if isinstance(exc, TargetError):
            raise
        raise TargetError(f"Cannot resolve target '{target_name}' at '{path}': {exc}") from exc

    try:
        if partial_value:
            try:
                inspect.signature(target).bind_partial(*positional, **configured_kwargs)
            except ValueError:
                pass
            return partial(target, *positional, **configured_kwargs)
        return target(*positional, **configured_kwargs)
    except Exception as exc:
        raise TargetError(f"Failed constructing target '{target_name}' at '{path}': {exc}") from exc


def _instantiate_value(value: Any, path: str) -> Any:
    if isinstance(value, Mapping):
        if "_target_" in value:
            return _instantiate_target(value, path)
        return {key: _instantiate_value(child, f"{path}.{key}") for key, child in value.items()}
    if isinstance(value, list):
        return [_instantiate_value(child, f"{path}[{index}]") for index, child in enumerate(value)]
    if isinstance(value, tuple):
        return tuple(
            _instantiate_value(child, f"{path}[{index}]") for index, child in enumerate(value)
        )
    return copy.deepcopy(value)


def _resolve_target(target_name: str) -> Any:
    if "." not in target_name:
        try:
            return getattr(builtins, target_name)
        except AttributeError as exc:
            raise ImportError(f"builtin '{target_name}' does not exist") from exc

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
