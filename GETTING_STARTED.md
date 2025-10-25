# Getting Started with Cobruh

This guide will help you get started with Cobruh, a hierarchical configuration management framework for Python.

## Installation

Install Cobruh using pip:

```bash
pip install cobruh
```

Or for development:

```bash
git clone https://github.com/OpenPrism-Labs/Cobruh.git
cd Cobruh
pip install -e ".[dev]"
```

## Basic Concepts

### Configuration Files

Cobruh uses YAML files to store configuration. Create a `configs` directory:

```
my_project/
├── configs/
│   ├── config.yaml
│   ├── model/
│   │   ├── resnet50.yaml
│   │   └── vgg.yaml
│   └── optimizer/
│       ├── adam.yaml
│       └── sgd.yaml
└── train.py
```

### Main Configuration

`configs/config.yaml`:

```yaml
defaults:
  - model: resnet50
  - optimizer: adam

batch_size: 32
epochs: 100
seed: 42
```

### Group Configurations

`configs/model/resnet50.yaml`:

```yaml
name: resnet
layers: 50
pretrained: false
```

`configs/optimizer/adam.yaml`:

```yaml
name: adam
lr: 0.001
betas: [0.9, 0.999]
```

## Using the `@cobruh.main()` Decorator

The simplest way to use Cobruh is with the `@cobruh.main()` decorator:

```python
import cobruh
from cobruh import DictConfig

@cobruh.main(config_path="configs", config_name="config")
def train(cfg: DictConfig) -> None:
    """Training function."""
    print(f"Model: {cfg.model.name}")
    print(f"Batch size: {cfg.batch_size}")
    print(f"Learning rate: {cfg.optimizer.lr}")
    
    # Your training code here
    model = create_model(cfg.model)
    optimizer = create_optimizer(cfg.optimizer)
    # ...

if __name__ == "__main__":
    train()
```

Run your script:

```bash
# Use default configuration
python train.py

# Override specific values
python train.py batch_size=64 optimizer.lr=0.01 epochs=200

# Use different config groups
python train.py model=vgg optimizer=sgd
```

## Programmatic Composition

For more control, use the programmatic API:

```python
import cobruh
from cobruh import DictConfig

# Initialize Cobruh
cobruh.initialize(config_path="configs")

# Compose configuration
cfg = cobruh.compose(
    config_name="config",
    overrides=["batch_size=128", "model=vgg"]
)

# Use the config
print(cfg.model.name)
print(cfg.batch_size)
```

## Configuration Access

Access configuration values using dot notation or dictionary-style:

```python
# Dot notation (recommended)
model_name = cfg.model.name
learning_rate = cfg.optimizer.lr

# Dictionary-style
model_name = cfg["model"]["name"]
learning_rate = cfg["optimizer"]["lr"]

# Mixed
model_name = cfg.model["name"]
```

## Type Safety with Dataclasses

Use Python dataclasses for type-safe configurations:

```python
from dataclasses import dataclass
from cobruh import ConfigStore, compose

@dataclass
class ModelConfig:
    name: str = "resnet"
    layers: int = 50
    pretrained: bool = False

@dataclass
class OptimizerConfig:
    name: str = "adam"
    lr: float = 0.001

@dataclass
class TrainConfig:
    model: ModelConfig = ModelConfig()
    optimizer: OptimizerConfig = OptimizerConfig()
    batch_size: int = 32
    epochs: int = 100

# Register the config
cs = ConfigStore.instance()
cs.store(name="train_config", node=TrainConfig)

# Use it
cfg = compose(config_name="train_config")
```

## Object Instantiation

Create Python objects from configuration:

```python
from cobruh.utils import instantiate

# Configuration with _target_
config = {
    "_target_": "torch.optim.Adam",
    "lr": 0.001,
    "betas": [0.9, 0.999],
    "weight_decay": 0.0001
}

# Instantiate the optimizer
optimizer = instantiate(config, params=model.parameters())
```

In YAML:

```yaml
optimizer:
  _target_: torch.optim.Adam
  lr: 0.001
  betas: [0.9, 0.999]
  weight_decay: 0.0001
```

Then in Python:

```python
from cobruh.utils import instantiate

optimizer = instantiate(cfg.optimizer, params=model.parameters())
```

## Command-Line Overrides

Override any configuration value from the command line:

```bash
# Simple value override
python train.py batch_size=64

# Nested value override
python train.py model.layers=101 optimizer.lr=0.01

# Multiple overrides
python train.py batch_size=128 epochs=200 seed=123

# Boolean values
python train.py model.pretrained=true

# Add new values (with +)
python train.py +new_param=value

# Override or add (with ~)
python train.py ~maybe_new=value
```

## Configuration Composition

Compose configurations from multiple sources:

```yaml
# config.yaml
defaults:
  - model: resnet50
  - optimizer: adam
  - dataset: imagenet

batch_size: 32
```

The `defaults` list specifies which configs to load from each group. They are merged in order.

## Best Practices

### 1. Organize by Component

```
configs/
├── config.yaml          # Main config
├── model/              # Model configs
│   ├── resnet50.yaml
│   └── vgg.yaml
├── optimizer/          # Optimizer configs
│   ├── adam.yaml
│   └── sgd.yaml
└── dataset/           # Dataset configs
    ├── imagenet.yaml
    └── cifar10.yaml
```

### 2. Use Type Hints

```python
from cobruh import DictConfig

@cobruh.main()
def train(cfg: DictConfig) -> None:
    # cfg is type-hinted for better IDE support
    model_name: str = cfg.model.name
```

### 3. Validate Early

```python
@cobruh.main()
def train(cfg: DictConfig) -> None:
    # Validate required fields early
    required = ["model.name", "optimizer.lr", "batch_size"]
    for field in required:
        parts = field.split(".")
        obj = cfg
        for part in parts:
            obj = obj[part]  # Will raise error if missing
```

### 4. Document Your Configs

```yaml
# config.yaml
# Main training configuration
# See docs/config.md for details

defaults:
  - model: resnet50  # Architecture to use
  - optimizer: adam  # Optimization algorithm

# Training hyperparameters
batch_size: 32  # Number of samples per batch
epochs: 100     # Number of training epochs
lr: 0.001      # Learning rate (can be overridden)
```

## Next Steps

- Read the [Architecture Documentation](../llm_docs/architecture/ARCHITECTURE.md)
- Check out the [API Specification](../llm_docs/api/API_SPECIFICATION.md)
- Explore the [Examples](../examples/)
- Run the tests: `pytest tests/`

## Getting Help

- Check the [README](../README.md)
- Look at the [examples](../examples/)
- Read the [documentation](../llm_docs/)
- Open an issue on GitHub

Happy configuring! 🎉
