# Cobruh Project Structure

> **AUTHORITATIVE SOURCE for directory layout, file organization, and module structure**  
> Use this document to determine where files should be created and how modules are organized.  
> Last Updated: October 25, 2025 | Version: 1.0.0

---

## Directory Layout

```
cobruh/
├── src/
│   └── cobruh/
│       ├── __init__.py
│       ├── __version__.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config_store.py          # Global configuration registry
│       │   ├── composer.py              # Configuration composition engine
│       │   ├── decorator.py             # @cobruh.main() decorator
│       │   ├── global_context.py        # Global state management
│       │   └── utils.py                 # Core utilities
│       │
│       ├── config/
│       │   ├── __init__.py
│       │   ├── dictconfig.py            # DictConfig implementation
│       │   ├── listconfig.py            # ListConfig implementation
│       │   ├── base_container.py        # Base container class
│       │   ├── nodes.py                 # Node types (Value, Missing, etc.)
│       │   └── errors.py                # Configuration-specific exceptions
│       │
│       ├── loader/
│       │   ├── __init__.py
│       │   ├── config_loader.py         # Main config loading logic
│       │   ├── yaml_loader.py           # YAML file loader
│       │   ├── structured_loader.py     # Dataclass/structured config loader
│       │   ├── search_path.py           # Config search path management
│       │   └── defaults_list.py         # Defaults list processing
│       │
│       ├── overrides/
│       │   ├── __init__.py
│       │   ├── parser.py                # Override string parser
│       │   ├── applier.py               # Apply overrides to config
│       │   └── types.py                 # Override types and classes
│       │
│       ├── resolver/
│       │   ├── __init__.py
│       │   ├── interpolation.py         # Interpolation resolution
│       │   ├── resolvers.py             # Built-in resolvers (env, oc, etc.)
│       │   ├── custom.py                # Custom resolver registration
│       │   └── graph.py                 # Dependency graph for circular detection
│       │
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── type_validator.py        # Type validation
│       │   ├── schema_validator.py      # Schema-based validation
│       │   └── missing_validator.py     # Missing value detection
│       │
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── instantiate.py           # cobruh.utils.instantiate()
│       │   ├── merge.py                 # Configuration merging
│       │   ├── conversion.py            # Type conversions
│       │   └── path_utils.py            # Path manipulation utilities
│       │
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── base.py                  # Plugin base class
│       │   ├── manager.py               # Plugin manager
│       │   └── builtin/
│       │       ├── __init__.py
│       │       ├── completion.py        # Shell completion plugin
│       │       └── help.py              # Help generation plugin
│       │
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── parser.py                # Command-line argument parser
│       │   ├── multirun.py              # Multi-run support
│       │   └── formatter.py             # Output formatting
│       │
│       └── types/
│           ├── __init__.py
│           ├── structured.py            # Structured config helpers
│           └── protocols.py             # Type protocols/interfaces
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Pytest configuration
│   │
│   ├── unit/
│   │   ├── test_config_store.py
│   │   ├── test_composer.py
│   │   ├── test_dictconfig.py
│   │   ├── test_overrides.py
│   │   ├── test_interpolation.py
│   │   ├── test_instantiate.py
│   │   └── test_merge.py
│   │
│   ├── integration/
│   │   ├── test_basic_composition.py
│   │   ├── test_defaults_list.py
│   │   ├── test_structured_configs.py
│   │   └── test_multirun.py
│   │
│   └── fixtures/
│       └── configs/
│           ├── config.yaml
│           ├── model/
│           │   ├── simple.yaml
│           │   └── complex.yaml
│           └── optimizer/
│               ├── adam.yaml
│               └── sgd.yaml
│
├── examples/
│   ├── 01_basic/
│   │   ├── config.yaml
│   │   └── app.py
│   ├── 02_structured_config/
│   │   ├── config.yaml
│   │   ├── schemas.py
│   │   └── app.py
│   ├── 03_config_groups/
│   │   ├── configs/
│   │   │   ├── config.yaml
│   │   │   ├── model/
│   │   │   └── optimizer/
│   │   └── app.py
│   ├── 04_instantiate/
│   │   ├── config.yaml
│   │   └── app.py
│   └── 05_multirun/
│       ├── config.yaml
│       └── app.py
│
├── docs/
│   ├── getting_started.md
│   ├── tutorials/
│   │   ├── 01_basic_usage.md
│   │   ├── 02_structured_configs.md
│   │   ├── 03_config_groups.md
│   │   ├── 04_overrides.md
│   │   └── 05_instantiate.md
│   ├── advanced/
│   │   ├── interpolation.md
│   │   ├── custom_resolvers.md
│   │   ├── plugins.md
│   │   └── performance.md
│   └── api/
│       ├── core.md
│       ├── config.md
│       └── utils.md
│
├── benchmarks/
│   ├── bench_composition.py
│   ├── bench_interpolation.py
│   └── bench_merge.py
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── release.yml
│       └── docs.yml
│
├── pyproject.toml                       # Modern Python packaging
├── setup.py                             # Backward compatibility
├── requirements.txt                     # Runtime dependencies
├── requirements-dev.txt                 # Development dependencies
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE
└── README.md
```

## Module Breakdown

### Core (`cobruh/core/`)
The heart of the framework, containing the main composition engine and entry points.

