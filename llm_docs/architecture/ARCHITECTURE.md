# Cobruh Architecture

> **AUTHORITATIVE SOURCE for algorithms, design patterns, and system architecture**  
> All implementation algorithms should follow the specifications in this document.  
> Last Updated: October 25, 2025 | Version: 1.0.0

## Overview

Cobruh is a hierarchical configuration management framework for Python applications, inspired by Facebook's Hydra. It enables composable configuration management with support for configuration groups, overrides, and structured configs.

---

## Core Design Principles

### 1. Composability
- Configurations should be composable from smaller, reusable pieces
- Support for configuration groups (model, optimizer, dataset, etc.)
- Default configuration with selective overrides

### 2. Type Safety
- Integration with Python dataclasses and type hints
- Runtime validation of configuration values
- Schema-based configuration validation

### 3. Hierarchical Organization
- Nested configuration structures
- Configuration inheritance and merging
- Group-based organization (configs/model/, configs/data/, etc.)

### 4. Dynamic Resolution
- Late binding of configuration values
- Support for interpolation and variable substitution
- Environment variable resolution

### 5. Flexibility
- Command-line overrides
- Programmatic configuration
- Multi-run support for parameter sweeps

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (User code decorated with @cobruh.main())                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Cobruh Core API                            │
│  - Decorator (@cobruh.main)                                 │
│  - ConfigStore (registration)                               │
│  - Compose API (programmatic composition)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Configuration Composer                          │
│  - Config loading and merging                               │
│  - Defaults resolution                                      │
│  - Override application                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
│Config Loader │ │ Override │ │ Interpolator│
│              │ │ Parser   │ │             │
│- YAML files  │ │- CLI args│ │- ${var}     │
│- Dataclasses │ │- dot path│ │- ${env:X}   │
│- Dictionaries│ │- notation│ │- ${oc:}     │
└──────────────┘ └──────────┘ └─────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 OmegaConf Container                          │
│  - Structured configuration (DictConfig)                    │
│  - Type validation                                          │
│  - Missing value handling (MISSING, optional)               │
│  - Read-only protection                                     │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Configuration Composer
**Responsibility**: Load, merge, and compose configurations from multiple sources

**Key Operations**:
- Load default configuration from YAML files
- Apply defaults list processing
- Merge structured configs
- Apply command-line overrides
- Resolve interpolations

**Algorithm**:
```python
def compose_config(config_name, overrides):
    # 1. Load primary config
    base_config = load_yaml(config_name)
    
    # 2. Process defaults list
    defaults = base_config.get('defaults', [])
    for default in defaults:
        group_config = load_group_config(default)
        base_config = merge(base_config, group_config)
    
    # 3. Apply overrides
    for override in overrides:
        base_config = apply_override(base_config, override)
    
    # 4. Resolve interpolations
    base_config = resolve_interpolations(base_config)
    
    # 5. Validate against schema (if structured config)
    if has_schema(base_config):
        validate(base_config)
    
    return OmegaConf.create(base_config)
```

### 2. Configuration Loader
**Responsibility**: Load configurations from various sources

**Supported Sources**:
- YAML files (primary)
- Python dataclasses (structured configs)
- Python dictionaries
- Config store (registered configs)

**Search Path**:
```
<config_path>/
├── config.yaml                  # Primary config
├── <group1>/
│   ├── option1.yaml
│   └── option2.yaml
└── <group2>/
    ├── option1.yaml
    └── option2.yaml
```

### 3. Override Parser
**Responsibility**: Parse and apply configuration overrides

**Override Syntax**:
```
key=value                    # Simple override
key.nested=value            # Nested override
+key=value                  # Add new key
~key=value                  # Override or add
group=option                # Select config group
+group=option               # Add config group
~group=option               # Override config group
group/subgroup=option       # Nested group selection
```

**Parser Logic**:
```python
class Override:
    def __init__(self, key: str, value: str, prefix: str = ''):
        self.key = key          # e.g., "model.learning_rate"
        self.value = value      # e.g., "0.001"
        self.prefix = prefix    # '', '+', '~'
        self.is_delete = value == 'null'
        self.is_group = '/' in key or key in known_groups
```

### 4. Interpolation Resolver
**Responsibility**: Resolve variable references and interpolations

**Supported Interpolations**:
- `${key}` - Reference to another config key
- `${env:VAR}` - Environment variable
- `${oc.env:VAR,default}` - Environment variable with default
- `${oc.decode:value}` - Decode resolver
- `${now:%Y-%m-%d}` - Current timestamp
- Custom resolvers (user-defined)

