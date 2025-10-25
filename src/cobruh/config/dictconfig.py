"""DictConfig implementation - dictionary-based configuration container."""

from typing import Any, Iterator, Optional, Union
from omegaconf import DictConfig as OmegaDictConfig, OmegaConf

from cobruh.config.base_container import BaseContainer
from cobruh.config.errors import (
    ConfigAttributeError,
    ConfigKeyError,
    ReadOnlyConfigError,
)


class DictConfig(BaseContainer):
    """Dictionary-based configuration container with dot-notation access.
    
    This class wraps OmegaConf's DictConfig to provide additional functionality
    and a consistent API for Cobruh.
    
    Examples:
        >>> cfg = DictConfig({"model": {"name": "resnet", "layers": 50}})
        >>> cfg.model.name
        'resnet'
        >>> cfg["model"]["layers"]
        50
    """
    
    def __init__(
        self,
        content: Optional[Union[dict[str, Any], OmegaDictConfig]] = None,
        parent: Optional[BaseContainer] = None,
        key: Optional[str] = None,
    ) -> None:
        """Initialize a DictConfig.
        
        Args:
            content: Dictionary or OmegaConf DictConfig to wrap
            parent: Parent container (for nested configs)
            key: Key in the parent container
        """
        super().__init__()
        
        if content is None:
            content = {}
        
        # If it's already an OmegaConf DictConfig, use it directly
        if isinstance(content, OmegaDictConfig):
            self._content = content
        else:
            # Create an OmegaConf DictConfig from the dict
            self._content = OmegaConf.create(content)
        
        if parent is not None and key is not None:
            self._set_parent(parent, key)
    
    def _get_item(self, key: str) -> Any:
        """Get an item from the config.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The value at the key
            
        Raises:
            ConfigKeyError: If the key doesn't exist
        """
        try:
            value = self._content[key]
            
            # If the value is an OmegaConf container, wrap it in Cobruh container
            if OmegaConf.is_dict(value):
                from cobruh.config.dictconfig import DictConfig
                wrapped = DictConfig(value, parent=self, key=key)
                return wrapped
            elif OmegaConf.is_list(value):
                from cobruh.config.listconfig import ListConfig
                wrapped = ListConfig(value, parent=self, key=key)
                return wrapped
            
            return value
        except KeyError:
            raise ConfigKeyError(key, self._get_full_key())
    
    def _set_item(self, key: str, value: Any) -> None:
        """Set an item in the config.
        
        Args:
            key: The key to set
            value: The value to set
            
        Raises:
            ReadOnlyConfigError: If the config is read-only
        """
        if self._get_metadata("readonly", False):
            raise ReadOnlyConfigError(key)
        
        # Unwrap Cobruh containers to OmegaConf containers
        if isinstance(value, DictConfig):
            value = value._content
        elif hasattr(value, "_content"):  # ListConfig
            value = value._content
        
        self._content[key] = value
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute using dot notation.
        
        Args:
            name: The attribute name
            
        Returns:
            The value at the attribute
            
        Raises:
            ConfigAttributeError: If the attribute doesn't exist
        """
        # Avoid infinite recursion for internal attributes
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        
        try:
            return self._get_item(name)
        except ConfigKeyError:
            raise ConfigAttributeError(name, self._get_full_key())
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute using dot notation.
        
        Args:
            name: The attribute name
            value: The value to set
        """
        # Internal attributes are set on the object itself
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self._set_item(name, value)
    
    def __getitem__(self, key: str) -> Any:
        """Get item using dictionary notation.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The value at the key
        """
        return self._get_item(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set item using dictionary notation.
        
        Args:
            key: The key to set
            value: The value to set
        """
        self._set_item(key, value)
    
    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the config.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return key in self._content
    
    def __len__(self) -> int:
        """Get the number of keys in the config.
        
        Returns:
            The number of keys
        """
        return len(self._content)
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over the keys in the config.
        
        Returns:
            An iterator over the keys
        """
        return iter(self._content)
    
    def keys(self) -> list[str]:
        """Get all keys in the config.
        
        Returns:
            List of keys
        """
        return list(self._content.keys())
    
    def values(self) -> list[Any]:
        """Get all values in the config.
        
        Returns:
            List of values
        """
        values = []
        for key in self.keys():
            values.append(self[key])
        return values
    
    def items(self) -> list[tuple[str, Any]]:
        """Get all key-value pairs in the config.
        
        Returns:
            List of (key, value) tuples
        """
        items = []
        for key in self.keys():
            items.append((key, self[key]))
        return items
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value with a default if the key doesn't exist.
        
        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The value at the key or the default
        """
        try:
            return self._get_item(key)
        except ConfigKeyError:
            return default
    
    def update(self, other: Union[dict[str, Any], "DictConfig"]) -> None:
        """Update the config with another dict or DictConfig.
        
        Args:
            other: Dictionary or DictConfig to merge in
        """
        if isinstance(other, DictConfig):
            other = other._content
        
        self._content.update(other)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to a plain Python dictionary.
        
        Returns:
            Plain dictionary representation
        """
        return OmegaConf.to_container(self._content, resolve=True)
    
    def __repr__(self) -> str:
        """String representation of the config.
        
        Returns:
            String representation
        """
        return f"DictConfig({dict(self._content)})"
    
    def __str__(self) -> str:
        """String representation of the config.
        
        Returns:
            String representation
        """
        return str(dict(self._content))
