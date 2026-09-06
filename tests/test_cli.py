"""Tests for the argparse CLI over the project API."""

from __future__ import annotations

import builtins
import json
from pathlib import Path

import pytest

from cobruh.cli import main


def test_catalog_and_compose_output(
    project_tree: tuple[object, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, project_root, config_root = project_tree
    status = main(
        [
            "catalog",
            "--root",
            str(config_root),
            "--project-root",
            str(project_root),
        ]
    )
    assert status == 0
    catalog = json.loads(capsys.readouterr().out)
    assert [option["name"] for option in catalog["groups"]["model"]] == ["resnet50", "vgg"]

    status = main(
        [
            "compose",
            "config",
            "--root",
            str(config_root),
            "--project-root",
            str(project_root),
            "--set",
            "model=vgg",
            "model.layers=19",
            "--format",
            "json",
        ]
    )
    assert status == 0
    data = json.loads(capsys.readouterr().out)
    assert data["model"] == {"name": "vgg", "layers": 19}


def test_compose_no_resolve_yaml(
    project_tree: tuple[object, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, project_root, config_root = project_tree
    status = main(
        [
            "compose",
            "--root",
            str(config_root),
            "--project-root",
            str(project_root),
            "--no-resolve",
        ]
    )
    output = capsys.readouterr()
    assert status == 0
    assert "copied: ${model.layers}" in output.out
    assert output.err == ""


def test_inspect_outputs_focused_validated_metadata(
    project_tree: tuple[object, Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    _, project_root, config_root = project_tree
    schema = project_root / "schema.json"
    schema.write_text(
        json.dumps(
            {
                "type": "object",
                "required": ["model"],
                "properties": {
                    "model": {
                        "type": "object",
                        "required": ["layers"],
                        "properties": {"layers": {"type": "integer"}},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    status = main(
        [
            "inspect",
            "config",
            "--root",
            str(config_root),
            "--project-root",
            str(project_root),
            "--schema",
            "config=schema.json",
            "--set",
            "model=vgg",
            "--node",
            "model",
        ]
    )
    output = capsys.readouterr()
    assert status == 0
    assert output.err == ""
    inspected = json.loads(output.out)
    assert inspected["data"] == {"name": "vgg", "layers": 16}
    assert inspected["choices"][0]["option"] == "vgg"
    assert inspected["provenance"]["/layers"] == {
        "kind": "source",
        "path": "model/vgg.yml",
    }
    assert inspected["types"]["/layers"] == {
        "source": "schema",
        "required": True,
        "schema": {"type": "integer"},
    }
    assert inspected["validation"] == {"status": "valid", "schema": "schema.json"}


def test_instantiate_prints_bounded_result_envelope(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_root = tmp_path / "configs"
    config_root.mkdir()
    (config_root / "config.yaml").write_text(
        "target:\n  _target_: dict\n  value: 3\n",
        encoding="utf-8",
    )
    status = main(
        [
            "instantiate",
            "--root",
            str(config_root),
            "--project-root",
            str(tmp_path),
            "--allow-target",
            "builtins.dict",
            "--node",
            "target",
        ]
    )
    envelope = json.loads(capsys.readouterr().out)
    assert status == 0
    assert envelope == {
        "repr": "{'value': 3}",
        "type": "builtins.dict",
        "value": {"value": 3},
    }


def test_user_errors_use_stderr_and_status_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = main(["catalog", "--root", str(tmp_path / "missing")])
    output = capsys.readouterr()
    assert status == 2
    assert output.out == ""
    assert "existing directory" in output.err


def test_non_loopback_http_rejected_before_server_start(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_root = tmp_path / "configs"
    config_root.mkdir()
    status = main(
        [
            "mcp",
            "--root",
            str(config_root),
            "--project-root",
            str(tmp_path),
            "--transport",
            "streamable-http",
            "--host",
            "0.0.0.0",
        ]
    )
    output = capsys.readouterr()
    assert status == 2
    assert output.out == ""
    assert "not loopback" in output.err


def test_missing_agentic_extra_prints_exact_remedy(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_root = tmp_path / "configs"
    config_root.mkdir()
    original_import = builtins.__import__

    def block_mcp_server(name, *args, **kwargs):
        if name == "cobruh.mcp_server":
            raise ModuleNotFoundError("No module named 'mcp'", name="mcp")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", block_mcp_server)
    status = main(
        [
            "mcp",
            "--root",
            str(config_root),
            "--project-root",
            str(tmp_path),
        ]
    )
    output = capsys.readouterr()
    assert status == 2
    assert output.out == ""
    assert output.err == "Install Cobruh with the agentic extra: pip install 'cobruh[agentic]'\n"
