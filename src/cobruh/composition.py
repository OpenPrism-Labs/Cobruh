"""YAML cataloging, composition, overrides, and interpolation."""

from __future__ import annotations

import copy
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from cobruh.errors import ConfigError, OverrideError

MAX_SOURCE_BYTES = 1024 * 1024
_YAML_SUFFIXES = (".yaml", ".yml")
_INTERPOLATION = re.compile(r"\$\{([^{}]+)\}")
_EXACT_INTERPOLATION = re.compile(r"^\$\{([^{}]+)\}$")


@dataclass(frozen=True)
class CompositionResult:
    """Composed data and its ordered root-relative source provenance."""

    data: dict[str, Any]
    sources: tuple[str, ...]


def catalog(config_root: Path) -> dict[str, object]:
    """Return a deterministic catalog of root configs and config groups."""
    configs: list[str] = []
    groups: dict[str, list[str]] = {}
    variants: dict[tuple[str, str], Path] = {}

    for path in sorted(config_root.rglob("*")):
        if not path.is_file() or path.suffix not in _YAML_SUFFIXES:
            continue
        _validate_existing_source(config_root, path)
        relative = path.relative_to(config_root)
        group = relative.parent.as_posix()
        key = (group, path.stem)
        previous = variants.get(key)
        if previous is not None:
            raise ConfigError(
                f"Duplicate YAML variants for '{relative.with_suffix('').as_posix()}': "
                f"{previous.name} and {path.name}"
            )
        variants[key] = path
        if relative.parent == Path("."):
            configs.append(path.stem)
        else:
            groups.setdefault(group, []).append(path.stem)

    return {
        "configs": sorted(configs),
        "groups": {name: sorted(options) for name, options in sorted(groups.items())},
    }


def compose(
    config_root: Path,
    name: str,
    overrides: Sequence[str],
    *,
    resolve: bool,
) -> CompositionResult:
    """Compose a logical config name and sequential overrides."""
    data, sources = _compose_file(config_root, name, ())
    mutable_sources = list(sources)
    for override in overrides:
        _apply_override(config_root, data, mutable_sources, override)
    if resolve:
        data = _resolve_interpolations(data)
    return CompositionResult(data=data, sources=tuple(mutable_sources))


def normalize_logical_name(name: str) -> str:
    """Normalize and validate a root-relative logical config name."""
    if not isinstance(name, str) or not name.strip():
        raise ConfigError(f"Invalid empty config name: {name!r}")
    normalized = name.strip().replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ConfigError(f"Invalid config name '{name}': expected a root-relative path")
    suffix = pure.suffix.lower()
    if suffix in _YAML_SUFFIXES:
        pure = pure.with_suffix("")
    elif suffix:
        raise ConfigError(f"Invalid config name '{name}': expected .yaml or .yml")
    return pure.as_posix()


def resolve_source_path(config_root: Path, name: str) -> Path:
    """Resolve one logical name, rejecting duplicate variants and escape."""
    logical = normalize_logical_name(name)
    base = config_root.joinpath(*PurePosixPath(logical).parts)
    candidates = [base.with_suffix(suffix) for suffix in _YAML_SUFFIXES]
    existing = [
        candidate for candidate in candidates if candidate.exists() or candidate.is_symlink()
    ]
    if len(existing) > 1:
        relative = base.relative_to(config_root).as_posix()
        raise ConfigError(f"Duplicate YAML variants for '{relative}': .yaml and .yml")
    if not existing:
        raise ConfigError(f"Config source '{logical}' was not found under '{config_root}'")
    path = existing[0]
    _validate_existing_source(config_root, path)
    return path


def load_source_mapping(config_root: Path, path: Path) -> dict[str, Any]:
    """Load one validated YAML mapping source."""
    _validate_existing_source(config_root, path)
    size = path.stat().st_size
    relative = path.relative_to(config_root).as_posix()
    if size > MAX_SOURCE_BYTES:
        raise ConfigError(
            f"Config source '{relative}' is {size} bytes; limit is {MAX_SOURCE_BYTES} bytes"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ConfigError(f"Cannot read config source '{relative}': {exc}") from exc
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Malformed YAML in config source '{relative}': {exc}") from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(
            f"Config source '{relative}' must contain a mapping, got {type(loaded).__name__}"
        )
    return loaded


