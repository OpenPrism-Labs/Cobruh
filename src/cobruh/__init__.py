"""Cobruh's explicit project-based configuration API."""

from importlib.metadata import version

from cobruh.errors import CobruhError, ConfigError, OverrideError, TargetError
from cobruh.project import Cobruh

__version__ = version("cobruh")

__all__ = [
    "Cobruh",
    "CobruhError",
    "ConfigError",
    "OverrideError",
    "TargetError",
    "__version__",
]
