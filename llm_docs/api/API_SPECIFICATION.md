# Cobruh API Design Specification

> **AUTHORITATIVE SOURCE for public API, usage patterns, and configuration syntax**  
> All API implementations should match the specifications in this document.  
> Last Updated: October 25, 2025 | Version: 1.0.0

---

## Public API Overview

The Cobruh API is designed to be minimal, intuitive, and type-safe. It follows these principles:

- **Simplicity**: Common use cases should be simple
- **Discoverability**: API should be self-documenting
- **Type Safety**: Full typing support with mypy
- **Compatibility**: Similar API surface to Hydra for easy migration

---

## Core API

### 1. Main Decorator

#### `@cobruh.main()`

Primary entry point for Cobruh applications.

```python
def main(
    config_path: Optional[str] = None,
    config_name: str = "config",
    version_base: Optional[str] = None
) -> Callable[[Callable[[DictConfig], Any]], Callable[[], Any]]:
    """
    Decorator for main application entry point.
    
    Args:
        config_path: Path to config directory (absolute or relative to caller)
                    If None, looks for 'configs' directory next to script
        config_name: Name of the primary config file (without .yaml extension)
        version_base: Cobruh version for compatibility (e.g., "1.0")
    
    Returns:
        Decorator function that wraps the main application function
    
    Example:
        @cobruh.main(config_path="configs", config_name="config")
        def my_app(cfg: DictConfig) -> None:
            print(cfg.model.name)
            model = cobruh.utils.instantiate(cfg.model)
    """
```

**Usage Examples**:

```python
# Basic usage - looks for configs/config.yaml
@cobruh.main()
def app(cfg: DictConfig):
    print(cfg)

# Custom config location
@cobruh.main(config_path="../conf", config_name="app_config")
def app(cfg: DictConfig):
    print(cfg)

# With version specification
@cobruh.main(version_base="1.1", config_name="experiment")
def app(cfg: DictConfig):
    print(cfg)
```

---

### 2. Compose API

#### `cobruh.compose()`

Programmatic configuration composition without decorator.

```python
def compose(
    config_name: Optional[str] = None,
    overrides: List[str] = [],
    return_cobruh_config: bool = False,
) -> DictConfig:
    """
    Compose configuration programmatically.
    
    Args:
        config_name: Name of config to load (or None for empty config)
        overrides: List of override strings (e.g., ["model=resnet", "lr=0.01"])
        return_cobruh_config: Include Cobruh runtime config in result
    
    Returns:
        Composed DictConfig
    
    Example:
        cfg = cobruh.compose(
            config_name="config",
            overrides=["model=resnet", "optimizer.lr=0.001"]
        )
    """
```

**Usage Examples**:

```python
# Basic composition
cfg = cobruh.compose(config_name="config")

# With overrides
cfg = cobruh.compose(
    config_name="experiment",
    overrides=["model=large", "data.batch_size=128"]
)

# Empty config with overrides only
cfg = cobruh.compose(overrides=["key=value"])
```

---

#### `cobruh.initialize()`

Initialize Cobruh context for composition.

```python
def initialize(
    config_path: Optional[str] = None,
    job_name: Optional[str] = None,
    caller_stack_depth: int = 1,
) -> None:
    """
    Initialize Cobruh global context.
    
    Must be called before compose() in programmatic usage.
    Not needed when using @cobruh.main() decorator.
    
    Args:
        config_path: Search path for configs
        job_name: Name for this job (affects output directory)
        caller_stack_depth: Stack depth for determining caller location
    
    Example:
        cobruh.initialize(config_path="configs")
        cfg = cobruh.compose(config_name="config")
    """
```

---

#### `cobruh.initialize_config_dir()`

More explicit initialization with directory specification.

```python
def initialize_config_dir(
    config_dir: str,
    job_name: str = "app",
    version_base: Optional[str] = None
) -> None:
    """
    Initialize with explicit config directory.
    
    Args:
        config_dir: Absolute path to config directory
        job_name: Job name for output organization
        version_base: Cobruh version for compatibility
    
    Example:
        cobruh.initialize_config_dir(
            config_dir="/path/to/configs",
            job_name="experiment_1"
        )
        cfg = cobruh.compose(config_name="config")
    """
```