def _validate_existing_source(config_root: Path, path: Path) -> None:
    try:
        relative = path.relative_to(config_root)
    except ValueError as exc:
        raise ConfigError(f"Config source '{path}' is outside config root '{config_root}'") from exc
    if path.suffix not in _YAML_SUFFIXES:
        raise ConfigError(f"Config source '{relative.as_posix()}' must use .yaml or .yml")
    resolved = path.resolve()
    if not resolved.is_relative_to(config_root):
        raise ConfigError(
            f"Config source '{relative.as_posix()}' escapes config root '{config_root}'"
        )
    if not resolved.is_file():
        raise ConfigError(f"Config source '{relative.as_posix()}' is not a regular file")


def _compose_file(
    config_root: Path, name: str, chain: tuple[str, ...]
) -> tuple[dict[str, Any], tuple[str, ...]]:
    path = resolve_source_path(config_root, name)
    relative = path.relative_to(config_root).as_posix()
    if relative in chain:
        cycle = " -> ".join((*chain, relative))
        raise ConfigError(f"Config include cycle: {cycle}")

    document = load_source_mapping(config_root, path)
    defaults = document.pop("defaults", None)
    if defaults is None:
        defaults = []
    if not isinstance(defaults, list):
        raise ConfigError(f"Invalid defaults in '{relative}': expected a list")

    result: dict[str, Any] = {}
    sources: list[str] = []
    saw_self = False
    next_chain = (*chain, relative)

    for index, item in enumerate(defaults):
        if item == "_self_":
            if saw_self:
                raise ConfigError(f"Duplicate _self_ in defaults of '{relative}'")
            saw_self = True
            _deep_merge(result, copy.deepcopy(document))
            sources.append(relative)
            continue
        if isinstance(item, str):
            included_data, included_sources = _compose_included(
                config_root, item, next_chain, relative, index
            )
            _deep_merge(result, included_data)
            sources.extend(included_sources)
            continue
        if isinstance(item, dict) and len(item) == 1:
            group, option = next(iter(item.items()))
            if not isinstance(group, str) or not group or not isinstance(option, str) or not option:
                raise ConfigError(
                    f"Invalid defaults item {index} in '{relative}': group and option must be strings"
                )
            logical = f"{group}/{option}"
            included_data, included_sources = _compose_included(
                config_root, logical, next_chain, relative, index
            )
            grouped: dict[str, Any] = {}
            cursor = grouped
            parts = group.replace("\\", "/").split("/")
            if any(not part or part in {".", ".."} for part in parts):
                raise ConfigError(f"Invalid defaults group '{group}' in '{relative}'")
            for part in parts[:-1]:
                child: dict[str, Any] = {}
                cursor[part] = child
                cursor = child
            cursor[parts[-1]] = included_data
            _deep_merge(result, grouped)
            sources.extend(included_sources)
            continue
        raise ConfigError(
            f"Invalid defaults item {index} in '{relative}': expected _self_, a config name, "
            "or a one-key group mapping"
        )

    if not saw_self:
        _deep_merge(result, document)
        sources.append(relative)
    return result, tuple(sources)


