"""Unit tests for configuration composition."""

import pytest
from pathlib import Path

from cobruh import compose, initialize
from cobruh.config import DictConfig, ConfigCompositionError


class TestCompose:
    """Tests for configuration composition."""
    
    def test_compose_empty(self):
        """Test composing empty config."""
        cfg = compose(config_name=None)
        assert isinstance(cfg, DictConfig)
        assert len(cfg) == 0
    
    def test_compose_simple(self, simple_config):
        """Test composing a simple config."""
        initialize(config_path=str(simple_config))
        cfg = compose(config_name="config")
        
        assert cfg.model.name == "resnet"
        assert cfg.model.layers == 50
        assert cfg.optimizer.name == "adam"
        assert cfg.batch_size == 32
    
    def test_compose_with_overrides(self, simple_config):
        """Test composing with overrides."""
        initialize(config_path=str(simple_config))
        cfg = compose(
            config_name="config",
            overrides=["batch_size=64", "optimizer.lr=0.01"]
        )
        
        assert cfg.batch_size == 64
        assert cfg.optimizer.lr == 0.01
    
    def test_compose_with_defaults(self, config_with_defaults):
        """Test composing config with defaults list."""
        initialize(config_path=str(config_with_defaults))
        cfg = compose(config_name="config")
        
        # Check that defaults were applied
        assert cfg.model.name == "resnet"
        assert cfg.model.layers == 50
        assert cfg.optimizer.name == "adam"
        assert cfg.optimizer.lr == 0.001
        assert cfg.batch_size == 32
    
    def test_compose_override_defaults(self, config_with_defaults):
        """Test overriding default selections."""
        initialize(config_path=str(config_with_defaults))
        cfg = compose(
            config_name="config",
            overrides=["model.layers=101", "optimizer.lr=0.1"]
        )
        
        assert cfg.model.layers == 101
        assert cfg.optimizer.lr == 0.1
    
    def test_compose_type_conversion(self, simple_config):
        """Test type conversion in overrides."""
        initialize(config_path=str(simple_config))
        cfg = compose(
            config_name="config",
            overrides=[
                "batch_size=128",
                "optimizer.lr=0.0001",
                "model.name=vgg"
            ]
        )
        
        assert cfg.batch_size == 128
        assert isinstance(cfg.batch_size, int)
        assert cfg.optimizer.lr == 0.0001
        assert isinstance(cfg.optimizer.lr, float)
        assert cfg.model.name == "vgg"
    
    def test_compose_missing_config(self):
        """Test error when config file is missing."""
        initialize(config_path="/tmp/nonexistent")
        with pytest.raises(ConfigCompositionError):
            compose(config_name="missing")
