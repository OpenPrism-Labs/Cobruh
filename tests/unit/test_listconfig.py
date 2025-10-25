"""Unit tests for ListConfig."""

import pytest
from cobruh.config import ListConfig


class TestListConfig:
    """Tests for ListConfig class."""
    
    def test_create_empty(self):
        """Test creating empty ListConfig."""
        cfg = ListConfig([])
        assert len(cfg) == 0
    
    def test_create_from_list(self):
        """Test creating ListConfig from list."""
        data = [1, 2, 3]
        cfg = ListConfig(data)
        assert len(cfg) == 3
        assert cfg[0] == 1
        assert cfg[1] == 2
        assert cfg[2] == 3
    
    def test_index_access(self):
        """Test index access."""
        cfg = ListConfig([10, 20, 30])
        assert cfg[0] == 10
        assert cfg[2] == 30
    
    def test_index_update(self):
        """Test updating by index."""
        cfg = ListConfig([1, 2, 3])
        cfg[1] = 99
        assert cfg[1] == 99
    
    def test_append(self):
        """Test appending values."""
        cfg = ListConfig([1, 2])
        cfg.append(3)
        assert len(cfg) == 3
        assert cfg[2] == 3
    
    def test_extend(self):
        """Test extending with multiple values."""
        cfg = ListConfig([1, 2])
        cfg.extend([3, 4])
        assert len(cfg) == 4
        assert list(cfg) == [1, 2, 3, 4]
    
    def test_insert(self):
        """Test inserting value at index."""
        cfg = ListConfig([1, 3])
        cfg.insert(1, 2)
        assert len(cfg) == 3
        assert list(cfg) == [1, 2, 3]
    
    def test_iteration(self):
        """Test iterating over list."""
        cfg = ListConfig([1, 2, 3])
        result = []
        for item in cfg:
            result.append(item)
        assert result == [1, 2, 3]
    
    def test_to_list(self):
        """Test converting to plain list."""
        cfg = ListConfig([1, 2, 3])
        lst = cfg.to_list()
        assert isinstance(lst, list)
        assert lst == [1, 2, 3]
    
    def test_nested_list(self):
        """Test nested lists."""
        cfg = ListConfig([[1, 2], [3, 4]])
        assert isinstance(cfg[0], ListConfig)
        assert cfg[0][0] == 1
        assert cfg[1][1] == 4
    
    def test_mixed_content(self):
        """Test list with mixed types."""
        cfg = ListConfig([1, "two", 3.0, True])
        assert cfg[0] == 1
        assert cfg[1] == "two"
        assert cfg[2] == 3.0
        assert cfg[3] is True
