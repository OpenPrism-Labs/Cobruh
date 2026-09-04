"""Shared Cobruh test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from cobruh import Cobruh


@pytest.fixture
def project_tree(tmp_path: Path) -> tuple[Cobruh, Path, Path]:
    config_root = tmp_path / "configs"
    (config_root / "model").mkdir(parents=True)
    (config_root / "optimizer").mkdir()
    (config_root / "base.yaml").write_text(
        "shared:\n  base: true\nitems: [base]\n",
        encoding="utf-8",
    )
    (config_root / "model" / "resnet50.yaml").write_text(
        "name: resnet\nlayers: 50\n",
        encoding="utf-8",
    )
    (config_root / "model" / "vgg.yml").write_text(
        "name: vgg\nlayers: 16\n",
        encoding="utf-8",
    )
    (config_root / "optimizer" / "adam.yaml").write_text(
        "name: adam\nlr: 0.001\n",
        encoding="utf-8",
    )
    (config_root / "config.yaml").write_text(
        "defaults:\n"
        "  - base\n"
        "  - _self_\n"
        "  - model: resnet50\n"
        "  - optimizer: adam\n"
        "shared:\n"
        "  local: true\n"
        "items: [local]\n"
        "copied: ${model.layers}\n"
        "label: model-${model.name}\n",
        encoding="utf-8",
    )
    return Cobruh(config_root, project_root=tmp_path), tmp_path, config_root
