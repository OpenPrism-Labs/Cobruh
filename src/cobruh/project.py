"""Explicit project API for Cobruh."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from cobruh._adapter import select_value
from cobruh.composition import CompositionResult, normalize_logical_name
from cobruh.composition import catalog as build_catalog
from cobruh.composition import compose as compose_config
from cobruh.errors import ConfigError
from cobruh.validation import (
    SchemaRegistration,
    build_type_metadata,
    normalize_schemas,
    validate_composition,
)


class Cobruh:
    """A stateless view of one project's configuration tree."""

    def __init__(
        self,
        config_root: str | Path,
        *,
        project_root: str | Path | None = None,
        schemas: Mapping[str, Mapping[str, Any] | str | Path] | None = None,
        allowed_targets: Sequence[str] = (),
    ) -> None:
        resolved_config_root = Path(config_root).expanduser().resolve()
        resolved_project_root = (
            Path(project_root).expanduser().resolve()
            if project_root is not None
            else resolved_config_root.parent
        )
        if not resolved_config_root.is_dir():
            raise ConfigError(f"Config root '{resolved_config_root}' must be an existing directory")
        if not resolved_project_root.is_dir():
            raise ConfigError(
                f"Project root '{resolved_project_root}' must be an existing directory"
            )
        if not resolved_config_root.is_relative_to(resolved_project_root):
            raise ConfigError(
                f"Config root '{resolved_config_root}' must be contained by project root "
                f"'{resolved_project_root}'"
            )
        self.config_root = resolved_config_root
        self.project_root = resolved_project_root
        self._schemas = normalize_schemas(self.project_root, schemas)
        from cobruh.runtime import normalize_allowed_targets

        self.allowed_targets = normalize_allowed_targets(allowed_targets)

    def catalog(self) -> dict[str, object]:
        """List root configs and grouped options deterministically."""
        return build_catalog(
            self.config_root,
            {name: registration.source for name, registration in self._schemas.items()},
        )

    def compose(
        self,
        name: str = "config",
        *,
        overrides: Sequence[str] = (),
        resolve: bool = True,
    ) -> dict[str, Any]:
        """Compose one config into ordinary Python mappings and sequences."""
        return self._compose_result(name, overrides=overrides, resolve=resolve).data

    def inspect(
        self,
        name: str = "config",
        *,
        overrides: Sequence[str] = (),
        resolve: bool = True,
        node: str = "",
    ) -> dict[str, Any]:
        """Compose and return focused agent-readable metadata."""
        normalized_name = normalize_logical_name(name)
        result = self._compose_result(
            normalized_name,
            overrides=overrides,
            resolve=resolve,
        )
        selected = select_value(result.data, node)
        node_parts = tuple(node.split(".")) if node else ()
        registration = self._schemas.get(normalized_name)
        provenance = _focus_pointers(result.provenance, node_parts)
        types = build_type_metadata(selected, registration, node_parts)
        validation: dict[str, Any]
        if registration is None:
            validation = {"status": "not_configured"}
        elif resolve:
            validation = {"status": "valid", "schema": registration.source}
        else:
            validation = {
                "status": "skipped",
                "schema": registration.source,
                "reason": "resolve=false",
            }
        return {
            "name": normalized_name,
            "node": node,
            "data": selected,
            "sources": list(result.sources),
            "choices": [dict(choice) for choice in result.choices],
            "provenance": provenance,
            "types": types,
            "validation": validation,
        }

    def instantiate(
        self,
        config: Mapping[str, Any],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Instantiate a target mapping relative to this project."""
        from cobruh.runtime import instantiate

        return instantiate(self.project_root, self.allowed_targets, config, *args, **kwargs)

    def _compose_result(
        self,
        name: str = "config",
        *,
        overrides: Sequence[str] = (),
        resolve: bool = True,
    ) -> CompositionResult:
        normalized_name = normalize_logical_name(name)
        result = compose_config(
            self.config_root,
            normalized_name,
            overrides,
            resolve=resolve,
        )
        registration = self._schemas.get(normalized_name)
        if resolve and registration is not None:
            validate_composition(normalized_name, result.data, registration)
        return result

    def _schema_registration(self, name: str) -> SchemaRegistration | None:
        return self._schemas.get(normalize_logical_name(name))


def _focus_pointers(
    pointers: Mapping[str, Mapping[str, Any]],
    node_parts: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    if not node_parts:
        return {pointer: dict(value) for pointer, value in pointers.items()}
    prefix = "".join(f"/{part.replace('~', '~0').replace('/', '~1')}" for part in node_parts)
    focused: dict[str, dict[str, Any]] = {}
    for pointer, value in pointers.items():
        if pointer == prefix:
            focused[""] = dict(value)
        elif pointer.startswith(f"{prefix}/"):
            focused[pointer[len(prefix) :]] = dict(value)
    return focused
