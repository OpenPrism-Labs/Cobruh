"""Tests for project-bound Draft 2020-12 JSON Schema validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobruh import Cobruh, ConfigError
from cobruh.validation import MAX_SCHEMA_BYTES


def test_memory_and_path_schemas_validate_resolved_compositions(tmp_path: Path) -> None:
    config_root = tmp_path / "configs"
    config_root.mkdir()
    (config_root / "config.yaml").write_text(
        "width: 4\ncopy: ${width}\n",
        encoding="utf-8",
    )
    memory_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["width", "copy"],
        "properties": {
            "width": {"type": "integer"},
            "copy": {"type": "integer"},
        },
    }
    project = Cobruh(config_root, project_root=tmp_path, schemas={"config": memory_schema})
    memory_schema["properties"]["width"]["type"] = "string"
    assert project.compose() == {"width": 4, "copy": 4}
    assert project.compose(resolve=False)["copy"] == "${width}"

    schema_path = tmp_path / "schemas" / "config.json"
    schema_path.parent.mkdir()
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {"width": {"type": "integer"}},
            }
        ),
        encoding="utf-8",
    )
    path_project = Cobruh(
        config_root,
        project_root=tmp_path,
        schemas={"config.yaml": "schemas/config.json"},
    )
    assert path_project.compose()["width"] == 4


def test_schema_sources_are_project_bound_local_and_well_formed(tmp_path: Path) -> None:
    config_root = tmp_path / "configs"
    config_root.mkdir()
    (config_root / "config.yaml").write_text("value: 1\n", encoding="utf-8")

    outside = tmp_path.parent / "outside-schema.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(ConfigError, match="contained|escapes"):
        Cobruh(config_root, project_root=tmp_path, schemas={"config": outside})

    text_schema = tmp_path / "schema.yaml"
    text_schema.write_text("{}", encoding="utf-8")
    with pytest.raises(ConfigError, match=r"must use \.json"):
        Cobruh(config_root, project_root=tmp_path, schemas={"config": text_schema})

    large = tmp_path / "large.json"
    large.write_bytes(b" " * (MAX_SCHEMA_BYTES + 1))
    with pytest.raises(ConfigError, match="limit"):
        Cobruh(config_root, project_root=tmp_path, schemas={"config": large})

    list_schema = tmp_path / "list.json"
    list_schema.write_text("[]", encoding="utf-8")
    with pytest.raises(ConfigError, match="must contain a mapping"):
        Cobruh(config_root, project_root=tmp_path, schemas={"config": list_schema})

    with pytest.raises(ConfigError, match="local '#.*fragment"):
        Cobruh(
            config_root,
            project_root=tmp_path,
            schemas={"config": {"$ref": "https://example.com/schema.json"}},
        )
    with pytest.raises(ConfigError, match="Invalid schema"):
        Cobruh(config_root, project_root=tmp_path, schemas={"config": {"type": "wat"}})


def test_validation_errors_are_deterministic_bounded_json_pointers(tmp_path: Path) -> None:
    config_root = tmp_path / "configs"
    config_root.mkdir()
    values = {f"v{index}": "wrong" for index in range(22)}
    (config_root / "config.yaml").write_text(
        "\n".join(f"{key}: {value}" for key, value in values.items()) + "\n",
        encoding="utf-8",
    )
    schema = {
        "type": "object",
        "properties": {key: {"type": "integer"} for key in values},
    }
    project = Cobruh(config_root, project_root=tmp_path, schemas={"config": schema})

    with pytest.raises(ConfigError) as failure:
        project.compose()
    message = str(failure.value)
    assert "schema '<memory>'" in message
    assert "instance '/v0' schema '/properties/v0/type'" in message
    assert "instance '/v10' schema '/properties/v10/type'" in message
    assert "2 additional validation error(s) omitted" in message


def test_focused_inspection_rebases_provenance_and_schema_types(tmp_path: Path) -> None:
    config_root = tmp_path / "configs"
    (config_root / "model").mkdir(parents=True)
    (config_root / "config.yaml").write_text(
        "defaults:\n  - model: small\nbatch: 8\ncopied: ${batch}\n",
        encoding="utf-8",
    )
    (config_root / "model" / "small.yaml").write_text("width: 4\n", encoding="utf-8")
    schema = {
        "type": "object",
        "required": ["model", "batch", "copied"],
        "properties": {
            "model": {
                "type": "object",
                "required": ["width"],
                "properties": {"width": {"$ref": "#/$defs/positive"}},
            },
            "batch": {"type": "integer"},
            "copied": {"type": "integer"},
        },
        "$defs": {
            "positive": {"type": "integer", "minimum": 1},
        },
    }
    project = Cobruh(config_root, project_root=tmp_path, schemas={"config": schema})

    inspected = project.inspect(node="model")
    assert list(inspected) == [
        "name",
        "node",
        "data",
        "sources",
        "choices",
        "provenance",
        "types",
        "validation",
    ]
    assert inspected["name"] == "config"
    assert inspected["node"] == "model"
    assert inspected["data"] == {"width": 4}
    assert inspected["sources"] == ["model/small.yaml", "config.yaml"]
    assert inspected["choices"][0]["option"] == "small"
    assert inspected["provenance"] == {"/width": {"kind": "source", "path": "model/small.yaml"}}
    assert inspected["types"] == {
        "": {
            "source": "schema",
            "required": True,
            "schema": {"type": "object", "required": ["width"]},
        },
        "/width": {
            "source": "schema",
            "required": True,
            "schema": {
                "type": "integer",
                "minimum": 1,
                "$ref": "#/$defs/positive",
            },
        },
    }
    assert inspected["validation"] == {"status": "valid", "schema": "<memory>"}

    skipped = project.inspect(resolve=False, node="copied")
    assert skipped["data"] == "${batch}"
    assert skipped["provenance"] == {"": {"kind": "source", "path": "config.yaml"}}
    assert skipped["validation"] == {
        "status": "skipped",
        "schema": "<memory>",
        "reason": "resolve=false",
    }


def test_focused_inspection_infers_json_types_without_schema(tmp_path: Path) -> None:
    config_root = tmp_path / "configs"
    config_root.mkdir()
    (config_root / "config.yaml").write_text(
        "value: 3\nflags: [true, null]\n",
        encoding="utf-8",
    )
    inspected = Cobruh(config_root, project_root=tmp_path).inspect(node="flags")
    assert inspected["types"] == {
        "": {"source": "inferred", "type": "array"},
        "/0": {"source": "inferred", "type": "boolean"},
        "/1": {"source": "inferred", "type": "null"},
    }
    assert inspected["validation"] == {"status": "not_configured"}