---

### 3. ConfigStore API

#### `ConfigStore.instance()`

Access the global config store.

```python
class ConfigStore:
    """Global registry for structured configurations."""
    
    @staticmethod
    def instance() -> "ConfigStore":
        """Get singleton instance of ConfigStore."""
        
    def store(
        self,
        name: str,
        node: Any,
        group: Optional[str] = None,
        package: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> None:
        """
        Register a configuration.
        
        Args:
            name: Configuration name
            node: Config object (dict, dataclass, or DictConfig)
            group: Optional group name (e.g., "model", "optimizer")
            package: Package path for config placement
            provider: Provider name for tracking
        
        Example:
            from dataclasses import dataclass
            from cobruh import ConfigStore
            
            @dataclass
            class ModelConfig:
                name: str = "resnet"
                layers: int = 50
            
            cs = ConfigStore.instance()
            cs.store(name="resnet", node=ModelConfig, group="model")
        """
```

**Usage Examples**:

```python
from dataclasses import dataclass
from cobruh import ConfigStore

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "mydb"

# Register in config store
cs = ConfigStore.instance()
cs.store(name="postgres", node=DatabaseConfig, group="database")

# Now can use in config or override:
# database=postgres
```

---

### 4. Container API (DictConfig/ListConfig)

#### `DictConfig`

Dictionary-like configuration container.

```python
class DictConfig:
    """
    Dictionary-based configuration container with enhanced features.
    
    Supports:
    - Dot notation: cfg.model.name
    - Dict access: cfg["model"]["name"]
    - Attribute access: cfg.model
    - Type safety and validation
    - Interpolation resolution
    - Metadata tracking
    """
    
    def __init__(
        self,
        content: Union[Dict, DictConfig],
        parent: Optional["DictConfig"] = None,
        key: Optional[str] = None,
        flags: Optional[Dict[str, bool]] = None
    ):
        """Create DictConfig from dict or another DictConfig."""
    
    def __getattr__(self, key: str) -> Any:
        """Get value using dot notation."""
    
    def __getitem__(self, key: str) -> Any:
        """Get value using dict notation."""
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set value using dict notation."""
    
    def __setattr__(self, key: str, value: Any) -> None:
        """Set value using dot notation."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default."""
    
    def keys(self) -> KeysView:
        """Get config keys."""
    
    def values(self) -> ValuesView:
        """Get config values."""
    
    def items(self) -> ItemsView:
        """Get config items."""
    
    def update(self, other: Union[Dict, "DictConfig"]) -> None:
        """Update config with another dict/DictConfig."""
    
    def merge_with(self, other: Union[Dict, "DictConfig"]) -> "DictConfig":
        """Merge with another config (returns new config)."""
    
    def to_dict(self) -> Dict:
        """Convert to plain Python dict."""
```

#### `ListConfig`

List-like configuration container.

```python
class ListConfig:
    """
    List-based configuration container.
    
    Supports:
    - Index access: cfg[0]
    - Slicing: cfg[1:3]
    - List operations: append, extend, insert
    - Type safety
    - Interpolation in elements
    """
    
    def __init__(
        self,
        content: Union[List, ListConfig],
        parent: Optional[Union[DictConfig, ListConfig]] = None,
        key: Optional[Union[str, int]] = None,
        flags: Optional[Dict[str, bool]] = None
    ):
        """Create ListConfig from list or another ListConfig."""
    
    def __getitem__(self, index: Union[int, slice]) -> Any:
        """Get item by index or slice."""
    
    def __setitem__(self, index: Union[int, slice], value: Any) -> None:
        """Set item by index or slice."""
    
    def append(self, value: Any) -> None:
        """Append item to list."""
    
    def extend(self, values: List[Any]) -> None:
        """Extend list with multiple items."""
    
    def insert(self, index: int, value: Any) -> None:
        """Insert item at index."""
    
    def to_list(self) -> List:
        """Convert to plain Python list."""
```

---

