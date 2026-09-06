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
    project = Cobruh(
        configs,
        project_root=tmp_path,
        allowed_targets=("builtins.*", "collections.Counter"),
    )
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
    project = Cobruh(configs, allowed_targets=("builtins.*",))
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
    project = Cobruh(configs, allowed_targets=("builtins.dict",))
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
    project = Cobruh(
        configs,
        project_root=tmp_path,
        allowed_targets=("local_target.Box",),
    )
    original = sys.path[:]
    box = project.instantiate({"_target_": "local_target.Box", "value": 9})
    assert box.value == 9
    assert sys.path == original


def test_target_errors_include_target_path_and_cause(tmp_path: Path) -> None:
    configs = tmp_path / "configs"
    configs.mkdir()
    project = Cobruh(
        configs,
        allowed_targets=("builtins.*", "missing.module.Target"),
    )

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


def test_target_allowlist_denies_before_import_and_checks_canonical_identity(
    tmp_path: Path,
) -> None:
    configs = tmp_path / "configs"
    configs.mkdir()
    imported = tmp_path / "imported"
    invoked = tmp_path / "invoked"
    (tmp_path / "policy_side_effect_target.py").write_text(
        "from pathlib import Path\n"
        "Path(__file__).with_name('imported').write_text('yes')\n"
        "def build(value):\n"
        "    return {'built': value}\n",
        encoding="utf-8",
    )
    (tmp_path / "policy_real_target.py").write_text(
        "from pathlib import Path\n"
        "def build(value):\n"
        "    Path(__file__).with_name('invoked').write_text('yes')\n"
        "    return {'built': value}\n",
        encoding="utf-8",
    )
    (tmp_path / "policy_alias_target.py").write_text(
        "from policy_real_target import build\n",
        encoding="utf-8",
    )
    for module in (
        "policy_side_effect_target",
        "policy_real_target",
        "policy_alias_target",
    ):
        sys.modules.pop(module, None)

    denied = Cobruh(configs, project_root=tmp_path)
    with pytest.raises(TargetError, match="configured 'policy_side_effect_target.build'"):
        denied.instantiate({"_target_": "policy_side_effect_target.build", "value": 7})
    assert not imported.exists()

    allowed = Cobruh(
        configs,
        project_root=tmp_path,
        allowed_targets=("policy_side_effect_target.build",),
    )
    assert allowed.allowed_targets == ("policy_side_effect_target.build",)
    assert allowed.instantiate({"_target_": "policy_side_effect_target.build", "value": 7}) == {
        "built": 7
    }
    assert imported.exists()

    alias_only = Cobruh(
        configs,
        project_root=tmp_path,
        allowed_targets=("policy_alias_target.build",),
    )
    with pytest.raises(TargetError) as canonical:
        alias_only.instantiate({"_target_": "policy_alias_target.build", "value": 1})
    assert "configured 'policy_alias_target.build'" in str(canonical.value)
    assert "canonical 'policy_real_target.build'" in str(canonical.value)
    assert not invoked.exists()

    with pytest.raises(TargetError, match="Bare"):
        Cobruh(configs, allowed_targets=("*",))
    with pytest.raises(TargetError, match="empty"):
        Cobruh(configs, allowed_targets=("",))
