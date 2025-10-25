"""ListConfig implementation - list-based configuration container."""

from typing import Any, Iterator, Optional, Union
from omegaconf import ListConfig as OmegaListConfig, OmegaConf

from cobruh.config.base_container import BaseContainer
from cobruh.config.errors import ReadOnlyConfigError


class ListConfig(BaseContainer):
    """List-based configuration container with index access.
    
    This class wraps OmegaConf's ListConfig to provide additional functionality
    and a consistent API for Cobruh.
    
    Examples:
        >>> cfg = ListConfig([1, 2, 3])
        >>> cfg[0]
        1
        >>> cfg.append(4)
        >>> len(cfg)
        4
    """
    
    def __init__(
        self,
        content: Optional[Union[list[Any], OmegaListConfig]] = None,
        parent: Optional[BaseContainer] = None,
        key: Optional[str] = None,
    ) -> None:
        """Initialize a ListConfig.
        
        Args:
            content: List or OmegaConf ListConfig to wrap
            parent: Parent container (for nested configs)
            key: Key in the parent container
        """
        super().__init__()
        
        if content is None:
            content = []
        
        # If it's already an OmegaConf ListConfig, use it directly
        if isinstance(content, OmegaListConfig):
            self._content = content
        else:
            # Create an OmegaConf ListConfig from the list
            self._content = OmegaConf.create(content)
        
        if parent is not None and key is not None:
            self._set_parent(parent, key)
    
    def _get_item(self, index: int) -> Any:
        """Get an item from the list.
        
        Args:
            index: The index to retrieve
            
        Returns:
            The value at the index
            
        Raises:
            IndexError: If the index is out of range
        """
        value = self._content[index]
        
        # If the value is an OmegaConf container, wrap it in Cobruh container
        if OmegaConf.is_dict(value):
            from cobruh.config.dictconfig import DictConfig
            wrapped = DictConfig(value, parent=self, key=str(index))
            return wrapped
        elif OmegaConf.is_list(value):
            wrapped = ListConfig(value, parent=self, key=str(index))
            return wrapped
        
        return value
    
    def _set_item(self, index: int, value: Any) -> None:
        """Set an item in the list.
        
        Args:
            index: The index to set
            value: The value to set
            
        Raises:
            ReadOnlyConfigError: If the config is read-only
        """
        if self._get_metadata("readonly", False):
            raise ReadOnlyConfigError(str(index))
        
        # Unwrap Cobruh containers to OmegaConf containers
        if hasattr(value, "_content"):
            value = value._content
        
        self._content[index] = value
    
    def __getitem__(self, index: int) -> Any:
        """Get item at index.
        
        Args:
            index: The index to retrieve
            
        Returns:
            The value at the index
        """
        return self._get_item(index)
    
    def __setitem__(self, index: int, value: Any) -> None:
        """Set item at index.
        
        Args:
            index: The index to set
            value: The value to set
        """
        self._set_item(index, value)
    
    def __len__(self) -> int:
        """Get the length of the list.
        
        Returns:
            The number of items in the list
        """
        return len(self._content)
    
    def __iter__(self) -> Iterator[Any]:
        """Iterate over items in the list.
        
        Returns:
            An iterator over the items
        """
        for i in range(len(self)):
            yield self[i]
    
    def append(self, value: Any) -> None:
        """Append a value to the list.
        
        Args:
            value: The value to append
            
        Raises:
            ReadOnlyConfigError: If the config is read-only
        """
        if self._get_metadata("readonly", False):
            raise ReadOnlyConfigError()
        
        # Unwrap Cobruh containers to OmegaConf containers
        if hasattr(value, "_content"):
            value = value._content
        
        self._content.append(value)
    
    def extend(self, values: list[Any]) -> None:
        """Extend the list with multiple values.
        
        Args:
            values: The values to add
            
        Raises:
            ReadOnlyConfigError: If the config is read-only
        """
        if self._get_metadata("readonly", False):
            raise ReadOnlyConfigError()
        
        for value in values:
            self.append(value)
    
    def insert(self, index: int, value: Any) -> None:
        """Insert a value at the specified index.
        
        Args:
            index: The index at which to insert
            value: The value to insert
            
        Raises:
            ReadOnlyConfigError: If the config is read-only
        """
        if self._get_metadata("readonly", False):
            raise ReadOnlyConfigError()
        
        # Unwrap Cobruh containers to OmegaConf containers
        if hasattr(value, "_content"):
            value = value._content
        
        self._content.insert(index, value)
    
    def to_list(self) -> list[Any]:
        """Convert to a plain Python list.
        
        Returns:
            Plain list representation
        """
        return OmegaConf.to_container(self._content, resolve=True)
    
    def __repr__(self) -> str:
        """String representation of the list config.
        
        Returns:
            String representation
        """
        return f"ListConfig({list(self._content)})"
    
    def __str__(self) -> str:
        """String representation of the list config.
        
        Returns:
            String representation
        """
        return str(list(self._content))
