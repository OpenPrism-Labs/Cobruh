"""Cobruh command-line interface."""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import yaml

from cobruh import Cobruh, CobruhError
from cobruh._adapter import result_envelope, select_mapping


class _MissingAgenticError(Exception):
    pass


_AGENTIC_REMEDY = "Install Cobruh with the agentic extra: pip install 'cobruh[agentic]'"


def build_parser() -> argparse.ArgumentParser:
    """Build the public CLI grammar."""
    parser = argparse.ArgumentParser(prog="cobruh")
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog_parser = subparsers.add_parser("catalog", help="List available configurations")
    _add_project_arguments(catalog_parser)

    compose_parser = subparsers.add_parser("compose", help="Compose a configuration")
    compose_parser.add_argument("name", nargs="?", default="config")
    _add_project_arguments(compose_parser)
    _add_override_arguments(compose_parser)
    compose_parser.add_argument("--no-resolve", action="store_true")
    compose_parser.add_argument("--format", choices=("yaml", "json"), default="yaml")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect composed data and metadata")
    inspect_parser.add_argument("name", nargs="?", default="config")
    _add_project_arguments(inspect_parser)
    _add_override_arguments(inspect_parser)
    inspect_parser.add_argument("--no-resolve", action="store_true")
    inspect_parser.add_argument("--node", default="")

    instantiate_parser = subparsers.add_parser(
        "instantiate", help="Compose and instantiate a target mapping"
    )
    instantiate_parser.add_argument("name", nargs="?", default="config")
    _add_project_arguments(instantiate_parser)
    _add_override_arguments(instantiate_parser)
    instantiate_parser.add_argument("--node", default="")
    instantiate_parser.add_argument("--allow-target", action="append", default=[])

    mcp_parser = subparsers.add_parser("mcp", help="Run the trusted local MCP server")
    _add_project_arguments(mcp_parser)
    mcp_parser.add_argument("--allow-target", action="append", default=[])
    mcp_parser.add_argument("--transport", choices=("stdio", "streamable-http"), default="stdio")
    mcp_parser.add_argument("--host", default="127.0.0.1")
    mcp_parser.add_argument("--port", type=int, default=8000)

    skills_parser = subparsers.add_parser("skills", help="List or install bundled skills")
    skills_subparsers = skills_parser.add_subparsers(dest="skills_command", required=True)
    skills_subparsers.add_parser("list", help="List bundled skills")
    install_parser = skills_subparsers.add_parser("install", help="Install bundled skills")
    install_parser.add_argument(
        "--agent", required=True, choices=("codex", "claude", "copilot", "cursor", "all")
    )
    install_parser.add_argument("--scope", choices=("project", "user"), default="project")
    install_parser.add_argument("--project", type=Path, default=Path("."))
    install_parser.add_argument("--skill", action="append", default=[])
    install_parser.add_argument("--force", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return its process exit status."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        return _dispatch(arguments)
    except _MissingAgenticError:
        print(_AGENTIC_REMEDY, file=sys.stderr)
        return 2
    except (CobruhError, OSError, TypeError, ValueError) as exc:
        print(f"cobruh: {exc}", file=sys.stderr)
        return 2


def _dispatch(arguments: argparse.Namespace) -> int:
    if arguments.command == "skills":
        from cobruh.skills import install_skills, list_skills

        if arguments.skills_command == "list":
            print(json.dumps({"skills": list_skills()}, indent=2, sort_keys=True))
            return 0
        installed = install_skills(
            agent=arguments.agent,
            scope=arguments.scope,
            project=arguments.project,
            names=arguments.skill,
            force=arguments.force,
        )
        print(json.dumps({"installed": installed}, indent=2, sort_keys=True))
        return 0

    project = _build_project(arguments)
    if arguments.command == "catalog":
        print(json.dumps(project.catalog(), indent=2, sort_keys=True))
        return 0
    if arguments.command == "compose":
        data = project.compose(
            arguments.name,
            overrides=arguments.overrides,
            resolve=not arguments.no_resolve,
        )
        if arguments.format == "json":
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print(yaml.safe_dump(data, sort_keys=False), end="")
        return 0
    if arguments.command == "inspect":
        inspected = project.inspect(
            arguments.name,
            overrides=arguments.overrides,
            resolve=not arguments.no_resolve,
            node=arguments.node,
        )
        print(json.dumps(inspected, indent=2, sort_keys=True))
        return 0
    if arguments.command == "instantiate":
        data = project.compose(arguments.name, overrides=arguments.overrides)
        result = project.instantiate(select_mapping(data, arguments.node))
        print(json.dumps(result_envelope(result), indent=2, sort_keys=True))
        return 0
    if arguments.command == "mcp":
        return _run_mcp(project, arguments)
    raise ValueError(f"Unknown command '{arguments.command}'")


def _build_project(arguments: argparse.Namespace) -> Cobruh:
    schemas: dict[str, Path] = {}
    for expression in arguments.schema:
        name, separator, raw_path = expression.partition("=")
        if not separator or not name or not raw_path:
            raise ValueError(f"Invalid schema registration '{expression}': expected NAME=PATH")
        if name in schemas:
            raise ValueError(f"Duplicate schema registration for '{name}'")
        schemas[name] = Path(raw_path)
    return Cobruh(
        arguments.root,
        project_root=arguments.project_root,
        schemas=schemas,
        allowed_targets=getattr(arguments, "allow_target", ()),
    )


def _run_mcp(project: Cobruh, arguments: argparse.Namespace) -> int:
    if arguments.transport == "streamable-http" and not _is_loopback(arguments.host):
        raise ValueError(
            f"Streamable HTTP host '{arguments.host}' is not loopback; refusing to expose "
            "an unauthenticated code-execution server"
        )
    try:
        from cobruh.mcp_server import create_server
    except ImportError as exc:
        if exc.name == "mcp" or (exc.name and exc.name.startswith("mcp.")):
            raise _MissingAgenticError from exc
        raise
    server = create_server(project)
    if arguments.transport == "stdio":
        server.run()
    else:
        server.run(
            transport="streamable-http",
            host=arguments.host,
            port=arguments.port,
        )
    return 0


def _add_project_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--schema", action="append", default=[], metavar="NAME=PATH")


def _add_override_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])


def _is_loopback(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False