**Resolution Strategy**:
```python
def resolve_interpolation(config, path):
    value = get_value(config, path)
    if is_interpolation(value):
        referenced_path = extract_path(value)
        if is_circular(path, referenced_path):
            raise CircularReferenceError()
        resolved = resolve_interpolation(config, referenced_path)
        return resolved
    return value
```

### 5. Config Store
**Responsibility**: Registry for structured configurations

```python
class ConfigStore:
    _instance = None
    _store = {}
    
    @staticmethod
    def instance():
        if ConfigStore._instance is None:
            ConfigStore._instance = ConfigStore()
        return ConfigStore._instance
    
    def store(self, name: str, node: Any, group: str = None):
        key = f"{group}/{name}" if group else name
        self._store[key] = node
    
    def get(self, name: str, group: str = None):
        key = f"{group}/{name}" if group else name
        return self._store.get(key)
```

### 6. Decorator System
**Responsibility**: Main entry point for applications

```python
def main(
    config_path: Optional[str] = None,
    config_name: Optional[str] = "config",
    version_base: Optional[str] = None
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Parse command-line arguments
            overrides = parse_args(sys.argv[1:])
            
            # Compose configuration
            cfg = compose(
                config_name=config_name,
                config_path=config_path,
                overrides=overrides
            )
            
            # Setup output directory
            setup_output_dir(cfg)
            
            # Call user function
            return func(cfg, *args, **kwargs)
        
        return wrapper
    return decorator
```

## Data Structures

### DictConfig
Wrapper around dictionary with additional features:
- Dot notation access (`cfg.model.name`)
- Type validation
- Missing value handling
- Read-only mode
- Attribute and dict-style access

### ListConfig
Wrapper around list with:
- Index-based access
- Type validation
- Interpolation support

### Node Types
```python
@dataclass
class Node:
    value: Any
    metadata: Dict[str, Any]
    
class ValueNode(Node):
    """Leaf node containing actual value"""
    pass

class InterpolationNode(Node):
    """Node with unresolved interpolation"""
    resolver: str
    path: str
    
class MissingNode(Node):
    """Placeholder for missing mandatory values"""
    pass
```

## Configuration Merging Strategy

### Merge Rules
1. **Dict-to-Dict**: Recursive merge, child keys override parent
2. **List-to-List**: Replace entire list (no element-wise merge)
3. **Value-to-Value**: Override completely
4. **None handling**: None can override non-None values
5. **MISSING**: Can be overridden by any value

### Merge Order
```
1. Package defaults (built-in)
2. Config file defaults list
3. Config file body
4. Structured config schema (if any)
5. Command-line overrides
```

## Error Handling

### Configuration Errors
- `ConfigCompositionError`: Error during config composition
- `ConfigAttributeError`: Invalid attribute access
- `MissingMandatoryValue`: Required value not provided
- `ValidationError`: Type validation failed
- `InterpolationResolutionError`: Cannot resolve interpolation
- `CircularReferenceError`: Circular dependency in interpolations

### Error Recovery
- Fail fast on composition errors
- Provide clear error messages with context
- Show configuration path to error location

## Extension Points

### Custom Resolvers
```python
def register_resolver(name: str, resolver: Callable):
    """Register custom interpolation resolver"""
    OmegaConf.register_new_resolver(name, resolver)

# Example
register_resolver("add", lambda x, y: x + y)
# Usage: ${add:10,20}
```

### Plugins System
```python
class Plugin:
    def setup(self):
        """Called during initialization"""
        pass
    
    def before_compose(self, config):
        """Called before config composition"""
        return config
    
    def after_compose(self, config):
        """Called after config composition"""
        return config
```

## Performance Considerations

1. **Lazy Loading**: Load configs only when needed
2. **Caching**: Cache loaded YAML files
3. **Lazy Interpolation**: Resolve interpolations on access, not upfront
4. **Structural Sharing**: Avoid deep copying when possible

## Security Considerations

1. **YAML Safety**: Use safe YAML loader (no arbitrary code execution)
2. **Path Traversal**: Validate config paths to prevent directory traversal
3. **Environment Variables**: Sanitize environment variable access
4. **Read-only Mode**: Support immutable configs after composition

## Future Enhancements

1. **Schema Generation**: Auto-generate schemas from dataclasses
2. **Config Validation**: JSON Schema validation support
3. **Remote Configs**: Load configs from URLs or cloud storage
4. **Config Diffing**: Show differences between configs
5. **Interactive Mode**: CLI for exploring configurations
6. **Config Visualization**: Generate diagrams of config hierarchy