def _compose_included(
    config_root: Path,
    name: str,
    chain: tuple[str, ...],
    source: str,
    index: int,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    try:
        return _compose_file(config_root, name, chain)
    except ConfigError as exc:
        include_chain = " -> ".join(chain)
        raise ConfigError(
            f"Failed defaults item {index} '{name}' in '{source}' "
            f"(include chain: {include_chain}): {exc}"
        ) from exc


def _deep_merge(destination: dict[str, Any], incoming: Mapping[str, Any]) -> None:
    for key, value in incoming.items():
        current = destination.get(key)
        if isinstance(current, dict) and isinstance(value, Mapping):
            _deep_merge(current, value)
        else:
            destination[key] = copy.deepcopy(value)


def _apply_override(
    config_root: Path,
    data: dict[str, Any],
    sources: list[str],
    expression: str,
) -> None:
    if not isinstance(expression, str) or "=" not in expression:
        raise OverrideError(f"Invalid override {expression!r}: expected path=value")
    raw_path, raw_value = expression.split("=", 1)
    create = raw_path.startswith("+")
    path = raw_path[1:] if create else raw_path
    parts = path.split(".")
    if not path or any(not part or part in {".", ".."} for part in parts):
        raise OverrideError(f"Invalid override path '{path}' in '{expression}'")

    group_parts = path.replace("\\", "/").split("/")
    group_dir = config_root.joinpath(*PurePosixPath(path.replace("\\", "/")).parts)
    group_is_directory = (
        not create
        and "." not in path
        and all(part not in {"", ".", ".."} for part in group_parts)
        and group_dir.exists()
        and group_dir.is_dir()
        and group_dir.resolve().is_relative_to(config_root)
    )
    if group_is_directory:
        try:
            selected, selected_sources = _compose_file(config_root, f"{path}/{raw_value}", ())
        except ConfigError as exc:
            raise OverrideError(
                f"Unknown option '{raw_value}' for config group '{path}': {exc}"
            ) from exc
        _assign_group(data, group_parts, selected, expression=expression)
        sources.extend(selected_sources)
        return

    try:
        value = yaml.safe_load(raw_value)
    except yaml.YAMLError as exc:
        raise OverrideError(f"Invalid YAML value in override '{expression}': {exc}") from exc
    _assign_path(data, parts, value, create=create, expression=expression)


def _assign_group(
    data: dict[str, Any],
    parts: list[str],
    value: dict[str, Any],
    *,
    expression: str,
) -> None:
    cursor = data
    for part in parts[:-1]:
        child = cursor.get(part)
        if child is None:
            child = {}
            cursor[part] = child
        if not isinstance(child, dict):
            raise OverrideError(
                f"Group override '{expression}' cannot traverse non-mapping key '{part}'"
            )
        cursor = child
    cursor[parts[-1]] = copy.deepcopy(value)


def _assign_path(
    data: dict[str, Any],
    parts: list[str],
    value: Any,
    *,
    create: bool,
    expression: str,
) -> None:
    cursor: dict[str, Any] = data
    for part in parts[:-1]:
        if part not in cursor:
            if not create:
                raise OverrideError(
                    f"Override '{expression}' references missing path '{'.'.join(parts)}'"
                )
            cursor[part] = {}
        child = cursor[part]
        if not isinstance(child, dict):
            raise OverrideError(f"Override '{expression}' cannot traverse non-mapping key '{part}'")
        cursor = child
    leaf = parts[-1]
    exists = leaf in cursor
    if create and exists:
        raise OverrideError(
            f"Override '{expression}' cannot create existing path '{'.'.join(parts)}'"
        )
    if not create and not exists:
        raise OverrideError(f"Override '{expression}' references missing path '{'.'.join(parts)}'")
    cursor[leaf] = copy.deepcopy(value)


def _resolve_interpolations(data: dict[str, Any]) -> dict[str, Any]:
    original = copy.deepcopy(data)
    cache: dict[tuple[str, ...], Any] = {}
    Chain = tuple[tuple[str, ...], ...]

    def chain_text(chain: Chain) -> str:
        return " -> ".join(".".join(path) for path in chain) or "<root>"

    def lookup(path_text: str, chain: Chain) -> Any:
        parts = tuple(path_text.split("."))
        if any(not part for part in parts):
            raise ConfigError(f"Invalid interpolation reference '${{{path_text}}}'")
        cursor: Any = original
        for part in parts:
            if not isinstance(cursor, Mapping) or part not in cursor:
                raise ConfigError(
                    f"Missing interpolation reference '{path_text}' while resolving "
                    f"'{chain_text(chain)}'"
                )
            cursor = cursor[part]
        return resolve_value(cursor, parts, chain)

    def resolve_token(token: str, chain: Chain) -> Any:
        if token.startswith("env:"):
            spec = token[4:]
            name, separator, default = spec.partition(",")
            if not name:
                raise ConfigError(f"Invalid environment interpolation '${{{token}}}'")
            if name in os.environ:
                return os.environ[name]
            if separator:
                return default
            raise ConfigError(
                f"Missing environment variable '{name}' while resolving '{chain_text(chain)}'"
            )
        return lookup(token, chain)

    def resolve_value(value: Any, path: tuple[str, ...], chain: Chain) -> Any:
        if path in cache:
            return copy.deepcopy(cache[path])
        if path in chain:
            cycle = " -> ".join(".".join(item) for item in (*chain, path))
            raise ConfigError(f"Interpolation cycle: {cycle}")

        next_chain = (*chain, path)
        resolved: Any
        if isinstance(value, dict):
            resolved = {
                key: resolve_value(child, (*path, str(key)), next_chain)
                for key, child in value.items()
            }
        elif isinstance(value, list):
            resolved = [
                resolve_value(child, (*path, str(index)), next_chain)
                for index, child in enumerate(value)
            ]
        elif isinstance(value, str):
            exact = _EXACT_INTERPOLATION.fullmatch(value)
            if exact:
                resolved = copy.deepcopy(resolve_token(exact.group(1), next_chain))
            else:
                resolved = _INTERPOLATION.sub(
                    lambda match: str(resolve_token(match.group(1), next_chain)), value
                )
        else:
            resolved = value
        cache[path] = copy.deepcopy(resolved)
        return resolved

    return {key: resolve_value(value, (str(key),), ()) for key, value in original.items()}
