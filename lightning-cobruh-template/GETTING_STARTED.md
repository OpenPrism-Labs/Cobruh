# Getting Started with Lightning-Cobruh Template

This guide will help you get started with the Lightning-Cobruh template for your deep learning projects.

## Table of Contents

1. [Installation](#installation)
2. [Project Structure](#project-structure)
3. [Quick Start](#quick-start)
4. [Configuration Guide](#configuration-guide)
5. [Training Your First Model](#training-your-first-model)
6. [Advanced Usage](#advanced-usage)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or conda package manager

### Basic Installation

```bash
# Clone the repository
git clone <your-repository-url>
cd lightning-cobruh-template

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the project in development mode
pip install -e .
```

### Verify Installation

```bash
# Test the installation
python -c "import lightning; import cobruh; print('Installation successful!')"
```

## Project Structure

```
lightning-cobruh-template/
├── configs/                    # All configuration files
│   ├── callbacks/             # Callback configurations
│   ├── data/                  # Data module configurations
│   ├── debug/                 # Debug mode configurations
│   ├── experiment/            # Experiment-specific configs
│   ├── logger/                # Logger configurations
│   ├── model/                 # Model configurations
│   ├── paths/                 # Path configurations
│   ├── trainer/               # Trainer configurations
│   ├── train.yaml             # Main training config
│   └── eval.yaml              # Main evaluation config
│
├── src/                       # Source code
│   ├── data/                  # Data modules
│   │   └── mnist_datamodule.py
│   ├── models/                # Models
│   │   ├── components/        # Model components
│   │   │   └── simple_dense_net.py
│   │   └── mnist_module.py    # Lightning module
│   ├── utils/                 # Utility functions
│   ├── train.py               # Training script
│   └── eval.py                # Evaluation script
│
├── tests/                     # Test files
├── scripts/                   # Shell scripts
├── data/                      # Data directory
├── logs/                      # Logs directory
└── notebooks/                 # Jupyter notebooks
```

## Quick Start

### 1. Run Your First Training

```bash
# Train with default configuration
python src/train.py

# The MNIST dataset will be downloaded automatically to data/MNIST/
```

### 2. Monitor Training

During training, you'll see:
- Progress bars showing training progress
- Loss and accuracy metrics
- Checkpoints saved to `logs/train/runs/<timestamp>/checkpoints/`

### 3. Evaluate Your Model

```bash
# Evaluate the trained model
python src/eval.py ckpt_path="logs/train/runs/<timestamp>/checkpoints/last.ckpt"
```

## Configuration Guide

### Understanding Cobruh Configuration

Cobruh uses YAML files for configuration. The main benefits:

1. **Hierarchical Organization**: Split configs into reusable groups
2. **Composition**: Combine multiple configs dynamically
3. **CLI Overrides**: Override any parameter from command line
4. **Type Safety**: Validate configurations using Python dataclasses

### Main Configuration Files

#### `configs/train.yaml`

The main training configuration file that composes all other configs:

```yaml
defaults:
  - data: mnist.yaml           # Data configuration
  - model: mnist.yaml          # Model configuration
  - callbacks: default.yaml    # Callbacks (checkpointing, early stopping)
  - logger: null               # Logger (null means no logging)
  - trainer: default.yaml      # PyTorch Lightning Trainer settings
  - paths: default.yaml        # Project paths
  - extras: default.yaml       # Extra utilities

task_name: "train"
tags: ["dev"]
train: True
test: True
seed: null
```

### Common Override Patterns

```bash
# Override single parameter
python src/train.py data.batch_size=128

# Override multiple parameters
python src/train.py data.batch_size=128 model.optimizer.lr=0.001

# Switch entire config groups
python src/train.py model=my_custom_model data=my_custom_data

# Use experiment configuration
python src/train.py experiment=example

# Enable logging
python src/train.py logger=tensorboard

# Train on GPU
python src/train.py trainer=gpu
```

## Training Your First Model

### Example 1: MNIST Classification (Default)

```bash
# Train with default settings
python src/train.py

# Output:
# - Model checkpoints: logs/train/runs/<timestamp>/checkpoints/
# - Logs: logs/train/runs/<timestamp>/
```

### Example 2: Custom Training

```bash
# Train with custom hyperparameters
python src/train.py \
    trainer.max_epochs=20 \
    data.batch_size=64 \
    model.optimizer.lr=0.0001 \
    tags=["custom_training","experiment_1"]
```

### Example 3: GPU Training

```bash
# Train on GPU with mixed precision
python src/train.py \
    trainer=gpu \
    trainer.precision=16-mixed \
    trainer.max_epochs=10
```

### Example 4: Debug Mode

```bash
# Quick debug run (1 epoch, CPU)
python src/train.py debug=default

# Fast dev run (1 batch of train/val/test)
python src/train.py debug=fdr
```

## Advanced Usage

### Creating Custom Experiments

1. Create a new experiment config in `configs/experiment/my_experiment.yaml`:

```yaml
# @package _global_

defaults:
  - override /data: mnist.yaml
  - override /model: mnist.yaml

tags: ["my_experiment", "custom"]

trainer:
  max_epochs: 15
  gradient_clip_val: 0.5

model:
  optimizer:
    lr: 0.005
  net:
    lin1_size: 512
    lin2_size: 256

data:
  batch_size: 128
```

2. Run the experiment:

```bash
python src/train.py experiment=my_experiment
```

### Adding Custom Loggers

1. Create logger config in `configs/logger/wandb.yaml`:

```yaml
wandb:
  _target_: lightning.pytorch.loggers.WandbLogger
  project: "my-project"
  name: "my-run"
  save_dir: "${paths.output_dir}"
```

2. Use the logger:

```bash
python src/train.py logger=wandb
```

### Resume Training

```bash
# Resume from checkpoint
python src/train.py \
    ckpt_path="logs/train/runs/<timestamp>/checkpoints/last.ckpt"
```

### Multiple Runs with Different Seeds

```bash
# Run with different seeds
python src/train.py seed=42 tags=["seed_42"]
python src/train.py seed=123 tags=["seed_123"]
python src/train.py seed=999 tags=["seed_999"]
```

## Creating Your Own Project

### 1. Create Custom Data Module

```python
# src/data/my_datamodule.py
from lightning import LightningDataModule
from torch.utils.data import DataLoader

class MyDataModule(LightningDataModule):
    def __init__(self, data_dir: str, batch_size: int = 32):
        super().__init__()
        self.save_hyperparameters()
    
    def prepare_data(self):
        # Download data
        pass
    
    def setup(self, stage: str):
        # Load data
        pass
    
    def train_dataloader(self):
        return DataLoader(...)
    
    def val_dataloader(self):
        return DataLoader(...)
    
    def test_dataloader(self):
        return DataLoader(...)
```

### 2. Create Data Config

```yaml
# configs/data/my_data.yaml
_target_: src.data.my_datamodule.MyDataModule

data_dir: ${paths.data_dir}/my_data
batch_size: 32
```

### 3. Create Custom Model

```python
# src/models/my_module.py
from lightning import LightningModule
import torch

class MyLitModule(LightningModule):
    def __init__(self, net, optimizer, scheduler):
        super().__init__()
        self.save_hyperparameters()
        self.net = net
    
    def forward(self, x):
        return self.net(x)
    
    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = torch.nn.functional.cross_entropy(logits, y)
        self.log("train/loss", loss)
        return loss
    
    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = torch.nn.functional.cross_entropy(logits, y)
        self.log("val/loss", loss)
    
    def configure_optimizers(self):
        optimizer = self.hparams.optimizer(params=self.parameters())
        return optimizer
```

### 4. Create Model Config

```yaml
# configs/model/my_model.yaml
_target_: src.models.my_module.MyLitModule

optimizer:
  _target_: torch.optim.Adam
  _partial_: true
  lr: 0.001

net:
  _target_: src.models.components.my_net.MyNet
  # your network parameters
```

### 5. Run Training

```bash
python src/train.py data=my_data model=my_model
```

## Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/unit/test_train.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only fast tests
pytest -k "not slow"
```

## Troubleshooting

### Common Issues

1. **CUDA out of memory**
   ```bash
   # Reduce batch size
   python src/train.py data.batch_size=32
   ```

2. **Slow data loading**
   ```bash
   # Increase num_workers
   python src/train.py data.num_workers=4
   ```

3. **Import errors**
   ```bash
   # Reinstall in development mode
   pip install -e .
   ```

## Next Steps

- Read the [README.md](README.md) for more details
- Explore example configurations in `configs/`
- Check out example notebooks in `notebooks/`
- Customize the template for your project

## Getting Help

- Check the [PyTorch Lightning documentation](https://lightning.ai/docs/pytorch/)
- Review [Cobruh documentation](https://github.com/OpenPrism-Labs/Cobruh)
- Open an issue on GitHub

Happy training! 🚀⚡
