"""Utility for instantiating objects from configuration."""

from typing import Any, Optional
import importlib


def instantiate(config: Any, *args: Any, **kwargs: Any) -> Any:
    """Instantiate an object from a configuration.
    
    The config should have a '_target_' key specifying the class/function to instantiate.
    Additional keys in the config will be passed as keyword arguments.
    
    Args:
        config: Configuration dict/DictConfig with '_target_' key
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments (override config values)
        
    Returns:
        Instantiated object
        
    Example:
        >>> config = DictConfig({
        ...     "_target_": "collections.Counter",
        ...     "data": [1, 2, 2, 3]
        ... })
        >>> obj = instantiate(config)
        >>> print(obj)
        Counter({2: 2, 1: 1, 3: 1})
    """
    # Handle DictConfig
    if hasattr(config, "_content"):
        config_dict = config.to_dict()
    elif isinstance(config, dict):
        config_dict = config
    else:
        raise ValueError(f"Config must be a dict or DictConfig, got {type(config)}")
    
    # Get target
    target = config_dict.get("_target_")
    if target is None:
        raise ValueError("Config must have a '_target_' key")
    
    # Get the class/function
    obj_class = _get_class(target)
    
    # Prepare kwargs
    init_kwargs = {k: v for k, v in config_dict.items() if k != "_target_"}
    init_kwargs.update(kwargs)
    
    # Instantiate
    return obj_class(*args, **init_kwargs)


def _get_class(target: str) -> Any:
    """Get a class or function from a module path.
    
    Args:
        target: Fully qualified path like "module.submodule.ClassName"
        
    Returns:
        The class or function
    """
    parts = target.split(".")
    module_path = ".".join(parts[:-1])
    class_name = parts[-1]
    
    if not module_path:
        # Try to get from builtins
        import builtins
        return getattr(builtins, class_name)
    
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Cannot import {target}: {e}")