### 5. OmegaConf Utilities

#### `OmegaConf`

Main utility class for config operations.

```python
class OmegaConf:
    """Utility functions for configuration management."""
    
    @staticmethod
    def create(
        obj: Any = None,
        parent: Optional[Container] = None,
        flags: Optional[Dict[str, bool]] = None
    ) -> Union[DictConfig, ListConfig]:
        """
        Create DictConfig or ListConfig from object.
        
        Args:
            obj: Dict, list, dataclass, or other structured object
            parent: Parent container
            flags: Configuration flags (struct, readonly, etc.)
        
        Returns:
            DictConfig or ListConfig
        
        Example:
            cfg = OmegaConf.create({"model": {"name": "resnet"}})
            cfg = OmegaConf.create(MyDataclass)
        """
    
    @staticmethod
    def merge(
        *configs: Union[DictConfig, Dict, ListConfig, List]
    ) -> Union[DictConfig, ListConfig]:
        """
        Merge multiple configs.
        
        Args:
            *configs: Variable number of configs to merge
        
        Returns:
            Merged config
        
        Example:
            base = OmegaConf.create({"a": 1, "b": 2})
            override = OmegaConf.create({"b": 3, "c": 4})
            merged = OmegaConf.merge(base, override)
            # Result: {"a": 1, "b": 3, "c": 4}
        """
    
    @staticmethod
    def to_container(
        cfg: Union[DictConfig, ListConfig],
        resolve: bool = False,
        enum_to_str: bool = False
    ) -> Union[Dict, List]:
        """
        Convert config to plain Python container.
        
        Args:
            cfg: Config to convert
            resolve: Whether to resolve interpolations
            enum_to_str: Convert enums to strings
        
        Returns:
            Plain dict or list
        
        Example:
            cfg = OmegaConf.create({"a": "${b}", "b": 10})
            container = OmegaConf.to_container(cfg, resolve=True)
            # Result: {"a": 10, "b": 10}
        """
    
    @staticmethod
    def to_yaml(cfg: Union[DictConfig, ListConfig]) -> str:
        """
        Convert config to YAML string.
        
        Example:
            yaml_str = OmegaConf.to_yaml(cfg)
            print(yaml_str)
        """
    
    @staticmethod
    def is_missing(cfg: Any, key: str) -> bool:
        """
        Check if key has MISSING value.
        
        Example:
            if OmegaConf.is_missing(cfg, "model.path"):
                raise ValueError("model.path is required")
        """
    
    @staticmethod
    def is_interpolation(cfg: Any, key: str) -> bool:
        """Check if key value is an interpolation."""
    
    @staticmethod
    def select(
        cfg: Union[DictConfig, ListConfig],
        key: str,
        default: Any = None
    ) -> Any:
        """
        Select value using dotted path.
        
        Args:
            cfg: Config to select from
            key: Dotted path (e.g., "model.optimizer.lr")
            default: Default value if path doesn't exist
        
        Returns:
            Selected value or default
        
        Example:
            lr = OmegaConf.select(cfg, "model.optimizer.lr", default=0.001)
        """
    
    @staticmethod
    def update(
        cfg: Union[DictConfig, ListConfig],
        key: str,
        value: Any,
        merge: bool = True
    ) -> None:
        """
        Update value at dotted path.
        
        Example:
            OmegaConf.update(cfg, "model.layers", 100)
        """
    
    @staticmethod
    def set_struct(cfg: DictConfig, value: bool) -> None:
        """
        Enable/disable struct mode.
        
        In struct mode, cannot add new keys not in schema.
        
        Example:
            OmegaConf.set_struct(cfg, True)  # Enable struct mode
            cfg.new_key = 10  # Raises error
        """
    
    @staticmethod
    def set_readonly(cfg: Union[DictConfig, ListConfig], value: bool) -> None:
        """
        Enable/disable readonly mode.
        
        Example:
            OmegaConf.set_readonly(cfg, True)
            cfg.key = "value"  # Raises error
        """
    
    @staticmethod
    def register_new_resolver(
        name: str,
        resolver: Callable,
        replace: bool = False
    ) -> None:
        """
        Register custom interpolation resolver.
        
        Args:
            name: Resolver name (used as ${name:arg1,arg2})
            resolver: Callable that takes arguments and returns value
            replace: Whether to replace existing resolver
        
        Example:
            def add(x: int, y: int) -> int:
                return x + y
            
            OmegaConf.register_new_resolver("add", add)
            
            # In config: result: ${add:10,20}  # Result: 30
        """
```

