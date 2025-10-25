"""Global configuration store for registering configs."""

from typing import Any, Optional
from dataclasses import is_dataclass

from cobruh.config.dictconfig import DictConfig


class ConfigStore:
    """Global registry for configuration schemas and defaults.
    
    The ConfigStore allows you to register configuration schemas (dataclasses)
    and default configurations that can be referenced by name.
    
    Examples:
        >>> from dataclasses import dataclass
        >>> from cobruh import ConfigStore
        >>>
        >>> @dataclass
        >>> class ModelConfig:
        ...     name: str = "resnet"
        ...     layers: int = 50
        >>>
        >>> cs = ConfigStore.instance()
        >>> cs.store(name="model_base", node=ModelConfig)
    """
    
    _instance: Optional["ConfigStore"] = None
    
    def __init__(self) -> None:
        """Initialize the config store."""
        self._configs: dict[str, dict[str, Any]] = {}
    
    @classmethod
    def instance(cls) -> "ConfigStore":
        """Get the singleton instance of the config store.
        
        Returns:
            The ConfigStore singleton instance
        """
        if cls._instance is None:
            cls._instance = ConfigStore()
        return cls._instance
    
    def store(
        self,
        name: str,
        node: Any,
        group: Optional[str] = None,
        package: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> None:
        """Store a configuration schema or instance.
        
        Args:
            name: Name to register the config under
            node: Config to store (dict, dataclass, or DictConfig)
            group: Optional group name (e.g., "model", "optimizer")
            package: Optional package path for the config
            provider: Optional provider name for tracking
        """
        # Initialize group if it doesn't exist
        if group is None:
            group = "_global_"
        
        if group not in self._configs:
            self._configs[group] = {}
        
        # Store the config with metadata
        entry = {
            "node": node,
            "package": package,
            "provider": provider or "user",
        }
        
        self._configs[group][name] = entry
    
    def get(
        self,
        name: str,
        group: Optional[str] = None,
    ) -> Optional[Any]:
        """Retrieve a stored configuration.
        
        Args:
            name: Name of the config to retrieve
            group: Optional group name
            
        Returns:
            The stored config or None if not found
        """
        if group is None:
            group = "_global_"
        
        if group not in self._configs:
            return None
        
        entry = self._configs[group].get(name)
        if entry is None:
            return None
        
        return entry["node"]
    
    def get_group(self, group: str) -> dict[str, Any]:
        """Get all configs in a group.
        
        Args:
            group: The group name
            
        Returns:
            Dictionary of config names to configs in the group
        """
        if group not in self._configs:
            return {}
        
        return {
            name: entry["node"]
            for name, entry in self._configs[group].items()
        }
    
    def list_groups(self) -> list[str]:
        """List all registered groups.
        
        Returns:
            List of group names
        """
        return [g for g in self._configs.keys() if g != "_global_"]
    
    def clear(self) -> None:
        """Clear all stored configurations."""
        self._configs.clear()
    
    def __repr__(self) -> str:
        """String representation of the config store.
        
        Returns:
            String representation
        """
        total = sum(len(configs) for configs in self._configs.values())
        groups = len(self._configs)
        return f"ConfigStore(groups={groups}, total_configs={total})"
