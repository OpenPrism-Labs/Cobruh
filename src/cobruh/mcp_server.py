"""Optional full-authority MCP adapter for trusted local coding agents."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from mcp.server import MCPServer

from cobruh import Cobruh, CobruhError, __version__
from cobruh._adapter import result_envelope, select_mapping
from cobruh.composition import MAX_SOURCE_BYTES
from cobruh.errors import ConfigError

_SERVER_INSTRUCTIONS = """Cobruh manages configuration for a trusted local project.
This server can inspect schemas, provenance, choices, and focused composed values; write
project configuration; and instantiate explicitly allowed Python targets. Catalog and read
before editing, use expected SHA-256 hashes for replacements, inspect after writes, and
instantiate only when the user explicitly intends authorized target code to execute.
"""


def create_server(project: Cobruh) -> MCPServer:
    """Create a Cobruh MCP server bound to one explicit project."""
    server = MCPServer(
        "Cobruh",
        version=__version__,
        instructions=_SERVER_INSTRUCTIONS,
    )

    @server.tool()
    def list_configs() -> dict[str, Any]:
        """List root configurations and grouped options."""
        try:
            return _ok(catalog=project.catalog())
        except Exception as exc:
            return _failure(exc)

    @server.tool()
    def read_config_source(path: str) -> dict[str, Any]:
        """Read a root-relative YAML source with its replacement hash."""
        try:
            source = _source_path(project.config_root, path, must_exist=True)
            size = source.stat().st_size
            if size > MAX_SOURCE_BYTES:
                raise ConfigError(
                    f"Config source '{path}' is {size} bytes; limit is {MAX_SOURCE_BYTES} bytes"
                )
            content = source.read_text(encoding="utf-8")
            return _ok(
                path=source.relative_to(project.config_root).as_posix(),
                content=content,
                sha256=_sha256(content.encode("utf-8")),
            )
        except Exception as exc:
            return _failure(exc)

    @server.tool()
    def write_config_source(
        path: str,
        content: str,
        expected_sha256: str | None = None,
    ) -> dict[str, Any]:
        """Atomically create or hash-guardedly replace a root-relative YAML source."""
        try:
            relative, digest = _write_source(
                project.config_root,
                path,
                content,
                expected_sha256=expected_sha256,
            )
            return _ok(path=relative, sha256=digest)
        except Exception as exc:
            return _failure(exc)

    @server.tool()
    def compose_config(
        name: str = "config",
        node: str = "",
        overrides: list[str] | None = None,
        resolve: bool = True,
    ) -> dict[str, Any]:
        """Inspect composed data, choices, provenance, types, and validation."""
        try:
            return _ok(
                **project.inspect(
                    name,
                    node=node,
                    overrides=overrides or (),
                    resolve=resolve,
                )
            )
        except Exception as exc:
            return _failure(exc)

    @server.tool()
    def instantiate_config(
        name: str = "config",
        node: str = "",
        overrides: list[str] | None = None,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compose and execute an intended target mapping in the trusted project."""
        try:
            data = project.compose(name, overrides=overrides or ())
            selected = select_mapping(data, node)
            result = project.instantiate(selected, *(args or ()), **(kwargs or {}))
            return _ok(result=result_envelope(result))
        except Exception as exc:
            return _failure(exc)

    @server.resource("cobruh://catalog")
    def catalog_resource() -> str:
        """Current deterministic Cobruh configuration catalog."""
        return json.dumps(project.catalog(), indent=2, sort_keys=True)

    @server.resource("cobruh://skills")
    def skills_resource() -> str:
        """Bundled portable Agent Skills available from this installation."""
        from cobruh.skills import list_skills

        return json.dumps({"skills": list_skills()}, indent=2, sort_keys=True)

    @server.prompt()
    def author_config(goal: str, config_name: str = "config") -> str:
        """Safely author and verify Cobruh configuration for a stated goal."""
        return (
            f"Author Cobruh configuration '{config_name}' for this goal: {goal}\n\n"
            "Call list_configs first. Read every source you plan to change and retain its "
            "SHA-256. Use write_config_source with expected_sha256 for replacements (omit it "
            "only for creation), then call compose_config to inspect validation, choices, and "
            "provenance. Call instantiate_config only if the user intends authorized target "
            "code to execute."
        )

    @server.prompt()
    def debug_config(error: str, config_name: str = "config") -> str:
        """Diagnose a Cobruh error using sources and deterministic composition."""
        return (
            f"Debug Cobruh configuration '{config_name}' reporting: {error}\n\n"
            "Call list_configs and compose_config before editing; inspect focused nodes and "
            "their provenance and schema types. Read implicated sources and retain their "
            "SHA-256 values. Make replacements only with hash-guarded write_config_source, "
            "compose again after each change, and call instantiate_config only if the user "
            "intends authorized target code to execute."
        )

    return server


