"""Configuration node types for representing values and special states."""

from enum import Enum
from typing import Any, Optional


class NodeType(Enum):
    """Type of configuration node."""
    
    VALUE = "value"
    MISSING = "missing"
    INTERPOLATION = "interpolation"
    NONE = "none"


class Node:
    """Base class for configuration nodes."""
    
    def __init__(self, value: Any = None, node_type: NodeType = NodeType.VALUE) -> None:
        """Initialize a Node.
        
        Args:
            value: The value stored in this node
            node_type: The type of this node
        """
        self._value = value
        self._node_type = node_type
    
    @property
    def value(self) -> Any:
        """Get the node value."""
        return self._value
    
    @property
    def node_type(self) -> NodeType:
        """Get the node type."""
        return self._node_type
    
    def __repr__(self) -> str:
        """String representation of the node."""
        return f"{self.__class__.__name__}(value={self._value!r}, type={self._node_type.value})"


class ValueNode(Node):
    """Node that stores an actual value."""
    
    def __init__(self, value: Any) -> None:
        """Initialize a ValueNode.
        
        Args:
            value: The value to store
        """
        super().__init__(value, NodeType.VALUE)


class MissingNode(Node):
    """Node that represents a missing mandatory value."""
    
    def __init__(self) -> None:
        """Initialize a MissingNode."""
        super().__init__(None, NodeType.MISSING)
    
    def __repr__(self) -> str:
        """String representation of the missing node."""
        return "MISSING"


class InterpolationNode(Node):
    """Node that contains an unresolved interpolation."""
    
    def __init__(self, interpolation: str) -> None:
        """Initialize an InterpolationNode.
        
        Args:
            interpolation: The interpolation expression (e.g., "${key}")
        """
        super().__init__(interpolation, NodeType.INTERPOLATION)
    
    @property
    def interpolation(self) -> str:
        """Get the interpolation expression."""
        return self._value
    
    def __repr__(self) -> str:
        """String representation of the interpolation node."""
        return f"Interpolation({self._value!r})"


class NoneNode(Node):
    """Node that explicitly stores None value."""
    
    def __init__(self) -> None:
        """Initialize a NoneNode."""
        super().__init__(None, NodeType.NONE)


# Sentinel value for missing mandatory configuration
MISSING = MissingNode()
