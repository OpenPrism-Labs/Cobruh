"""Project-bound Draft 2020-12 JSON Schema loading and validation."""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from cobruh.composition import normalize_logical_name
from cobruh.errors import ConfigError

MAX_SCHEMA_BYTES = 1024 * 1024
_MAX_VALIDATION_ERRORS = 20


@dataclass(frozen=True)
class SchemaRegistration:
    """One normalized, validated schema and its public source label."""

    schema: dict[str, Any]
    source: str


def normalize_schemas(
    project_root: Path,
    schemas: Mapping[str, Mapping[str, Any] | str | Path] | None,
) -> dict[str, SchemaRegistration]:
    """Validate and defensively copy project schema registrations."""
    registrations: dict[str, SchemaRegistration] = {}
    if schemas is None:
        return registrations
    if not isinstance(schemas, Mapping):
        raise ConfigError("Schemas must be a mapping from config names to schemas")

    for raw_name, value in schemas.items():
        try:
            name = normalize_logical_name(raw_name)
        except ConfigError as exc:
            raise ConfigError(f"Invalid schema config name {raw_name!r}: {exc}") from exc
        if name in registrations:
            raise ConfigError(f"Duplicate schema registration for normalized config name '{name}'")
        if isinstance(value, Mapping):
            schema = copy.deepcopy(dict(value))
            source = "<memory>"
        elif isinstance(value, (str, Path)):
            schema, source = _load_schema_path(project_root, value)
        else:
            raise ConfigError(
                f"Schema for config '{name}' must be a mapping or JSON path, "
                f"got {type(value).__name__}"
            )
        _validate_schema_document(name, schema, source)
        registrations[name] = SchemaRegistration(schema=schema, source=source)
    return registrations


def validate_composition(
    name: str,
    data: Any,
    registration: SchemaRegistration,
) -> None:
    """Raise one deterministic configuration error for invalid composed data."""
    validator = Draft202012Validator(registration.schema)
    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: (
            _json_pointer(error.absolute_path),
            _json_pointer(error.absolute_schema_path),
            error.message,
        ),
    )
    if not errors:
        return

    displayed = errors[:_MAX_VALIDATION_ERRORS]
    details = "; ".join(
        f"instance '{_json_pointer(error.absolute_path)}' "
        f"schema '{_json_pointer(error.absolute_schema_path)}': {error.message}"
        for error in displayed
    )
    omitted = len(errors) - len(displayed)
    if omitted:
        details += f"; {omitted} additional validation error(s) omitted"
    raise ConfigError(
        f"Config '{name}' failed validation against schema '{registration.source}': {details}"
    )


def build_type_metadata(
    data: Any,
    registration: SchemaRegistration | None,
    node_parts: tuple[str, ...] = (),
) -> dict[str, dict[str, Any]]:
    """Describe every selected data node from a schema or inferred JSON types."""
    result: dict[str, dict[str, Any]] = {}
    if registration is None:
        _walk_inferred_types(data, (), result)
        return result
    selected_schema = _schema_at_node(registration.schema, node_parts)
    _walk_schema_types(
        data,
        selected_schema,
        registration.schema,
        (),
        True,
        result,
    )
    return result


def _walk_inferred_types(
    value: Any,
    path: tuple[str, ...],
    result: dict[str, dict[str, Any]],
) -> None:
    result[_json_pointer(path)] = {"source": "inferred", "type": _json_type(value)}
    if isinstance(value, Mapping):
        for key, child in value.items():
            _walk_inferred_types(child, (*path, str(key)), result)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_inferred_types(child, (*path, str(index)), result)


def _walk_schema_types(
    value: Any,
    schema: Mapping[str, Any],
    root_schema: Mapping[str, Any],
    path: tuple[str, ...],
    required: bool,
    result: dict[str, dict[str, Any]],
) -> None:
    resolved = _resolve_schema_ref(schema, root_schema, ())
    public_schema = {
        key: copy.deepcopy(child)
        for key, child in resolved.items()
        if key not in {"properties", "items", "$defs"}
    }
    result[_json_pointer(path)] = {
        "source": "schema",
        "required": required,
        "schema": public_schema,
    }
    if isinstance(value, Mapping):
        properties = resolved.get("properties", {})
        property_schemas = properties if isinstance(properties, Mapping) else {}
        required_names = resolved.get("required", [])
        required_set = set(required_names) if isinstance(required_names, list) else set()
        additional = resolved.get("additionalProperties", {})
        for key, child in value.items():
            child_schema = property_schemas.get(key, additional)
            if not isinstance(child_schema, Mapping):
                child_schema = {}
            _walk_schema_types(
                child,
                child_schema,
                root_schema,
                (*path, str(key)),
                key in required_set,
                result,
            )
    elif isinstance(value, list):
        item_schema = resolved.get("items", {})
        if not isinstance(item_schema, Mapping):
            item_schema = {}
        for index, child in enumerate(value):
            _walk_schema_types(
                child,
                item_schema,
                root_schema,
                (*path, str(index)),
                False,
                result,
            )


