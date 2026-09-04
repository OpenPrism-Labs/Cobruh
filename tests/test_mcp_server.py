"""Tests for the optional official MCP SDK adapter."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp import Client

from cobruh import Cobruh
from cobruh.composition import MAX_SOURCE_BYTES
from cobruh.mcp_server import create_server


def _run(coroutine: Any) -> Any:
    return asyncio.run(coroutine)


def test_exact_capabilities_and_generated_schemas(tmp_path: Path) -> None:
    async def scenario() -> None:
        config_root = tmp_path / "configs"
        config_root.mkdir()
        (config_root / "config.yaml").write_text("value: 1\n", encoding="utf-8")
        async with Client(create_server(Cobruh(config_root, project_root=tmp_path))) as client:
            tools = await client.list_tools()
            assert [tool.name for tool in tools.tools] == [
                "list_configs",
                "read_config_source",
                "write_config_source",
                "compose_config",
                "instantiate_config",
            ]
            schemas = {tool.name: tool.input_schema for tool in tools.tools}
            assert schemas["list_configs"] == {
                "properties": {},
                "title": "list_configsArguments",
                "type": "object",
            }
            assert schemas["read_config_source"]["required"] == ["path"]
            assert schemas["write_config_source"]["required"] == ["path", "content"]
            assert set(schemas["compose_config"]["properties"]) == {
                "name",
                "overrides",
                "resolve",
            }
            assert set(schemas["instantiate_config"]["properties"]) == {
                "name",
                "node",
                "overrides",
                "args",
                "kwargs",
            }

            resources = await client.list_resources()
            assert [str(resource.uri) for resource in resources.resources] == [
                "cobruh://catalog",
                "cobruh://skills",
            ]
            prompts = await client.list_prompts()
            assert [prompt.name for prompt in prompts.prompts] == [
                "author_config",
                "debug_config",
            ]

    _run(scenario())


def test_read_hash_write_conflict_and_compose_provenance(tmp_path: Path) -> None:
    async def scenario() -> None:
        config_root = tmp_path / "configs"
        (config_root / "model").mkdir(parents=True)
        (config_root / "config.yaml").write_text(
            "defaults:\n  - model: small\nvalue: 1\n", encoding="utf-8"
        )
        (config_root / "model" / "small.yaml").write_text("width: 4\n", encoding="utf-8")
        async with Client(create_server(Cobruh(config_root, project_root=tmp_path))) as client:
            read_result = await client.call_tool("read_config_source", {"path": "model/small.yaml"})
            source = read_result.structured_content
            assert source["ok"] is True
            assert len(source["sha256"]) == 64

            written = await client.call_tool(
                "write_config_source",
                {
                    "path": "model/small.yaml",
                    "content": "width: 8\n",
                    "expected_sha256": source["sha256"],
                },
            )
            assert written.structured_content["ok"] is True
            stale = await client.call_tool(
                "write_config_source",
                {
                    "path": "model/small.yaml",
                    "content": "width: 9\n",
                    "expected_sha256": source["sha256"],
                },
            )
            assert stale.structured_content["ok"] is False
            assert (config_root / "model" / "small.yaml").read_text() == "width: 8\n"

            composed = await client.call_tool("compose_config", {"name": "config"})
            assert composed.structured_content == {
                "ok": True,
                "data": {"model": {"width": 8}, "value": 1},
                "sources": ["model/small.yaml", "config.yaml"],
            }

    _run(scenario())


def test_source_tools_reject_unsafe_inputs_without_mutation(tmp_path: Path) -> None:
    async def scenario() -> None:
        config_root = tmp_path / "configs"
        config_root.mkdir()
        original = "value: original\n"
        target = config_root / "config.yaml"
        target.write_text(original, encoding="utf-8")
        outside = tmp_path / "outside.yaml"
        outside.write_text("value: outside\n", encoding="utf-8")
        link = config_root / "linked.yaml"
        try:
            link.symlink_to(outside)
        except OSError:
            link = None

        async with Client(create_server(Cobruh(config_root, project_root=tmp_path))) as client:
            cases = [
                {"path": "../outside.yaml", "content": "value: bad\n"},
                {"path": str(outside.resolve()), "content": "value: bad\n"},
                {"path": "not-yaml.txt", "content": "value: bad\n"},
                {"path": "large.yaml", "content": "x" * (MAX_SOURCE_BYTES + 1)},
                {"path": "malformed.yaml", "content": "value: [\n"},
                {"path": "list.yaml", "content": "- item\n"},
            ]
            if link is not None:
                cases.append({"path": "linked.yaml", "content": "value: bad\n"})
            for arguments in cases:
                result = await client.call_tool("write_config_source", arguments)
                assert result.structured_content["ok"] is False
            assert target.read_text(encoding="utf-8") == original
            assert outside.read_text(encoding="utf-8") == "value: outside\n"
            assert not (config_root / "large.yaml").exists()
            assert not (config_root / "malformed.yaml").exists()
            assert not (config_root / "list.yaml").exists()

            read_traversal = await client.call_tool(
                "read_config_source", {"path": "../outside.yaml"}
            )
            assert read_traversal.structured_content["ok"] is False

    _run(scenario())


def test_project_target_execution_and_result_serialization(tmp_path: Path) -> None:
    async def scenario() -> None:
        config_root = tmp_path / "configs"
        config_root.mkdir()
        (tmp_path / "target_module.py").write_text(
            "def build(value):\n    return {'built': value}\n",
            encoding="utf-8",
        )
        (config_root / "config.yaml").write_text(
            "job:\n  _target_: target_module.build\n  value: 7\n",
            encoding="utf-8",
        )
        async with Client(create_server(Cobruh(config_root, project_root=tmp_path))) as client:
            result = await client.call_tool("instantiate_config", {"name": "config", "node": "job"})
            assert result.structured_content == {
                "ok": True,
                "result": {
                    "type": "builtins.dict",
                    "repr": "{'built': 7}",
                    "value": {"built": 7},
                },
            }

    _run(scenario())


def test_core_import_does_not_require_mcp() -> None:
    code = """
import builtins
original = builtins.__import__
def blocked(name, *args, **kwargs):
    if name == 'mcp' or name.startswith('mcp.'):
        raise ImportError('mcp intentionally absent')
    return original(name, *args, **kwargs)
builtins.__import__ = blocked
import cobruh
assert cobruh.Cobruh
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
