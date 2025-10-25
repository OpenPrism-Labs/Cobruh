# Cobruh

A hierarchical configuration management framework for Python applications, inspired by Facebook's Hydra.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

- 🏗️ **Hierarchical Configuration** - Split configs into reusable groups
- 🔄 **Composable** - Merge multiple configs dynamically
- 🔒 **Type-Safe** - Validate using Python dataclasses
- 🖥️ **CLI Overrides** - Override any config value from command line
- 🔗 **Interpolation** - Reference config values and environment variables
- ⚡ **Object Instantiation** - Create Python objects from config

## Installation

```bash
pip install cobruh
```

Or install from source:

```bash
git clone https://github.com/OpenPrism-Labs/Cobruh.git
cd Cobruh
pip install -e .
```

## Quick Start

### 1. Create Your Configuration

Create a `configs` directory with your YAML files:

```yaml
# configs/config.yaml
defaults:
  - model: resnet50
  - optimizer: adam

batch_size: 32
epochs: 100
```

```yaml
# configs/model/resnet50.yaml
name: resnet
layers: 50
pretrained: false
```

```yaml
# configs/optimizer/adam.yaml
name: adam
lr: 0.001
betas: [0.9, 0.999]
```

### 2. Use in Your Application

```python
import cobruh
from cobruh import DictConfig

@cobruh.main(config_path="configs", config_name="config")
def train(cfg: DictConfig) -> None:
    print(f"Model: {cfg.model.name}")
    print(f"Optimizer: {cfg.optimizer.name}")
    print(f"Batch size: {cfg.batch_size}")
    
    # Your training code here...

if __name__ == "__main__":
    train()
```

### 3. Run with CLI Overrides

```bash
# Use default config
python app.py

# Override specific values
python app.py batch_size=64 optimizer.lr=0.01

# Switch entire config groups
python app.py model=vgg optimizer=sgd
```

## Advanced Usage

### Programmatic Composition

```python
import cobruh

# Initialize
cobruh.initialize(config_path="configs")

# Compose configuration
cfg = cobruh.compose(
    config_name="config",
    overrides=["model=resnet50", "batch_size=128"]
)

print(cfg.model.name)  # resnet
```

### Object Instantiation

```python
from cobruh.utils import instantiate

# Config with _target_
config = {
    "_target_": "torch.optim.Adam",
    "lr": 0.001,
    "betas": [0.9, 0.999]
}

# Instantiate the object
optimizer = instantiate(config, params=model.parameters())
```

### Config Store

```python
from dataclasses import dataclass
from cobruh import ConfigStore

@dataclass
class ModelConfig:
    name: str = "resnet"
    layers: int = 50

# Register config
cs = ConfigStore.instance()
cs.store(name="base_model", node=ModelConfig)
```

## Python Version Support

Cobruh supports Python 3.10 and later versions:
- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12
- ✅ Python 3.13+

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/OpenPrism-Labs/Cobruh.git
cd Cobruh

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cobruh --cov-report=html

# Run specific test file
pytest tests/unit/test_dictconfig.py
```

### Code Quality

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Lint
ruff check src tests

# Type check
mypy src
```

## Documentation

For detailed documentation, see the `llm_docs/` directory:

- [Architecture](llm_docs/architecture/ARCHITECTURE.md) - System design and algorithms
- [API Specification](llm_docs/api/API_SPECIFICATION.md) - Complete API reference
- [Implementation Roadmap](llm_docs/implementation/IMPLEMENTATION_ROADMAP.md) - Development plan
- [Testing Strategy](llm_docs/testing/TESTING_STRATEGY.md) - Testing approach

## Examples

Check out the `examples/` directory for complete examples:
- `simple_app.py` - Basic application with config composition

## Comparison with Hydra

Cobruh is inspired by [Hydra](https://hydra.cc/) and aims to provide a similar API while being:
- Lighter weight
- Easier to understand
- More focused on core configuration management

If you're familiar with Hydra, you'll feel right at home with Cobruh!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [Facebook's Hydra](https://hydra.cc/)
- Built on top of [OmegaConf](https://github.com/omry/omegaconf)

## Project Status

🚧 **Alpha** - This project is in early development. APIs may change.