---

### 6. Instantiate Utility

#### `cobruh.utils.instantiate()`

Instantiate objects from configuration.

```python
def instantiate(
    config: Union[DictConfig, Dict],
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Instantiate object from config with _target_ field.
    
    Args:
        config: Configuration with _target_ field
        *args: Positional arguments to pass to constructor
        **kwargs: Additional keyword arguments
    
    Returns:
        Instantiated object
    
    Special fields:
        _target_: Full import path to class/function (required)
        _partial_: If True, return functools.partial instead of calling
        _recursive_: If False, don't recursively instantiate nested configs
        _convert_: Conversion mode ("none", "partial", "all")
    
    Example:
        # Config:
        # model:
        #   _target_: torch.nn.Linear
        #   in_features: 10
        #   out_features: 5
        
        model = cobruh.utils.instantiate(cfg.model)
        # Equivalent to: torch.nn.Linear(in_features=10, out_features=5)
    
    Example with _partial_:
        # Config:
        # optimizer:
        #   _target_: torch.optim.Adam
        #   _partial_: true
        #   lr: 0.001
        
        optimizer_fn = cobruh.utils.instantiate(cfg.optimizer)
        optimizer = optimizer_fn(model.parameters())
    """
```

**Usage Examples**:

```python
# Simple instantiation
cfg = OmegaConf.create({
    "_target_": "pathlib.Path",
    "path": "/tmp/data"
})
path_obj = instantiate(cfg)

# Nested instantiation
cfg = OmegaConf.create({
    "model": {
        "_target_": "MyModel",
        "optimizer": {
            "_target_": "torch.optim.Adam",
            "lr": 0.001
        }
    }
})
model = instantiate(cfg.model)

# Partial instantiation
cfg = OmegaConf.create({
    "_target_": "torch.optim.SGD",
    "_partial_": True,
    "lr": 0.01,
    "momentum": 0.9
})
optimizer_fn = instantiate(cfg)
optimizer = optimizer_fn(params=model.parameters())

# Override config values
model = instantiate(cfg.model, hidden_dim=256)
```

---

### 7. Additional Utilities

#### `cobruh.utils.get_original_cwd()`

Get the original working directory (before Cobruh changed it).

```python
def get_original_cwd() -> str:
    """
    Get original working directory.
    
    Cobruh changes working directory to output dir.
    This returns the original directory where script was run.
    
    Returns:
        Original working directory path
    
    Example:
        data_path = os.path.join(cobruh.utils.get_original_cwd(), "data")
    """
```

#### `cobruh.utils.to_absolute_path()`

Convert relative path to absolute based on original cwd.

```python
def to_absolute_path(path: str) -> str:
    """
    Convert path to absolute based on original working directory.
    
    Args:
        path: Relative or absolute path
    
    Returns:
        Absolute path
    
    Example:
        abs_path = cobruh.utils.to_absolute_path("data/train.csv")
    """
```

---

## Special Values and Constants

### `MISSING`

Sentinel value for missing mandatory configuration.

```python
from cobruh.types import MISSING

@dataclass
class Config:
    required_field: str = MISSING  # Must be provided
    optional_field: Optional[str] = None  # Can be None

# Usage
cfg = OmegaConf.create(Config)
assert OmegaConf.is_missing(cfg, "required_field")
```

---

## Configuration File Syntax

### YAML Configuration