def _ok(**payload: Any) -> dict[str, Any]:
    return {"ok": True, **payload}


def _failure(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, CobruhError):
        error_type = type(exc).__name__
    elif isinstance(exc, (OSError, UnicodeError, ValueError, yaml.YAMLError)):
        error_type = type(exc).__name__
    else:
        error_type = type(exc).__name__
    return {"ok": False, "error": {"type": error_type, "message": str(exc)}}


def _source_path(config_root: Path, path: str, *, must_exist: bool) -> Path:
    if not isinstance(path, str) or not path:
        raise ConfigError(f"Invalid empty config source path: {path!r}")
    if "\\" in path:
        raise ConfigError(f"Config source path '{path}' must use '/' separators")
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ConfigError(f"Config source path '{path}' must be root-relative without traversal")
    if pure.suffix not in {".yaml", ".yml"}:
        raise ConfigError(f"Config source path '{path}' must end in .yaml or .yml")

    candidate = config_root.joinpath(*pure.parts)
    _validate_parent_chain(config_root, candidate.parent)
    if candidate.exists() or candidate.is_symlink():
        if candidate.is_symlink():
            raise ConfigError(f"Config source path '{path}' must not be a symlink")
        if not candidate.is_file():
            raise ConfigError(f"Config source path '{path}' must be a regular file")
        if not candidate.resolve().is_relative_to(config_root):
            raise ConfigError(f"Config source path '{path}' escapes config root '{config_root}'")
    elif must_exist:
        raise ConfigError(f"Config source path '{path}' does not exist")
    return candidate


def _validate_parent_chain(config_root: Path, parent: Path) -> None:
    try:
        relative = parent.relative_to(config_root)
    except ValueError as exc:
        raise ConfigError(f"Config source parent '{parent}' is outside '{config_root}'") from exc
    cursor = config_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ConfigError(
                f"Config source parent '{cursor.relative_to(config_root).as_posix()}' "
                "must not be a symlink"
            )
        if cursor.exists() and not cursor.is_dir():
            raise ConfigError(
                f"Config source parent '{cursor.relative_to(config_root).as_posix()}' "
                "must be a directory"
            )
        if cursor.exists() and not cursor.resolve().is_relative_to(config_root):
            raise ConfigError(
                f"Config source parent '{cursor}' escapes config root '{config_root}'"
            )


def _write_source(
    config_root: Path,
    path: str,
    content: str,
    *,
    expected_sha256: str | None,
) -> tuple[str, str]:
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_SOURCE_BYTES:
        raise ConfigError(
            f"Config source '{path}' is {len(encoded)} bytes; limit is {MAX_SOURCE_BYTES} bytes"
        )
    try:
        loaded = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Malformed YAML for config source '{path}': {exc}") from exc
    if loaded is not None and not isinstance(loaded, dict):
        raise ConfigError(
            f"Config source '{path}' must contain a mapping, got {type(loaded).__name__}"
        )

    target = _source_path(config_root, path, must_exist=False)
    exists = target.exists()
    if exists:
        current = target.read_bytes()
        current_sha256 = _sha256(current)
        if expected_sha256 is None:
            raise ConfigError(
                f"Replacing config source '{path}' requires its current expected_sha256"
            )
        if expected_sha256 != current_sha256:
            raise ConfigError(
                f"Stale SHA-256 for config source '{path}': expected {expected_sha256}, "
                f"current {current_sha256}"
            )
    elif expected_sha256 is not None:
        raise ConfigError(f"Creating config source '{path}' requires expected_sha256 to be omitted")

    _validate_parent_chain(config_root, target.parent)
    created_parents: list[Path] = []
    cursor = config_root
    for part in target.parent.relative_to(config_root).parts:
        cursor = cursor / part
        if not cursor.exists():
            cursor.mkdir()
            created_parents.append(cursor)

    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, target)
        temporary_path = None
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        if not exists:
            target.unlink(missing_ok=True)
            for parent in reversed(created_parents):
                try:
                    parent.rmdir()
                except OSError:
                    break
        raise

    return target.relative_to(config_root).as_posix(), _sha256(encoded)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
