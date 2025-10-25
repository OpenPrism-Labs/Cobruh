"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def simple_config(temp_config_dir):
    """Create a simple config file."""
    config_file = temp_config_dir / "config.yaml"
    config_file.write_text("""
model:
  name: resnet
  layers: 50

optimizer:
  name: adam
  lr: 0.001

batch_size: 32
""")
    return temp_config_dir


@pytest.fixture
def config_with_defaults(temp_config_dir):
    """Create config files with defaults list."""
    # Main config
    config_file = temp_config_dir / "config.yaml"
    config_file.write_text("""
defaults:
  - model: resnet50
  - optimizer: adam

batch_size: 32
""")
    
    # Model configs
    model_dir = temp_config_dir / "model"
    model_dir.mkdir()
    
    (model_dir / "resnet50.yaml").write_text("""
name: resnet
layers: 50
""")
    
    (model_dir / "vgg.yaml").write_text("""
name: vgg
layers: 16
""")
    
    # Optimizer configs
    opt_dir = temp_config_dir / "optimizer"
    opt_dir.mkdir()
    
    (opt_dir / "adam.yaml").write_text("""
name: adam
lr: 0.001
betas: [0.9, 0.999]
""")
    
    (opt_dir / "sgd.yaml").write_text("""
name: sgd
lr: 0.01
momentum: 0.9
""")
    
    return temp_config_dir
