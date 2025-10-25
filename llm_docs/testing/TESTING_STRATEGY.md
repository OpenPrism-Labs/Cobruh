# Cobruh Testing Strategy

> **AUTHORITATIVE SOURCE for testing approach, test patterns, and coverage requirements**  
> Follow this strategy to achieve >90% code coverage with comprehensive tests.  
> Last Updated: October 25, 2025 | Version: 1.0.0

---

## Overview

Comprehensive testing strategy to ensure Cobruh is reliable, maintainable, and performant. Target: >90% code coverage with focus on critical paths and edge cases.

---

## Testing Pyramid

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E ╲              ~5% of tests
                 ╱        ╲             Full workflows
                ╱──────────╲
               ╱            ╲
              ╱ Integration  ╲         ~25% of tests
             ╱                ╲        Component interactions
            ╱──────────────────╲
           ╱                    ╲
          ╱   Unit Tests         ╲     ~70% of tests
         ╱                        ╲    Individual functions/classes
        ╱──────────────────────────╲
```

---

## Unit Tests

### Test Organization

```
tests/unit/
├── test_dictconfig.py          # DictConfig functionality
├── test_listconfig.py          # ListConfig functionality
├── test_nodes.py               # Node types
├── test_config_store.py        # ConfigStore operations
├── test_composer.py            # Composition logic
├── test_yaml_loader.py         # YAML loading
├── test_structured_loader.py   # Dataclass loading
├── test_override_parser.py     # Override parsing
├── test_override_applier.py    # Override application
├── test_interpolation.py       # Interpolation resolution
├── test_resolvers.py           # Built-in resolvers
├── test_merge.py               # Merging strategies
├── test_instantiate.py         # Object instantiation
├── test_type_validation.py     # Type checking
├── test_path_utils.py          # Path utilities
└── test_errors.py              # Error handling
```

### Test Templates

#### Basic Unit Test Structure

```python
import pytest
from cobruh.config import DictConfig
from cobruh.config.errors import ConfigAttributeError

class TestDictConfig:
    """Tests for DictConfig class."""
    
    def test_create_empty(self):
        """Test creating empty DictConfig."""
        cfg = DictConfig({})
        assert len(cfg) == 0
    
    def test_create_from_dict(self):
        """Test creating DictConfig from dict."""
        data = {"key": "value", "nested": {"a": 1}}
        cfg = DictConfig(data)
        assert cfg.key == "value"
        assert cfg.nested.a == 1
    
    def test_attribute_access(self):
        """Test dot notation access."""
        cfg = DictConfig({"model": {"name": "resnet"}})
        assert cfg.model.name == "resnet"
    
    def test_dict_access(self):
        """Test dict-style access."""
        cfg = DictConfig({"model": {"name": "resnet"}})
        assert cfg["model"]["name"] == "resnet"
    
    def test_missing_key_error(self):
        """Test error on missing key."""
        cfg = DictConfig({"key": "value"})
        with pytest.raises(ConfigAttributeError):
            _ = cfg.missing_key
    
    def test_nested_update(self):
        """Test updating nested values."""
        cfg = DictConfig({"a": {"b": 1}})
        cfg.a.b = 2
        assert cfg.a.b == 2
    
    @pytest.mark.parametrize("value,expected_type", [
        (42, int),
        ("string", str),
        (3.14, float),
        (True, bool),
        ([1, 2, 3], list),
        ({"k": "v"}, dict),
    ])
    def test_type_preservation(self, value, expected_type):
        """Test that types are preserved."""
        cfg = DictConfig({"value": value})
        assert isinstance(cfg.value, expected_type)
```

#### Parametrized Tests

```python
@pytest.mark.parametrize("input_str,expected", [
    ("key=value", ("key", "value", "")),
    ("key.nested=value", ("key.nested", "value", "")),
    ("+key=value", ("key", "value", "+")),
    ("~key=value", ("key", "value", "~")),
    ("key=123", ("key", 123, "")),
    ("key=true", ("key", True, "")),
    ("key=3.14", ("key", 3.14, "")),
])
def test_parse_override(input_str, expected):
    """Test override parsing with various inputs."""
    from cobruh.overrides.parser import parse_override
    result = parse_override(input_str)
    assert result == expected
