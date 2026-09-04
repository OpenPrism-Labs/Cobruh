"""Discovery and transactional installation of bundled Agent Skills."""

from __future__ import annotations

import os
import secrets
import shutil
import tempfile
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal

from cobruh.errors import ConfigError

Agent = Literal["codex", "claude", "copilot", "cursor", "all"]
Scope = Literal["project", "user"]

_PROJECT_DESTINATIONS = {
    "codex": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
    "copilot": Path(".github/skills"),
    "cursor": Path(".cursor/skills"),
}
_USER_DESTINATIONS = {
    "codex": Path(".agents/skills"),
    "claude": Path(".claude/skills"),
    "copilot": Path(".copilot/skills"),
    "cursor": Path(".cursor/skills"),
}


@dataclass
class _Operation:
    target: Path
    content: dict[str, bytes]
    replace: bool
    backup: Path | None = None
    created_parents: tuple[Path, ...] = ()


def list_skills() -> list[str]:
    """Return bundled skill names in deterministic order."""
    root = files("cobruh").joinpath("_skills")
    return sorted(
        entry.name
        for entry in root.iterdir()
        if entry.is_dir() and entry.joinpath("SKILL.md").is_file()
    )


def install_skills(
    *,
    agent: Agent,
    scope: Scope = "project",
    project: Path = Path("."),
    names: list[str] | None = None,
    force: bool = False,
) -> list[str]:
    """Install selected bundled skills atomically across requested agents."""
    available = list_skills()
    selected = available if not names else _normalize_names(names, available)
    agents = list(_PROJECT_DESTINATIONS) if agent == "all" else [agent]
    if any(name not in _PROJECT_DESTINATIONS for name in agents):
        raise ConfigError(f"Unknown skill agent '{agent}'")
    if scope not in {"project", "user"}:
        raise ConfigError(f"Unknown skill scope '{scope}'")

    package_root = files("cobruh").joinpath("_skills")
    bundled = {name: _resource_content(package_root.joinpath(name)) for name in selected}
    base = Path.home().resolve() if scope == "user" else Path(project).resolve()
    destinations = _USER_DESTINATIONS if scope == "user" else _PROJECT_DESTINATIONS

    operations: list[_Operation] = []
    expected: list[str] = []
    for agent_name in agents:
        destination_root = base / destinations[agent_name]
        _preflight_parent_chain(base, destination_root)
        for name in selected:
            target = destination_root / name
            expected.append(str(target))
            if target.is_symlink():
                raise ConfigError(f"Skill destination '{target}' must not be a symlink")
            if target.exists():
                if not target.is_dir():
                    raise ConfigError(f"Skill destination '{target}' must be a directory")
                if _directory_content(target) == bundled[name]:
                    continue
                if not force:
                    raise ConfigError(
                        f"Skill destination '{target}' differs from bundled content; use --force"
                    )
                operations.append(_Operation(target, bundled[name], replace=True))
            else:
                operations.append(_Operation(target, bundled[name], replace=False))

    applied: list[_Operation] = []
    try:
        for operation in operations:
            operation.created_parents = _create_parents(base, operation.target.parent)
            stage = Path(
                tempfile.mkdtemp(
                    prefix=f".{operation.target.name}.stage-",
                    dir=operation.target.parent,
                )
            )
            try:
                _write_content(stage, operation.content)
                if operation.replace:
                    backup = operation.target.parent / (
                        f".{operation.target.name}.backup-{secrets.token_hex(8)}"
                    )
                    os.replace(operation.target, backup)
                    operation.backup = backup
                os.replace(stage, operation.target)
            except Exception:
                shutil.rmtree(stage, ignore_errors=True)
                if operation.backup is not None and not operation.target.exists():
                    os.replace(operation.backup, operation.target)
                    operation.backup = None
                _remove_empty_parents(operation.created_parents)
                raise
            applied.append(operation)
    except Exception:
        for operation in reversed(applied):
            if operation.target.exists() and not operation.target.is_symlink():
                shutil.rmtree(operation.target)
            if operation.backup is not None:
                os.replace(operation.backup, operation.target)
                operation.backup = None
            _remove_empty_parents(operation.created_parents)
        raise

    for operation in applied:
        if operation.backup is not None:
            shutil.rmtree(operation.backup)
    return expected


def _normalize_names(names: list[str], available: list[str]) -> list[str]:
    selected: list[str] = []
    for name in names:
        if name not in available:
            raise ConfigError(f"Unknown bundled skill '{name}'; available: {', '.join(available)}")
        if name not in selected:
            selected.append(name)
    return selected


def _resource_content(root: Any) -> dict[str, bytes]:
    content: dict[str, bytes] = {}

    def visit(entry: Any, prefix: str = "") -> None:
        for child in sorted(entry.iterdir(), key=lambda item: item.name):
            relative = f"{prefix}/{child.name}" if prefix else child.name
            if child.is_dir():
                visit(child, relative)
            elif child.is_file():
                content[relative] = child.read_bytes()

    visit(root)
    return content


def _directory_content(root: Path) -> dict[str, bytes]:
    content: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ConfigError(f"Installed skill '{root}' contains symlink '{path}'")
        if path.is_file():
            content[path.relative_to(root).as_posix()] = path.read_bytes()
    return content


def _preflight_parent_chain(base: Path, destination: Path) -> None:
    if base.is_symlink():
        raise ConfigError(f"Skill installation base '{base}' must not be a symlink")
    cursor = base
    try:
        relative = destination.relative_to(base)
    except ValueError as exc:
        raise ConfigError(f"Skill destination '{destination}' escapes base '{base}'") from exc
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ConfigError(f"Skill destination parent '{cursor}' must not be a symlink")
        if cursor.exists() and not cursor.is_dir():
            raise ConfigError(f"Skill destination parent '{cursor}' must be a directory")


def _create_parents(base: Path, destination: Path) -> tuple[Path, ...]:
    created: list[Path] = []
    cursor = base
    for part in destination.relative_to(base).parts:
        cursor = cursor / part
        if not cursor.exists():
            cursor.mkdir()
            created.append(cursor)
    return tuple(created)


def _write_content(root: Path, content: dict[str, bytes]) -> None:
    for relative, payload in content.items():
        target = root.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def _remove_empty_parents(parents: tuple[Path, ...]) -> None:
    for parent in reversed(parents):
        try:
            parent.rmdir()
        except OSError:
            break
