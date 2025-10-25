"""Unit tests for DictConfig."""

import pytest
from cobruh.config import DictConfig, ConfigAttributeError, ConfigKeyError


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
    
    def test_missing_key_dict_access(self):
        """Test error on missing key with dict access."""
        cfg = DictConfig({"key": "value"})
        with pytest.raises(ConfigKeyError):
            _ = cfg["missing_key"]
    
    def test_nested_update(self):
        """Test updating nested values."""
        cfg = DictConfig({"model": {"name": "resnet"}})
        cfg.model.name = "vgg"
        assert cfg.model.name == "vgg"
    
    def test_contains(self):
        """Test checking if key exists."""
        cfg = DictConfig({"key": "value"})
        assert "key" in cfg
        assert "missing" not in cfg
    
    def test_keys(self):
        """Test getting keys."""
        cfg = DictConfig({"a": 1, "b": 2})
        keys = cfg.keys()
        assert set(keys) == {"a", "b"}
    
    def test_values(self):
        """Test getting values."""
        cfg = DictConfig({"a": 1, "b": 2})
        values = cfg.values()
        assert set(values) == {1, 2}
    
    def test_items(self):
        """Test getting items."""
        cfg = DictConfig({"a": 1, "b": 2})
        items = cfg.items()
        assert set(items) == {("a", 1), ("b", 2)}
    
    def test_get_with_default(self):
        """Test get with default value."""
        cfg = DictConfig({"key": "value"})
        assert cfg.get("key") == "value"
        assert cfg.get("missing", "default") == "default"
    
    def test_update(self):
        """Test updating config."""
        cfg = DictConfig({"a": 1})
        cfg.update({"b": 2, "c": 3})
        assert cfg.a == 1
        assert cfg.b == 2
        assert cfg.c == 3
    
    def test_to_dict(self):
        """Test converting to plain dict."""
        cfg = DictConfig({"model": {"name": "resnet", "layers": 50}})
        d = cfg.to_dict()
        assert isinstance(d, dict)
        assert d == {"model": {"name": "resnet", "layers": 50}}
    
    def test_nested_dict_config(self):
        """Test that nested dicts become DictConfigs."""
        cfg = DictConfig({"outer": {"inner": {"value": 42}}})
        assert isinstance(cfg.outer, DictConfig)
        assert isinstance(cfg.outer.inner, DictConfig)
        assert cfg.outer.inner.value == 42
