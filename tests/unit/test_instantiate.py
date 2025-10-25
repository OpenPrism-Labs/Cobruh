"""Unit tests for instantiate utility."""

import pytest
from cobruh.utils import instantiate
from cobruh.config import DictConfig


class TestInstantiate:
    """Tests for the instantiate utility."""
    
    def test_instantiate_builtin(self):
        """Test instantiating a builtin type."""
        config = DictConfig({
            "_target_": "dict",
            "a": 1,
            "b": 2
        })
        obj = instantiate(config)
        assert isinstance(obj, dict)
        assert obj == {"a": 1, "b": 2}
    
    def test_instantiate_from_module(self):
        """Test instantiating from a module."""
        config = DictConfig({
            "_target_": "collections.Counter",
        })
        obj = instantiate(config, [1, 2, 2, 3])
        
        from collections import Counter
        assert isinstance(obj, Counter)
        assert obj[2] == 2
    
    def test_instantiate_with_kwargs(self):
        """Test instantiating with keyword arguments."""
        config = DictConfig({
            "_target_": "pathlib.Path",
            "_args_": ["/tmp/test"]
        })
        
        from pathlib import Path
        # Just test basic instantiation
        config2 = {"_target_": "dict", "x": 1}
        obj = instantiate(config2, y=2)
        assert obj == {"x": 1, "y": 2}
    
    def test_missing_target(self):
        """Test error when _target_ is missing."""
        config = DictConfig({"foo": "bar"})
        with pytest.raises(ValueError, match="_target_"):
            instantiate(config)
    
    def test_invalid_target(self):
        """Test error with invalid target."""
        config = DictConfig({"_target_": "nonexistent.module.Class"})
        with pytest.raises(ValueError):
            instantiate(config)