def _schema_at_node(
    root_schema: Mapping[str, Any],
    parts: tuple[str, ...],
) -> Mapping[str, Any]:
    schema = root_schema
    for part in parts:
        resolved = _resolve_schema_ref(schema, root_schema, ())
        properties = resolved.get("properties", {})
        if not isinstance(properties, Mapping):
            return {}
        child = properties.get(part, resolved.get("additionalProperties", {}))
        if not isinstance(child, Mapping):
            return {}
        schema = child
    return schema


def _resolve_schema_ref(
    schema: Mapping[str, Any],
    root_schema: Mapping[str, Any],
    seen: tuple[str, ...],
) -> dict[str, Any]:
    reference = schema.get("$ref")
    if not isinstance(reference, str):
        return dict(schema)
    if reference in seen:
        return {key: value for key, value in schema.items() if key != "$ref"}
    target: Any = root_schema
    fragment = reference[1:]
    if fragment:
        if not fragment.startswith("/"):
            return dict(schema)
        for encoded in fragment[1:].split("/"):
            part = encoded.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, Mapping) or part not in target:
                return dict(schema)
            target = target[part]
    if not isinstance(target, Mapping):
        return dict(schema)
    resolved = _resolve_schema_ref(target, root_schema, (*seen, reference))
    resolved.update(schema)
    return resolved


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, Mapping):
        return "object"
    return type(value).__name__


def _load_schema_path(
    project_root: Path,
    value: str | Path,
) -> tuple[dict[str, Any], str]:
    path = Path(value).expanduser()
    candidate = path if path.is_absolute() else project_root / path
    candidate = candidate.absolute()
    try:
        relative = candidate.relative_to(project_root)
    except ValueError as exc:
        raise ConfigError(
            f"Schema path '{value}' must be contained by project root '{project_root}'"
        ) from exc
    if candidate.suffix.lower() != ".json":
        raise ConfigError(f"Schema path '{relative.as_posix()}' must use .json")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(project_root):
        raise ConfigError(
            f"Schema path '{relative.as_posix()}' escapes project root '{project_root}'"
        )
    if not resolved.is_file():
        raise ConfigError(f"Schema path '{relative.as_posix()}' must be an existing regular file")
    size = resolved.stat().st_size
    if size > MAX_SCHEMA_BYTES:
        raise ConfigError(
            f"Schema '{relative.as_posix()}' is {size} bytes; limit is {MAX_SCHEMA_BYTES} bytes"
        )
    try:
        content = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ConfigError(f"Cannot read schema '{relative.as_posix()}': {exc}") from exc
    try:
        loaded = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Malformed JSON in schema '{relative.as_posix()}': {exc}") from exc
    if not isinstance(loaded, dict):
        raise ConfigError(
            f"Schema '{relative.as_posix()}' must contain a mapping, got {type(loaded).__name__}"
        )
    return loaded, relative.as_posix()


def _validate_schema_document(name: str, schema: dict[str, Any], source: str) -> None:
    _reject_external_refs(schema, ())
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        pointer = _json_pointer(exc.absolute_schema_path)
        raise ConfigError(
            f"Invalid schema '{source}' for config '{name}' at schema '{pointer}': {exc.message}"
        ) from exc


def _reject_external_refs(value: Any, path: tuple[str, ...]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = (*path, str(key))
            if key == "$ref" and (not isinstance(child, str) or not child.startswith("#")):
                raise ConfigError(
                    f"Schema $ref at '{_json_pointer(child_path)}' must be a local '#...' fragment"
                )
            _reject_external_refs(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_external_refs(child, (*path, str(index)))


def _json_pointer(path: Any) -> str:
    return "".join(f"/{str(part).replace('~', '~0').replace('/', '~1')}" for part in path)
