"""Base container class for configuration objects."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseContainer(ABC):
    """Base class for all configuration containers."""
    
    def __init__(self) -> None:
        """Initialize the base container."""
        self._metadata: dict[str, Any] = {}
        self._parent: Optional["BaseContainer"] = None
        self._key: Optional[str] = None
    
    @abstractmethod
    def _get_item(self, key: Any) -> Any:
        """Get an item from the container.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The value at the key
        """
        pass
    
    @abstractmethod
    def _set_item(self, key: Any, value: Any) -> None:
        """Set an item in the container.
        
        Args:
            key: The key to set
            value: The value to set
        """
        pass
    
    def _set_parent(self, parent: "BaseContainer", key: str) -> None:
        """Set the parent container and key.
        
        Args:
            parent: The parent container
            key: The key in the parent container
        """
        self._parent = parent
        self._key = key
    
    def _get_full_key(self) -> str:
        """Get the full dot-notation key path to this container.
        
        Returns:
            The full key path
        """
        if self._parent is None or self._key is None:
            return ""
        
        parent_key = self._parent._get_full_key()
        if parent_key:
            return f"{parent_key}.{self._key}"
        return self._key
    
    def _set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata value.
        
        Args:
            key: The metadata key
            value: The metadata value
        """
        self._metadata[key] = value
    
    def _get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value.
        
        Args:
            key: The metadata key
            default: Default value if key doesn't exist
            
        Returns:
            The metadata value or default
        """
        return self._metadata.get(key, default)