```

#### Fixture-Based Tests

```python
@pytest.fixture
def sample_config():
    """Provide sample config for tests."""
    return DictConfig({
        "model": {
            "name": "resnet",
            "layers": 50
        },
        "optimizer": {
            "type": "adam",
            "lr": 0.001
        }
    })

def test_with_fixture(sample_config):
    """Test using fixture."""
    assert sample_config.model.name == "resnet"
    sample_config.optimizer.lr = 0.01
    assert sample_config.optimizer.lr == 0.01
```

---

## Integration Tests

### Test Organization

```
tests/integration/
├── test_basic_composition.py       # Basic config loading and composition
├── test_defaults_list.py           # Defaults list processing
├── test_config_groups.py           # Config group selection
├── test_overrides.py               # Command-line overrides
├── test_interpolation_e2e.py       # End-to-end interpolation
├── test_structured_configs.py      # Dataclass configs
├── test_instantiate_e2e.py         # Object instantiation
├── test_multirun.py                # Multi-run functionality
└── test_yaml_files.py              # Real YAML file loading
```

### Integration Test Examples

#### Config Composition Test

```python
import pytest
from pathlib import Path
from cobruh import compose, initialize_config_dir

class TestBasicComposition:
    """Integration tests for config composition."""
    
    @pytest.fixture
    def config_dir(self, tmp_path):
        """Create temporary config directory."""
        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        
        # Main config
        (config_dir / "config.yaml").write_text("""
defaults:
  - model: simple
  - _self_

batch_size: 32
epochs: 10
        """)
        
        # Model configs
        model_dir = config_dir / "model"
        model_dir.mkdir()
        
        (model_dir / "simple.yaml").write_text("""
name: simple_model
layers: 3
        """)
        
        (model_dir / "complex.yaml").write_text("""
name: complex_model
layers: 10
dropout: 0.5
        """)
        
        return config_dir
    
    def test_basic_compose(self, config_dir):
        """Test basic config composition."""
        initialize_config_dir(str(config_dir))
        cfg = compose(config_name="config")
        
        assert cfg.batch_size == 32
        assert cfg.epochs == 10
        assert cfg.model.name == "simple_model"
        assert cfg.model.layers == 3
    
    def test_compose_with_override(self, config_dir):
        """Test composition with overrides."""
        initialize_config_dir(str(config_dir))
        cfg = compose(
            config_name="config",
            overrides=["model=complex", "batch_size=64"]
        )
        
        assert cfg.batch_size == 64
        assert cfg.model.name == "complex_model"
        assert cfg.model.layers == 10
```

#### Defaults List Test

```python
def test_defaults_list_order(config_dir):
    """Test that defaults are merged in correct order."""
    # Create configs with overlapping keys
    (config_dir / "config.yaml").write_text("""
defaults:
  - base
  - override
  - _self_

final_value: from_main
    """)
    
    (config_dir / "base.yaml").write_text("""
value1: from_base
value2: from_base
final_value: from_base
    """)
    
    (config_dir / "override.yaml").write_text("""
value2: from_override
final_value: from_override
    """)
    
    initialize_config_dir(str(config_dir))
    cfg = compose(config_name="config")
    
    assert cfg.value1 == "from_base"
    assert cfg.value2 == "from_override"
    assert cfg.final_value == "from_main"  # _self_ is last
```

---

## End-to-End Tests

### Test Organization

```
tests/e2e/
├── test_complete_workflows.py      # Full application workflows
├── test_multirun_sweep.py          # Complete sweep scenarios
├── test_real_world_configs.py      # Real-world config examples
└── test_cli_interaction.py         # CLI usage scenarios
```

### E2E Test Examples

```python
import subprocess
from pathlib import Path

