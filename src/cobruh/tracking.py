"""Optional experiment-tracking integrations."""

from __future__ import annotations

import copy
import importlib
import sys
from collections.abc import Mapping
from types import ModuleType
from typing import Any

from cobruh.errors import IntegrationError

_REMEDIES = {
    "wandb": "Install Cobruh with the W&B extra: pip install 'cobruh[wandb]'",
    "aim": "Install Cobruh with the Aim extra: pip install 'cobruh[aim]'",
}


def init_wandb(config: Mapping[str, Any], /, **kwargs: Any) -> Any:
    """Initialize W&B with a Cobruh config and return its native run object."""
    if "config" in kwargs:
        raise TypeError("init_wandb() received 'config' both positionally and by keyword")
    tracked_config = _copy_config(config)
    wandb = _import_tracker("wandb")
    return wandb.init(config=tracked_config, **kwargs)


def init_aim(
    config: Mapping[str, Any],
    /,
    *,
    config_key: str = "hparams",
    **kwargs: Any,
) -> Any:
    """Initialize Aim, attach a Cobruh config, and return its native run object."""
    if not isinstance(config_key, str) or not config_key:
        raise IntegrationError("Aim config_key must be a nonempty string")
    tracked_config = _copy_config(config)
    aim = _import_tracker("aim")
    run = aim.Run(**kwargs)
    run[config_key] = tracked_config
    return run


def _copy_config(config: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        raise IntegrationError(f"Experiment config must be a mapping, got {type(config).__name__}")
    return copy.deepcopy(dict(config))


def _import_tracker(name: str) -> ModuleType:
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            raise IntegrationError(_missing_remedy(name)) from exc
        raise


def _missing_remedy(name: str) -> str:
    if name == "aim" and sys.version_info >= (3, 13):
        return (
            "Aim 3.29 requires Python 3.12 or earlier; use a supported interpreter "
            "with the 'cobruh[aim]' extra"
        )
    return _REMEDIES[name]
