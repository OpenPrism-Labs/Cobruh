"""Cobruh's explicit project-based configuration API."""

from importlib.metadata import version

from cobruh.errors import CobruhError, ConfigError, IntegrationError, OverrideError, TargetError
from cobruh.project import Cobruh
from cobruh.tracking import init_aim, init_wandb

__version__ = version("cobruh")

__all__ = [
    "Cobruh",
    "CobruhError",
    "ConfigError",
    "IntegrationError",
    "OverrideError",
    "TargetError",
    "init_aim",
    "init_wandb",
    "__version__",
]
