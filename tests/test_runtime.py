"""Tests for recursive target instantiation."""

from __future__ import annotations

import functools
import sys
from collections import Counter
from pathlib import Path

import pytest

from cobruh import Cobruh, TargetError


def test_builtin_recursive_instantiation_and_overrides(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    configs.mkdir()
    project = Cobruh(configs, project_root=tmp_path)
    config = {
        "_target_": "dict",
        "child": {
            "_target_": "collections.Counter",
            "_args_": [[1, 2, 2]],
        },
        "items": [{"_target_": "list", "_args_": [[3, 4]]}],
        "configured": True,
    }
    result = project.instantiate(config, configured=False)
    assert result["child"] == Counter({2: 2, 1: 1})
    assert result["items"] == [[3, 4]]
    assert result["configured"] is False


def test_explicit_args_replace_configured_args_and_partial(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    configs.mkdir()
    project = Cobruh(configs)
    assert project.instantiate({"_target_": "list", "_args_": [[1]]}) == [1]
    assert project.instantiate(
        {"_target_": "list", "_args_": [[1]]},
        [2, 3],
    ) == [2, 3]

    factory = project.instantiate({"_target_": "dict", "value": 1, "_partial_": True})
    assert isinstance(factory, functools.partial)
    assert factory(extra=2) == {"value": 1, "extra": 2}


def test_recursive_false_preserves_nested_target_mapping(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    configs.mkdir()
    project = Cobruh(configs)
    result = project.instantiate(
        {
            "_target_": "dict",
            "_recursive_": False,
            "child": {"_target_": "list", "_args_": [[1, 2]]},
        }
    )
    assert result["child"] == {"_target_": "list", "_args_": [[1, 2]]}


def test_project_local_import_and_sys_path_restoration(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    configs.mkdir()
    (tmp_path / "local_target.py").write_text(
        "class Box:\n    def __init__(self, value):\n        self.value = value\n",
        encoding="utf-8",
    )
    project = Cobruh(configs, project_root=tmp_path)
    original = sys.path[:]
    box = project.instantiate({"_target_": "local_target.Box", "value": 9})
    assert box.value == 9
    assert sys.path == original


def test_target_errors_include_target_path_and_cause(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    configs.mkdir()
    project = Cobruh(configs)

    with pytest.raises(TargetError, match="requires a nonempty"):
        project.instantiate({"value": 1})
    with pytest.raises(TargetError, match="_args_.*sequence"):
        project.instantiate({"_target_": "dict", "_args_": "wrong"})
    with pytest.raises(TargetError, match="_partial_.*boolean"):
        project.instantiate({"_target_": "dict", "_partial_": 1})
    with pytest.raises(TargetError, match="unsupported reserved field"):
        project.instantiate({"_target_": "dict", "_unknown_": True})

    with pytest.raises(TargetError) as nested:
        project.instantiate({"_target_": "dict", "child": {"_target_": "missing.module.Target"}})
    assert "missing.module.Target" in str(nested.value)
    assert "<root>.child" in str(nested.value)
    assert nested.value.__cause__ is not None

    with pytest.raises(TargetError) as constructor:
        project.instantiate({"_target_": "list", "unknown": True})
    assert "list" in str(constructor.value)
    assert "<root>" in str(constructor.value)
    assert isinstance(constructor.value.__cause__, TypeError)
