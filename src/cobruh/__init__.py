"""Cobruh - A hierarchical configuration management framework for Python applications.

Cobruh is inspired by Facebook's Hydra and provides:
- Hierarchical configuration management
- Composable configuration from reusable pieces
- Type-safe configuration with dataclass support
- Command-line overrides
- Variable interpolation
- Object instantiation from config
"""

from cobruh.__version__ import __version__
from cobruh.core.decorator import main
from cobruh.core.global_context import GlobalContext, initialize
from cobruh.core.composer import compose
from cobruh.core.config_store import ConfigStore
from cobruh.config.dictconfig import DictConfig
from cobruh.config.listconfig import ListConfig

__all__ = [
    "__version__",
    "main",
    "initialize",
    "compose",
    "ConfigStore",
    "DictConfig",
    "ListConfig",
    "GlobalContext",
]