```yaml
# config.yaml

# Defaults list
defaults:
  - model: resnet50
  - optimizer: adam
  - _self_  # Position of this config in merge order

# Direct values
seed: 42
batch_size: 32

# Nested structure
data:
  root: /path/to/data
  train_split: 0.8
  
# Lists
augmentations:
  - random_crop
  - random_flip
  - normalize

# Interpolations
output_dir: /tmp/outputs
checkpoint_dir: ${output_dir}/checkpoints  # Reference

# Environment variables
data_path: ${env:DATA_ROOT}
cache_dir: ${oc.env:CACHE_DIR,/tmp/cache}  # With default

# Instantiation target
model:
  _target_: models.ResNet
  num_layers: 50
  pretrained: true

# Optional values
optional_setting: ???  # MISSING - must be provided
```

### Config Groups

```yaml
# configs/model/resnet.yaml
_target_: models.ResNet
num_layers: 50
pretrained: true

# configs/model/vgg.yaml
_target_: models.VGG
depth: 16
batch_norm: true

# configs/optimizer/adam.yaml
_target_: torch.optim.Adam
lr: 0.001
betas: [0.9, 0.999]

# configs/optimizer/sgd.yaml
_target_: torch.optim.SGD
lr: 0.01
momentum: 0.9
```

---

## Command-Line Syntax

### Basic Overrides

```bash
# Run with default config
python app.py

# Override values
python app.py batch_size=64 learning_rate=0.001

# Nested overrides
python app.py model.num_layers=101 optimizer.lr=0.01

# Select config group
python app.py model=vgg optimizer=sgd

# Multiple overrides
python app.py model=resnet optimizer=adam model.pretrained=false lr=0.001
```

### Advanced Overrides

```bash
# Force add (add even if not in schema)
python app.py +new_key=value

# Override or add
python app.py ~key=value

# Delete key
python app.py ~model.dropout=null

# List values
python app.py augmentations=[crop,flip,rotate]

# Dict values
python app.py 'model={num_layers:50,pretrained:true}'

# Add config group
python app.py +callbacks=early_stopping
```

### Multirun Syntax

```bash
# Run with multiple values (grid search)
python app.py -m learning_rate=0.1,0.01,0.001

# Multiple parameters
python app.py -m optimizer=adam,sgd learning_rate=0.1,0.01

# Range syntax
python app.py -m batch_size=range(16,128,16)

# Glob patterns
python app.py -m model=glob(*)
```

---

## Type Annotations

Full type annotation support for type checkers (mypy, pyright).

```python
from typing import Any, Optional
from cobruh import DictConfig, ListConfig
from cobruh.types import MISSING

@cobruh.main(config_path="configs", config_name="config")
def my_app(cfg: DictConfig) -> None:
    # Type checker knows cfg is DictConfig
    model_name: str = cfg.model.name
    layers: int = cfg.model.layers
    
    # Optional access with type hints
    lr: Optional[float] = cfg.get("learning_rate")
    
    # Instantiate with type hints
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from torch.nn import Module
    
    model: "Module" = cobruh.utils.instantiate(cfg.model)
```

---

## Error Messages

Cobruh provides clear, actionable error messages:

```python
# Missing mandatory value
ConfigAttributeError: Missing mandatory value: model.path
    Set model.path in your config or override with model.path=<value>

# Invalid override
ConfigCompositionError: Could not override 'model.invalid_key'
    Key 'invalid_key' not found in model config
    Available keys: name, layers, pretrained

# Circular interpolation
InterpolationResolutionError: Circular reference detected
    a -> b -> c -> a
    In config at path: data.output_dir

# Type validation
ValidationError: Type mismatch for 'batch_size'
    Expected: int
    Got: str ("64")
    
# Instantiation error
InstantiationError: Cannot instantiate target 'torch.nn.Linear'
    Missing required argument: 'in_features'
```

---

## Migration from Hydra

Cobruh maintains API compatibility with Hydra for easy migration:

```python
# Hydra code
from hydra import main, compose, initialize
from omegaconf import DictConfig, OmegaConf

# Cobruh equivalent - just change import
from cobruh import main, compose, initialize
from cobruh import DictConfig, OmegaConf

# Same code works with both!
@main(config_path="configs", config_name="config")
def app(cfg: DictConfig):
    model = instantiate(cfg.model)
```

Most Hydra configs and code work as-is with Cobruh.
