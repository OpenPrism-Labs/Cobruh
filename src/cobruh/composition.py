"""YAML cataloging, composition, overrides, and interpolation."""

from __future__ import annotations

import copy
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from cobruh.errors import ConfigError, OverrideError

MAX_SOURCE_BYTES = 1024 * 1024
_YAML_SUFFIXES = (".yaml", ".yml")
_INTERPOLATION = re.compile(r"\$\{([^{}]+)\}")
_EXACT_INTERPOLATION = re.compile(r"^\$\{([^{}]+)\}$")
_PACKAGE_KEYWORDS = {"_global_", "_group_", "_here_"}


@dataclass(frozen=True)
class CompositionResult:
    """Composed data and its ordered root-relative source provenance."""

    data: dict[str, Any]
    sources: tuple[str, ...]
    choices: tuple[dict[str, Any], ...]
    provenance: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class _Layer:
    source: str | None
    package: tuple[str, ...]
    data: dict[str, Any]
    owners: tuple[int, ...]


@dataclass(frozen=True)
class _Choice:
    selection_id: int
    group: str
    option: str | list[str] | None
    package: str
    declared_by: str
    owners: tuple[int, ...]


@dataclass(frozen=True)
class _ParsedOverride:
    expression: str
    index: int
    operator: str
    target: str
    raw_value: str | None
    is_group: bool
    group: str | None = None
    package: tuple[str, ...] = ()


@dataclass
class _LayerPlan:
    layers: list[_Layer] = field(default_factory=list)
    choices: list[_Choice] = field(default_factory=list)
    next_selection_id: int = 0

    def allocate_selection_id(self) -> int:
        selection_id = self.next_selection_id
        self.next_selection_id += 1
        return selection_id

    def replace_selection(self, group: str, package: str, *, source: str) -> None:
        selected = next(
            (
                choice
                for choice in reversed(self.choices)
                if choice.group == group and choice.package == package
            ),
            None,
        )
        if selected is None:
            raise ConfigError(
                f"Defaults override for group '{group}' package '{package}' in '{source}' "
                "has no earlier selection"
            )
        selection_id = selected.selection_id
        self.layers[:] = [layer for layer in self.layers if selection_id not in layer.owners]
        self.choices[:] = [choice for choice in self.choices if selection_id not in choice.owners]