def test_complete_application_flow(tmp_path):
    """Test complete application from start to finish."""
    
    # Create application
    app_file = tmp_path / "app.py"
    app_file.write_text("""
import cobruh
from cobruh import DictConfig

@cobruh.main(config_path="configs", config_name="config")
def my_app(cfg: DictConfig):
    print(f"Model: {cfg.model.name}")
    print(f"Batch size: {cfg.batch_size}")
    return 0

if __name__ == "__main__":
    my_app()
    """)
    
    # Create configs
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text("""
defaults:
  - model: resnet

batch_size: 32
    """)
    
    model_dir = config_dir / "model"
    model_dir.mkdir()
    (model_dir / "resnet.yaml").write_text("name: ResNet50")
    
    # Run application
    result = subprocess.run(
        ["python", str(app_file)],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "Model: ResNet50" in result.stdout
    assert "Batch size: 32" in result.stdout
```

---

## Performance Tests

### Benchmark Suite

```
benchmarks/
├── bench_composition.py        # Config composition speed
├── bench_interpolation.py      # Interpolation resolution speed
├── bench_merge.py              # Merging performance
├── bench_instantiate.py        # Object instantiation speed
└── bench_large_configs.py      # Scalability with large configs
```

### Performance Test Examples

```python
import pytest
from cobruh import OmegaConf

class TestPerformance:
    """Performance benchmarks."""
    
    def test_large_config_composition(self, benchmark):
        """Benchmark composition of large config."""
        # Create large config
        large_config = {
            f"key_{i}": {
                f"nested_{j}": f"value_{i}_{j}"
                for j in range(100)
            }
            for i in range(100)
        }
        
        def compose_large():
            return OmegaConf.create(large_config)
        
        result = benchmark(compose_large)
        assert len(result) == 100
    
    def test_deep_merge_performance(self, benchmark):
        """Benchmark deep config merging."""
        cfg1 = OmegaConf.create({
            f"level_{i}": {
                "value": i
            }
            for i in range(1000)
        })
        
        cfg2 = OmegaConf.create({
            f"level_{i}": {
                "value": i * 2
            }
            for i in range(500, 1500)
        })
        
        def merge_configs():
            return OmegaConf.merge(cfg1, cfg2)
        
        result = benchmark(merge_configs)
        assert len(result) == 1500
    
    @pytest.mark.parametrize("depth", [10, 50, 100])
    def test_interpolation_depth(self, benchmark, depth):
        """Test interpolation with varying depth."""
        # Create chain of interpolations
        config = {"start": "value"}
        for i in range(depth):
            config[f"ref_{i}"] = f"${{ref_{i-1}}}" if i > 0 else "${start}"
        
        cfg = OmegaConf.create(config)
        
        def resolve():
            return OmegaConf.to_container(cfg, resolve=True)
        
        benchmark(resolve)
```

---

## Property-Based Tests

Use Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st
from cobruh import DictConfig, OmegaConf

@given(st.dictionaries(
    keys=st.text(min_size=1, alphabet=st.characters(whitelist_categories=("Ll", "Lu"))),
    values=st.one_of(st.integers(), st.floats(allow_nan=False), st.text())
))
def test_roundtrip_conversion(data):
    """Test that dict -> DictConfig -> dict preserves data."""
    cfg = OmegaConf.create(data)
    result = OmegaConf.to_container(cfg)
    assert result == data

@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_list_operations(items):
    """Test list operations preserve order and values."""
    from cobruh.config import ListConfig
    cfg = ListConfig(items)
    
    # Test indexing
    for i, item in enumerate(items):
        assert cfg[i] == item
    
    # Test conversion back
    assert cfg.to_list() == items
```

---

## Regression Tests

Track and test known bugs:

```python
class TestRegressions:
    """Tests for previously found bugs."""
    
    def test_issue_42_circular_reference(self):
        """
        Regression test for issue #42.
        Circular references should be detected and raise error.
        """
        cfg = OmegaConf.create({
            "a": "${b}",
            "b": "${c}",
            "c": "${a}"
        })
        
        from cobruh.config.errors import CircularReferenceError
        with pytest.raises(CircularReferenceError):
            OmegaConf.to_container(cfg, resolve=True)
    
    def test_issue_67_none_override(self):
        """
        Regression test for issue #67.
        Setting value to None should work.
        """
        cfg = OmegaConf.create({"key": "value"})
        cfg.key = None
        assert cfg.key is None
```

---

## Test Fixtures

### Common Fixtures

```python
# tests/conftest.py

import pytest
from pathlib import Path
from cobruh import DictConfig, OmegaConf

@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def simple_config():
    """Simple config for testing."""
    return DictConfig({
        "model": {"name": "resnet", "layers": 50},
        "data": {"batch_size": 32, "num_workers": 4}
    })

@pytest.fixture
def config_with_interpolation():
    """Config with interpolations."""
    return OmegaConf.create({
        "base_dir": "/tmp",
        "data_dir": "${base_dir}/data",
        "output_dir": "${base_dir}/outputs"
    })

@pytest.fixture
def structured_config():
    """Structured config from dataclass."""
    from dataclasses import dataclass
    
    @dataclass
    class Config:
        name: str = "test"
        value: int = 42
    
    return OmegaConf.create(Config)
```

---

## Testing Best Practices

### 1. Naming Conventions

- Test files: `test_<module>.py`
- Test classes: `Test<Feature>`
- Test functions: `test_<specific_behavior>`
- Use descriptive names that explain what is being tested

### 2. Test Organization

```python
class TestDictConfig:
    """Tests for DictConfig."""
    
    class TestCreation:
        """Tests for config creation."""
        
        def test_from_dict(self):
            pass
        
        def test_from_list(self):
            pass
    
    class TestAccess:
        """Tests for value access."""
        
        def test_attribute_access(self):
            pass
        
        def test_dict_access(self):
            pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_merge_configs():
    # Arrange
    cfg1 = OmegaConf.create({"a": 1, "b": 2})
    cfg2 = OmegaConf.create({"b": 3, "c": 4})
    
    # Act
    result = OmegaConf.merge(cfg1, cfg2)
    
    # Assert
    assert result.a == 1
    assert result.b == 3
    assert result.c == 4
```

### 4. Test Independence

- Each test should be independent
- No shared state between tests
- Use fixtures for setup
- Clean up after tests

### 5. Edge Cases and Error Conditions

```python
def test_edge_cases():
    """Test edge cases."""
    # Empty config
    cfg = DictConfig({})
    assert len(cfg) == 0
    
    # Deeply nested
    cfg = DictConfig({"a": {"b": {"c": {"d": "value"}}}})
    assert cfg.a.b.c.d == "value"
    
    # Special characters
    cfg = DictConfig({"key-with-dash": "value"})
    assert cfg["key-with-dash"] == "value"

def test_error_conditions():
    """Test error handling."""
    cfg = DictConfig({"key": "value"})
    
    # Missing key
    with pytest.raises(ConfigAttributeError):
        _ = cfg.missing
    
    # Type error
    with pytest.raises(TypeError):
        cfg[123] = "value"
```

---

## Coverage Goals

### Target Coverage

- **Overall**: >90%
- **Core modules**: >95%
- **Utils**: >85%
- **CLI**: >80%

### Coverage Commands

```bash
# Run tests with coverage
pytest --cov=cobruh --cov-report=html --cov-report=term

# Generate coverage report
coverage report -m

# View HTML report
open htmlcov/index.html
```

---

## Continuous Integration

### CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: [3.8, 3.9, '3.10', 3.11]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      
      - name: Run tests
        run: |
          pytest --cov=cobruh --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Test Documentation

### Docstrings for Tests

```python
def test_complex_scenario():
    """
    Test complex config composition scenario.
    
    This test verifies that when:
    1. Multiple configs are merged
    2. With overlapping keys
    3. And command-line overrides
    
    Then:
    - The correct merge order is maintained
    - Overrides take precedence
    - No data is lost
    
    Related issues: #123, #456
    """
    # Test implementation
```

---

## Summary

The testing strategy ensures:

- ✅ High code coverage (>90%)
- ✅ Comprehensive test suite (unit, integration, e2e)
- ✅ Performance benchmarks
- ✅ Regression prevention
- ✅ Cross-platform compatibility
- ✅ Clear test documentation
- ✅ Automated CI/CD pipeline