**Key Files**:
- `composer.py`: Orchestrates the entire configuration composition process
- `config_store.py`: Singleton registry for storing and retrieving configs
- `decorator.py`: The `@cobruh.main()` decorator implementation
- `global_context.py`: Manages global state (output dir, job name, etc.)

### Config (`cobruh/config/`)
Configuration container implementations with enhanced features.

**Key Files**:
- `dictconfig.py`: Dictionary-like config with dot notation and validation
- `listconfig.py`: List-like config with type safety
- `nodes.py`: Internal node representations (ValueNode, MissingNode, etc.)
- `errors.py`: Custom exceptions for configuration errors

### Loader (`cobruh/loader/`)
Responsible for loading configurations from various sources.

**Key Files**:
- `config_loader.py`: Main loader coordinating all loading operations
- `yaml_loader.py`: YAML file parsing and loading
- `structured_loader.py`: Dataclass/structured config handling
- `defaults_list.py`: Processing of defaults composition

### Overrides (`cobruh/overrides/`)
Handles command-line and programmatic configuration overrides.

**Key Files**:
- `parser.py`: Parse override strings (e.g., "key=value", "+group=option")
- `applier.py`: Apply parsed overrides to configuration
- `types.py`: Override type definitions and classes

### Resolver (`cobruh/resolver/`)
Interpolation and variable resolution system.

**Key Files**:
- `interpolation.py`: Core interpolation resolution logic
- `resolvers.py`: Built-in resolvers (env, oc.env, oc.decode, etc.)
- `custom.py`: API for registering custom resolvers
- `graph.py`: Dependency tracking for circular reference detection

### Validation (`cobruh/validation/`)
Configuration validation and type checking.

**Key Files**:
- `type_validator.py`: Runtime type validation
- `schema_validator.py`: Schema-based validation
- `missing_validator.py`: Detect missing mandatory values

### Utils (`cobruh/utils/`)
Utility functions and helpers.

**Key Files**:
- `instantiate.py`: Object instantiation from config (`_target_` support)
- `merge.py`: Configuration merging strategies
- `conversion.py`: Type conversion utilities
- `path_utils.py`: Dotted path manipulation

### Plugins (`cobruh/plugins/`)
Plugin system for extensibility.

**Key Files**:
- `base.py`: Base plugin interface
- `manager.py`: Plugin discovery and lifecycle management
- `builtin/`: Built-in plugins (completion, help, etc.)

### CLI (`cobruh/cli/`)
Command-line interface components.

**Key Files**:
- `parser.py`: Argument parsing
- `multirun.py`: Multi-run (sweeps) implementation
- `formatter.py`: Output formatting and display

## File Size Estimates

| Component | Approx Lines | Complexity |
|-----------|-------------|------------|
| `composer.py` | 400-600 | High |
| `dictconfig.py` | 500-700 | High |
| `override/parser.py` | 300-400 | Medium |
| `interpolation.py` | 400-500 | High |
| `instantiate.py` | 200-300 | Medium |
| `merge.py` | 300-400 | High |
| `config_loader.py` | 300-500 | Medium |
| `decorator.py` | 200-300 | Medium |

## Dependencies

### Runtime Dependencies
```
pyyaml>=6.0          # YAML parsing
typing-extensions    # Type hints for older Python
```

### Development Dependencies
```
pytest>=7.0          # Testing framework
pytest-cov           # Coverage reporting
black                # Code formatting
mypy                 # Static type checking
ruff                 # Fast linting
pre-commit           # Git hooks
sphinx               # Documentation
```

## Import Structure

### Public API
```python
# Main entry point
from cobruh import main, initialize, compose

# Configuration containers
from cobruh import DictConfig, ListConfig, OmegaConf

# Config store
from cobruh import ConfigStore

# Utilities
from cobruh.utils import instantiate

# Types
from cobruh.types import MISSING, MissingMandatoryValue
```

### Internal Imports
```python
# Core should not import from other modules except types
# Loader can import from config and core
# Resolver can import from config and core
# Utils can import from config and core
# Avoid circular dependencies
```

## Testing Strategy

### Unit Tests
- Each module has corresponding test file
- Test individual functions and classes in isolation
- Mock external dependencies
- Aim for >90% code coverage

### Integration Tests
- Test complete workflows (load → compose → override)
- Test interaction between components
- Use fixture configs for realistic scenarios

### Performance Tests
- Benchmark critical paths (composition, interpolation, merge)
- Regression testing for performance
- Memory profiling for large configs

## Development Workflow

1. **Setup**: `pip install -e .[dev]`
2. **Run Tests**: `pytest tests/`
3. **Type Check**: `mypy src/cobruh`
4. **Lint**: `ruff check src/`
5. **Format**: `black src/ tests/`
6. **Pre-commit**: Automatically runs on git commit

## Documentation Structure

- **Getting Started**: Quick installation and basic usage
- **Tutorials**: Step-by-step guides for common use cases
- **Advanced**: Deep dives into complex features
- **API Reference**: Auto-generated from docstrings
- **Architecture**: Design decisions and internals

## Versioning Strategy

- Semantic Versioning (SEMVER): `MAJOR.MINOR.PATCH`
- Breaking changes increment MAJOR
- New features increment MINOR
- Bug fixes increment PATCH
- Pre-releases: `1.0.0-alpha.1`, `1.0.0-beta.2`, `1.0.0-rc.1`
