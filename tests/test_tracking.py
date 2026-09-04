"""Tests for the optional W&B and Aim integrations."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any

import pytest

from cobruh import IntegrationError, init_aim, init_wandb


class FakeAimRun:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.params: dict[str, Any] = {}
        self.tracked: list[tuple[object, str, int]] = []

    def __setitem__(self, key: str, value: Any) -> None:
        self.params[key] = value

    def track(self, value: object, *, name: str, step: int) -> None:
        self.tracked.append((value, name, step))


def test_init_wandb_passes_config_and_returns_native_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleType("wandb")
    native_run = object()
    received: dict[str, Any] = {}

    def init(**kwargs: Any) -> object:
        received.update(kwargs)
        return native_run

    module.init = init  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "wandb", module)
    config = {"model": {"layers": 50}, "batch_size": 32}

    run = init_wandb(config, project="demo", mode="offline")

    assert run is native_run
    assert received == {"config": config, "project": "demo", "mode": "offline"}
    assert received["config"] is not config
    assert received["config"]["model"] is not config["model"]


def test_init_aim_attaches_config_and_returns_native_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleType("aim")
    module.Run = FakeAimRun  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "aim", module)
    config = {"optimizer": {"name": "adam", "lr": 0.001}}

    run = init_aim(config, repo=".aim", experiment="baseline")
    run.track(0.25, name="loss", step=1)

    assert isinstance(run, FakeAimRun)
    assert run.kwargs == {"repo": ".aim", "experiment": "baseline"}
    assert run.params == {"hparams": config}
    assert run.params["hparams"] is not config
    assert run.tracked == [(0.25, "loss", 1)]


def test_init_aim_accepts_custom_config_key(monkeypatch: pytest.MonkeyPatch) -> None:
    module = ModuleType("aim")
    module.Run = FakeAimRun  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "aim", module)

    run = init_aim({"seed": 7}, config_key="config")

    assert run.params == {"config": {"seed": 7}}


@pytest.mark.parametrize(
    ("function", "module_name", "extra"),
    [
        (init_wandb, "wandb", "wandb"),
        (init_aim, "aim", "aim"),
    ],
)
def test_missing_tracker_reports_install_extra(
    function: Any,
    module_name: str,
    extra: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = __import__("importlib").import_module

    def missing(name: str, package: str | None = None) -> ModuleType:
        if name == module_name:
            raise ModuleNotFoundError(f"No module named '{name}'", name=name)
        return real_import(name, package)

    monkeypatch.setattr("cobruh.tracking.importlib.import_module", missing)

    with pytest.raises(IntegrationError, match=rf"cobruh\[{extra}\]"):
        function({"seed": 7})


def test_tracking_rejects_invalid_config_without_importing_tracker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_import(name: str) -> ModuleType:
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.setattr("cobruh.tracking.importlib.import_module", unexpected_import)

    with pytest.raises(IntegrationError, match="must be a mapping"):
        init_wandb(["not", "a", "mapping"])  # type: ignore[arg-type]
    with pytest.raises(IntegrationError, match="must be a mapping"):
        init_aim(["not", "a", "mapping"])  # type: ignore[arg-type]
