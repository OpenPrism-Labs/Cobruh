"""Tests for project validation, cataloging, composition, and interpolation."""

from __future__ import annotations

from pathlib import Path

import pytest

from cobruh import Cobruh, ConfigError, OverrideError
from cobruh.composition import MAX_SOURCE_BYTES


def test_project_validation_and_catalog(
    project_tree: tuple[Cobruh, Path, Path], tmp_path: Path
) -> None:
    project, project_root, config_root = project_tree
    assert project.config_root == config_root.resolve()
    assert project.project_root == project_root.resolve()
    assert project.catalog() == {
        "configs": ["base", "config"],
        "groups": {"model": ["resnet50", "vgg"], "optimizer": ["adam"]},
    }

    with pytest.raises(ConfigError, match="existing directory"):
        Cobruh(tmp_path / "missing")
    outside = tmp_path.parent / "outside-configs"
    outside.mkdir(exist_ok=True)
    with pytest.raises(ConfigError, match="contained"):
        Cobruh(outside, project_root=tmp_path)


def test_defaults_merge_order_and_provenance(project_tree: tuple[Cobruh, Path, Path]) -> None:
    project, _, config_root = project_tree
    data = project.compose()
    assert data["shared"] == {"base": True, "local": True}
    assert data["items"] == ["local"]
    assert data["model"] == {"name": "resnet", "layers": 50}
    assert data["optimizer"]["lr"] == 0.001
    assert data["copied"] == 50
    assert data["label"] == "model-resnet"
    assert project._compose_result(resolve=False).sources == (
        "base.yaml",
        "config.yaml",
        "model/resnet50.yaml",
        "optimizer/adam.yaml",
    )

    (config_root / "last.yaml").write_text(
        "defaults: [base]\nshared:\n  base: local\n",
        encoding="utf-8",
    )
    assert project.compose("last")["shared"]["base"] == "local"


def test_recursive_defaults_errors_report_include_chain(
    project_tree: tuple[Cobruh, Path, Path],
) -> None:
    project, _, config_root = project_tree
    (config_root / "first.yaml").write_text("defaults: [second]\n", encoding="utf-8")
    (config_root / "second.yaml").write_text("defaults: [first]\n", encoding="utf-8")
    with pytest.raises(ConfigError) as cycle:
        project.compose("first")
    assert "first.yaml" in str(cycle.value)
    assert "second.yaml" in str(cycle.value)

    (config_root / "missing-include.yaml").write_text("defaults: [not-there]\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="include chain"):
        project.compose("missing-include")

    (config_root / "invalid-defaults.yaml").write_text(
        "defaults: [{model: null}]\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="group and option must be strings"):
        project.compose("invalid-defaults")


def test_sequential_group_dotted_and_add_overrides(project_tree: tuple[Cobruh, Path, Path]) -> None:
    project, _, config_root = project_tree
    data = project.compose(overrides=("model=vgg", "model.layers=19", "+run.debug=true"))
    assert data["model"] == {"name": "vgg", "layers": 19}
    assert data["run"] == {"debug": True}

    nested_group = config_root / "services" / "cache"
    nested_group.mkdir(parents=True)
    (nested_group / "redis.yaml").write_text("backend: redis\n", encoding="utf-8")
    selected = project.compose(overrides=("services/cache=redis",))
    assert selected["services"]["cache"] == {"backend": "redis"}

    with pytest.raises(OverrideError, match="Unknown option"):
        project.compose(overrides=("model=unknown",))
    with pytest.raises(OverrideError, match="missing path"):
        project.compose(overrides=("missing=1",))
    with pytest.raises(OverrideError, match="existing path"):
        project.compose(overrides=("+model.name=other",))
    with pytest.raises(OverrideError, match="Invalid override path"):
        project.compose(overrides=("a..b=1",))


def test_interpolation_types_environment_errors_and_cycles(
    project_tree: tuple[Cobruh, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    project, _, config_root = project_tree
    monkeypatch.setenv("COBRUH_TEST_ENV", "present")
    (config_root / "interpolation.yaml").write_text(
        "number: 7\n"
        "mapping: {enabled: true}\n"
        "list: [1, 2]\n"
        "number_copy: ${number}\n"
        "mapping_copy: ${mapping}\n"
        "list_copy: ${list}\n"
        "text: value-${number}\n"
        "environment: ${env:COBRUH_TEST_ENV}\n"
        "fallback: ${env:COBRUH_ABSENT,fallback}\n",
        encoding="utf-8",
    )
    data = project.compose("interpolation")
    assert data["number_copy"] == 7
    assert data["mapping_copy"] == {"enabled": True}
    assert data["list_copy"] == [1, 2]
    assert data["text"] == "value-7"
    assert data["environment"] == "present"
    assert data["fallback"] == "fallback"
    assert project.compose("interpolation", resolve=False)["number_copy"] == "${number}"

    (config_root / "missing-ref.yaml").write_text("value: ${absent}\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Missing interpolation reference"):
        project.compose("missing-ref")
    (config_root / "missing-env.yaml").write_text("value: ${env:COBRUH_ABSENT}\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Missing environment variable"):
        project.compose("missing-env")
    (config_root / "interpolation-cycle.yaml").write_text(
        "first: ${second}\nsecond: ${third}\nthird: ${first}\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="first -> second -> third -> first"):
        project.compose("interpolation-cycle")


def test_source_validation_rejects_unsafe_or_invalid_documents(
    project_tree: tuple[Cobruh, Path, Path], tmp_path: Path
) -> None:
    project, _, config_root = project_tree
    with pytest.raises(ConfigError, match="root-relative"):
        project.compose("../outside")

    (config_root / "empty.yaml").write_text("", encoding="utf-8")
    assert project.compose("empty") == {}
    (config_root / "malformed.yaml").write_text("value: [\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Malformed YAML"):
        project.compose("malformed")
    (config_root / "list-root.yaml").write_text("- value\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="must contain a mapping"):
        project.compose("list-root")
    (config_root / "large.yaml").write_bytes(b"x" * (MAX_SOURCE_BYTES + 1))
    with pytest.raises(ConfigError, match="limit"):
        project.compose("large")

    (config_root / "duplicate.yaml").write_text("value: 1\n", encoding="utf-8")
    (config_root / "duplicate.yml").write_text("value: 2\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="Duplicate YAML variants"):
        project.compose("duplicate")

    real_source = config_root / "real-source.yaml"
    real_source.write_text("value: linked\n", encoding="utf-8")
    safe_link = config_root / "safe-link.yaml"
    try:
        safe_link.symlink_to(real_source)
    except OSError:
        pytest.skip("symlinks unavailable")
    assert project.compose("safe-link") == {"value": "linked"}

    outside = tmp_path / "outside.yaml"
    outside.write_text("value: escaped\n", encoding="utf-8")
    link = config_root / "linked.yaml"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(ConfigError, match="escapes config root"):
        project.compose("linked")