def catalog(
    config_root: Path,
    schema_sources: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Return deterministic config and option records with exact source paths."""
    schemas = schema_sources or {}
    configs: list[dict[str, str | None]] = []
    groups: dict[str, list[dict[str, str | None]]] = {}
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
        logical_name = relative.with_suffix("").as_posix()
        record = {
            "name": path.stem,
            "path": relative.as_posix(),
            "schema": schemas.get(logical_name),
        }
        if relative.parent == Path("."):
            configs.append(record)
        else:
            groups.setdefault(group, []).append(record)

    return {
        "configs": sorted(configs, key=lambda record: record["name"] or ""),
        "groups": {
            name: sorted(options, key=lambda record: record["name"] or "")
            for name, options in sorted(groups.items())
        },
    }


def compose(
    config_root: Path,
    name: str,
    overrides: Sequence[str],
    *,
    resolve: bool,
) -> CompositionResult:
    """Compose a logical config name with group operations before value mutations."""
    plan = _build_layer_plan(config_root, name)
    parsed = [
        _parse_override(config_root, plan, expression, index)
        for index, expression in enumerate(overrides)
    ]
    root_source = resolve_source_path(config_root, name).relative_to(config_root).as_posix()
    for operation in parsed:
        if operation.is_group:
            _apply_group_operation(config_root, plan, operation, root_source)

    data, provenance = _merge_layer_plan(plan)
    for operation in parsed:
        if not operation.is_group:
            _apply_value_operation(data, provenance, operation)
    if resolve:
        data = _resolve_interpolations(data)
    choices = tuple(
        {
            "group": choice.group,
            "option": copy.deepcopy(choice.option),
            "package": choice.package,
            "declared_by": choice.declared_by,
        }
        for choice in plan.choices
    )
    return CompositionResult(
        data=data,
        sources=tuple(layer.source for layer in plan.layers if layer.source is not None),
        choices=choices,
        provenance=provenance,
    )


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


def _build_layer_plan(config_root: Path, name: str) -> _LayerPlan:
    plan = _LayerPlan()
    _expand_file(config_root, normalize_logical_name(name), (), (), (), plan)
    return plan


def _expand_file(
    config_root: Path,
    name: str,
    package: tuple[str, ...],
    owners: tuple[int, ...],
    chain: tuple[str, ...],
    plan: _LayerPlan,
) -> None:
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

    saw_self = False
    next_chain = (*chain, relative)
    for index, item in enumerate(defaults):
        try:
            if item == "_self_":
                if saw_self:
                    raise ConfigError(f"Duplicate _self_ in defaults of '{relative}'")
                saw_self = True
                plan.layers.append(_Layer(relative, package, copy.deepcopy(document), owners))
            elif isinstance(item, str):
                include_name, include_package = _parse_config_include(item, relative, package)
                _expand_file(
                    config_root,
                    include_name,
                    include_package,
                    owners,
                    next_chain,
                    plan,
                )
            elif isinstance(item, dict) and len(item) == 1:
                raw_group, option = next(iter(item.items()))
                _expand_group_default(
                    config_root,
                    raw_group,
                    option,
                    relative,
                    package,
                    owners,
                    next_chain,
                    plan,
                )
            else:
                raise ConfigError(
                    f"Invalid defaults item {index} in '{relative}': expected _self_, "
                    "a config name, or a one-key group mapping"
                )
        except ConfigError as exc:
            if str(exc).startswith("Failed defaults item"):
                raise
            include_chain = " -> ".join(next_chain)
            raise ConfigError(
                f"Failed defaults item {index} {item!r} in '{relative}' "
                f"(include chain: {include_chain}): {exc}"
            ) from exc

    if not saw_self:
        plan.layers.append(_Layer(relative, package, copy.deepcopy(document), owners))


def _parse_config_include(
    item: str,
    declared_by: str,
    containing_package: tuple[str, ...],
) -> tuple[str, tuple[str, ...]]:
    raw_name, separator, raw_package = item.partition("@")
    if not raw_name or (separator and not raw_package):
        raise ConfigError(f"Invalid config include '{item}' in '{declared_by}'")
    source_parent = PurePosixPath(declared_by).parent
    is_absolute = raw_name.startswith("/")
    normalized_name = normalize_logical_name(raw_name[1:] if is_absolute else raw_name)
    if is_absolute:
        logical = normalized_name
        relative_parent = PurePosixPath(normalized_name).parent
        default_package = _path_package(relative_parent)
    else:
        logical_path = source_parent / PurePosixPath(normalized_name)
        logical = normalize_logical_name(logical_path.as_posix())
        relative_parent = PurePosixPath(normalized_name).parent
        default_package = containing_package + _path_package(relative_parent)
    package = (
        _resolve_package(raw_package, containing_package, default_package)
        if separator
        else default_package
    )
    return logical, package


def _expand_group_default(
    config_root: Path,
    raw_group: Any,
    option: Any,
    declared_by: str,
    containing_package: tuple[str, ...],
    owners: tuple[int, ...],
    chain: tuple[str, ...],
    plan: _LayerPlan,
) -> None:
    if not isinstance(raw_group, str) or not raw_group.strip():
        raise ConfigError("group name must be a nonempty string")
    key = raw_group.strip()
    modifier = ""
    for candidate in ("optional", "override"):
        prefix = f"{candidate} "
        if key.startswith(prefix):
            modifier = candidate
            key = key[len(prefix) :].strip()
            break
    raw_path, separator, raw_package = key.partition("@")
    if not raw_path or (separator and not raw_package):
        raise ConfigError(f"Invalid defaults group '{raw_group}' in '{declared_by}'")

    source_parent = PurePosixPath(declared_by).parent
    is_absolute = raw_path.startswith("/")
    local_group = normalize_logical_name(raw_path[1:] if is_absolute else raw_path)
    if is_absolute:
        absolute_group = local_group
        default_package = _path_package(PurePosixPath(local_group))
    else:
        absolute_group = normalize_logical_name((source_parent / local_group).as_posix())
        default_package = containing_package + _path_package(PurePosixPath(local_group))
    absolute_group_package = _path_package(PurePosixPath(absolute_group))
    destination = (
        _resolve_package(raw_package, containing_package, absolute_group_package)
        if separator
        else default_package
    )
    package_text = ".".join(destination)

    if option is None:
        options: list[str] = []
        recorded_option: str | list[str] | None = None
    elif isinstance(option, str) and option:
        options = [option]
        recorded_option = option
    elif (
        isinstance(option, list)
        and option
        and all(isinstance(value, str) and value for value in option)
    ):
        options = list(option)
        recorded_option = list(option)
    else:
        raise ConfigError("group option must be a nonempty string, list of strings, or null")
    if any("," in value for value in options):
        raise ConfigError("Comma-separated group choices are sweeps and require Hydra")

    if modifier == "override":
        plan.replace_selection(absolute_group, package_text, source=declared_by)

    selection_id = plan.allocate_selection_id()
    selection_owners = (*owners, selection_id)
    plan.choices.append(
        _Choice(
            selection_id,
            absolute_group,
            recorded_option,
            package_text,
            declared_by,
            selection_owners,
        )
    )
    plan.layers.append(_Layer(None, destination, {}, selection_owners))
    for selected_option in options:
        logical = f"{absolute_group}/{normalize_logical_name(selected_option)}"
        try:
            _expand_file(
                config_root,
                logical,
                destination,
                selection_owners,
                chain,
                plan,
            )
        except ConfigError as exc:
            if modifier == "optional" and " was not found under " in str(exc):
                continue
            raise


def _resolve_package(
    raw_package: str,
    containing_package: tuple[str, ...],
    group_package: tuple[str, ...],
) -> tuple[str, ...]:
    if raw_package == "_global_":
        return ()
    if raw_package == "_group_":
        return group_package
    if raw_package == "_here_":
        return containing_package
    if raw_package in _PACKAGE_KEYWORDS or raw_package.startswith("_"):
        raise ConfigError(f"Unknown defaults package keyword '{raw_package}'")
    parts = _package_parts(raw_package)
    return containing_package + parts


def _package_parts(value: str) -> tuple[str, ...]:
    normalized = value.replace("/", ".")
    parts = tuple(normalized.split("."))
    if any(not part or part in {".", ".."} for part in parts):
        raise ConfigError(f"Invalid defaults package '{value}'")
    return parts


def _path_package(path: PurePosixPath) -> tuple[str, ...]:
    return () if path == PurePosixPath(".") else tuple(path.parts)


def _merge_layer_plan(
    plan: _LayerPlan,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    result: dict[str, Any] = {}
    provenance: dict[str, dict[str, Any]] = {}
    for layer in plan.layers:
        if layer.source is None:
            continue
        destination = _ensure_package(result, layer.package, source=layer.source)
        _merge_with_provenance(
            destination,
            layer.data,
            layer.package,
            provenance,
            {"kind": "source", "path": layer.source},
        )
    return result, provenance


def _ensure_package(
    data: dict[str, Any], package: tuple[str, ...], *, source: str
) -> dict[str, Any]:
    cursor = data
    for part in package:
        child = cursor.get(part)
        if child is None:
            child = {}
            cursor[part] = child
        if not isinstance(child, dict):
            raise ConfigError(
                f"Config source '{source}' cannot merge package '{'.'.join(package)}' "
                f"through non-mapping key '{part}'"
            )
        cursor = child
    return cursor


def _merge_with_provenance(
    destination: dict[str, Any],
    incoming: Mapping[str, Any],
    path: tuple[str, ...],
    provenance: dict[str, dict[str, Any]],
    origin: dict[str, Any],
) -> None:
    for key, value in incoming.items():
        key_text = str(key)
        child_path = (*path, key_text)
        current = destination.get(key)
        if isinstance(value, Mapping):
            if not isinstance(current, dict):
                _clear_provenance(provenance, _json_pointer(child_path))
                current = {}
                destination[key] = current
            if value:
                _merge_with_provenance(current, value, child_path, provenance, origin)
            else:
                _clear_provenance(provenance, _json_pointer(child_path))
                provenance[_json_pointer(child_path)] = copy.deepcopy(origin)
            continue
        destination[key] = copy.deepcopy(value)
        pointer = _json_pointer(child_path)
        _clear_provenance(provenance, pointer)
        _record_leaf_provenance(value, child_path, provenance, origin)


def _record_leaf_provenance(
    value: Any,
    path: tuple[str, ...],
    provenance: dict[str, dict[str, Any]],
    origin: dict[str, Any],
) -> None:
    if isinstance(value, Mapping):
        if value:
            for key, child in value.items():
                _record_leaf_provenance(
                    child,
                    (*path, str(key)),
                    provenance,
                    origin,
                )
            return
    elif isinstance(value, list):
        if value:
            for index, child in enumerate(value):
                _record_leaf_provenance(
                    child,
                    (*path, str(index)),
                    provenance,
                    origin,
                )
            return
    provenance[_json_pointer(path)] = copy.deepcopy(origin)


def _clear_provenance(
    provenance: dict[str, dict[str, Any]],
    pointer: str,
) -> None:
    descendant_prefix = f"{pointer}/"
    for existing in tuple(provenance):
        if existing == pointer or existing.startswith(descendant_prefix):
            del provenance[existing]


def _json_pointer(path: tuple[str, ...]) -> str:
    return "".join(f"/{part.replace('~', '~0').replace('/', '~1')}" for part in path)


def _parse_override(
    config_root: Path,
    plan: _LayerPlan,
    expression: str,
    index: int,
) -> _ParsedOverride:
    if not isinstance(expression, str) or not expression:
        raise OverrideError(f"Invalid override {expression!r}")
    if expression.startswith("++"):
        operator = "++"
        remainder = expression[2:]
    elif expression[0] in {"+", "~"}:
        operator = expression[0]
        remainder = expression[1:]
    else:
        operator = "="
        remainder = expression

    target, separator, raw_value = remainder.partition("=")
    if not target or target != target.strip():
        raise OverrideError(f"Invalid override path '{target}' in '{expression}'")
    if operator != "~" and not separator:
        raise OverrideError(f"Invalid override '{expression}': expected path=value")
    value = raw_value if separator else None

    group_name, package = _override_group_key(target)
    is_group = False
    if group_name is not None:
        group_dir = config_root.joinpath(*PurePosixPath(group_name).parts)
        directory_exists = (
            group_dir.exists()
            and group_dir.is_dir()
            and group_dir.resolve().is_relative_to(config_root)
        )
        package_text = ".".join(package)
        selected = any(
            choice.group == group_name and choice.package == package_text for choice in plan.choices
        )
        is_group = directory_exists or selected or "@" in target

    if is_group:
        if operator == "++":
            raise OverrideError(
                f"Invalid group override '{expression}': use group=option or +group=option"
            )
        if operator == "~" and separator:
            raise OverrideError(
                f"Invalid group override '{expression}': group deletion does not take a value"
            )
        if value is not None and (
            "," in value or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\\(.*\\)", value)
        ):
            raise OverrideError(
                f"Override '{expression}' is a sweep or override function and requires Hydra"
            )
        return _ParsedOverride(
            expression,
            index,
            operator,
            target,
            value,
            True,
            group_name,
            package,
        )

    parts = target.split(".")
    if any(not part or part in {".", ".."} for part in parts) or "/" in target or "@" in target:
        raise OverrideError(f"Invalid override path '{target}' in '{expression}'")
    return _ParsedOverride(expression, index, operator, target, value, False)


def _override_group_key(target: str) -> tuple[str | None, tuple[str, ...]]:
    raw_group, separator, raw_package = target.partition("@")
    if "@" in raw_package:
        raise OverrideError(f"Invalid config group target '{target}'")
    if "." in raw_group or not raw_group:
        return None, ()
    try:
        group = normalize_logical_name(raw_group.lstrip("/"))
        group_package = _path_package(PurePosixPath(group))
        package = _resolve_package(raw_package, (), group_package) if separator else group_package
    except ConfigError as exc:
        raise OverrideError(f"Invalid config group target '{target}': {exc}") from exc
    return group, package


def _apply_group_operation(
    config_root: Path,
    plan: _LayerPlan,
    operation: _ParsedOverride,
    root_source: str,
) -> None:
    assert operation.group is not None
    package_text = ".".join(operation.package)
    selected = next(
        (
            choice
            for choice in reversed(plan.choices)
            if choice.group == operation.group and choice.package == package_text
        ),
        None,
    )
    if operation.operator == "~":
        if selected is None:
            raise OverrideError(
                f"Group override '{operation.expression}' references unselected group "
                f"'{operation.group}' package '{package_text}'"
            )
        _remove_plan_selection(plan, selected.selection_id)
        return
    if operation.operator == "+" and selected is not None:
        raise OverrideError(
            f"Group override '{operation.expression}' cannot add already selected group "
            f"'{operation.group}' package '{package_text}'"
        )
    if operation.operator == "=" and selected is None:
        raise OverrideError(
            f"Group override '{operation.expression}' references unselected group "
            f"'{operation.group}' package '{package_text}'"
        )
    if not operation.raw_value:
        raise OverrideError(f"Group override '{operation.expression}' requires a nonempty option")

    declared_by = selected.declared_by if selected is not None else root_source
    owners = (
        tuple(owner for owner in selected.owners if owner != selected.selection_id)
        if selected is not None
        else ()
    )
    layer_index = len(plan.layers)
    choice_index = len(plan.choices)
    if selected is not None:
        layer_positions = [
            index
            for index, layer in enumerate(plan.layers)
            if selected.selection_id in layer.owners
        ]
        choice_positions = [
            index
            for index, choice in enumerate(plan.choices)
            if selected.selection_id in choice.owners
        ]
        if layer_positions:
            layer_index = layer_positions[0]
        if choice_positions:
            choice_index = choice_positions[0]
        _remove_plan_selection(plan, selected.selection_id)

    before_layers = len(plan.layers)
    before_choices = len(plan.choices)
    selection_id = plan.allocate_selection_id()
    selection_owners = (*owners, selection_id)
    plan.choices.append(
        _Choice(
            selection_id,
            operation.group,
            operation.raw_value,
            package_text,
            declared_by,
            selection_owners,
        )
    )
    plan.layers.append(_Layer(None, operation.package, {}, selection_owners))
    try:
        option = normalize_logical_name(operation.raw_value)
        _expand_file(
            config_root,
            f"{operation.group}/{option}",
            operation.package,
            selection_owners,
            (),
            plan,
        )
    except ConfigError as exc:
        raise OverrideError(
            f"Unknown option '{operation.raw_value}' for config group '{operation.group}': {exc}"
        ) from exc

    if selected is not None:
        added_layers = plan.layers[before_layers:]
        del plan.layers[before_layers:]
        plan.layers[layer_index:layer_index] = added_layers
        added_choices = plan.choices[before_choices:]
        del plan.choices[before_choices:]
        plan.choices[choice_index:choice_index] = added_choices


def _remove_plan_selection(plan: _LayerPlan, selection_id: int) -> None:
    plan.layers[:] = [layer for layer in plan.layers if selection_id not in layer.owners]
    plan.choices[:] = [choice for choice in plan.choices if selection_id not in choice.owners]


def _apply_value_operation(
    data: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
    operation: _ParsedOverride,
) -> None:
    parts = operation.target.split(".")
    create_parents = operation.operator in {"+", "++"}
    cursor = data
    for part in parts[:-1]:
        if part not in cursor:
            if not create_parents:
                raise OverrideError(
                    f"Override '{operation.expression}' references missing path "
                    f"'{operation.target}'"
                )
            cursor[part] = {}
        child = cursor[part]
        if not isinstance(child, dict):
            raise OverrideError(
                f"Override '{operation.expression}' cannot traverse non-mapping key '{part}'"
            )
        cursor = child

    leaf = parts[-1]
    exists = leaf in cursor
    if operation.operator == "~":
        if not exists:
            raise OverrideError(
                f"Override '{operation.expression}' references missing path '{operation.target}'"
            )
        if operation.raw_value is not None:
            expected = _parse_override_value(operation)
            if cursor[leaf] != expected:
                raise OverrideError(
                    f"Conditional delete '{operation.expression}' expected "
                    f"{expected!r}, found {cursor[leaf]!r}"
                )
        del cursor[leaf]
        _clear_provenance(provenance, _json_pointer(tuple(parts)))
        return
    if operation.operator == "+" and exists:
        raise OverrideError(
            f"Override '{operation.expression}' cannot create existing path '{operation.target}'"
        )
    if operation.operator == "=" and not exists:
        raise OverrideError(
            f"Override '{operation.expression}' references missing path '{operation.target}'"
        )

    value = _parse_override_value(operation)
    cursor[leaf] = copy.deepcopy(value)
    pointer_path = tuple(parts)
    _clear_provenance(provenance, _json_pointer(pointer_path))
    _record_leaf_provenance(
        value,
        pointer_path,
        provenance,
        {
            "kind": "override",
            "index": operation.index,
            "expression": operation.expression,
        },
    )


def _parse_override_value(operation: _ParsedOverride) -> Any:
    assert operation.raw_value is not None
    if operation.raw_value == "":
        return ""
    try:
        return yaml.safe_load(operation.raw_value)
    except yaml.YAMLError as exc:
        raise OverrideError(
            f"Invalid YAML value in override '{operation.expression}': {exc}"
        ) from exc


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
