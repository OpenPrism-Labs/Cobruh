"""Explicit project API for Cobruh."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from cobruh.composition import CompositionResult
from cobruh.composition import catalog as build_catalog
from cobruh.composition import compose as compose_config
from cobruh.errors import ConfigError


class Cobruh:
    """A stateless view of one project's configuration tree."""

    def __init__(
        self,
        config_root: str | Path,
        *,
        project_root: str | Path | None = None,
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

    def catalog(self) -> dict[str, object]:
        """List root configs and grouped options deterministically."""
        return build_catalog(self.config_root)

    def compose(
        self,
        name: str = "config",
        *,
        overrides: Sequence[str] = (),
        resolve: bool = True,
    ) -> dict[str, Any]:
        """Compose one config into ordinary Python mappings and sequences."""
        return self._compose_result(name, overrides=overrides, resolve=resolve).data

    def instantiate(
        self,
        config: Mapping[str, Any],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Instantiate a target mapping relative to this project."""
        from cobruh.runtime import instantiate

        return instantiate(self.project_root, config, *args, **kwargs)

    def _compose_result(
        self,
        name: str = "config",
        *,
        overrides: Sequence[str] = (),
        resolve: bool = True,
    ) -> CompositionResult:
        return compose_config(
            self.config_root,
            name,
            overrides,
            resolve=resolve,
        )
