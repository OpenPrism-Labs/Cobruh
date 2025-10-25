"""Configuration composition engine."""

from typing import Any, Optional
from pathlib import Path
import yaml

from omegaconf import OmegaConf

from cobruh.config.dictconfig import DictConfig
from cobruh.config.errors import ConfigCompositionError
from cobruh.core.global_context import GlobalContext
from cobruh.core.config_store import ConfigStore


def compose(
    config_name: Optional[str] = None,
    overrides: Optional[list[str]] = None,
    return_cobruh_config: bool = False,
) -> DictConfig:
    """Compose configuration programmatically.
    
    Args:
        config_name: Name of config to load (or None for empty config)
        overrides: List of override strings (e.g., ["model=resnet", "lr=0.01"])
        return_cobruh_config: Include Cobruh runtime config in result
        
    Returns:
        Composed DictConfig
        
    Example:
        >>> cfg = cobruh.compose(
        ...     config_name="config",
        ...     overrides=["model=resnet", "optimizer.lr=0.001"]
        ... )
    """
    if overrides is None:
        overrides = []
    
    # Get global context
    ctx = GlobalContext.instance()
    
    # Initialize context if not already done
    if not ctx.is_initialized:
        ctx.initialize(caller_stack_depth=2)
    
    # Start with empty config
    if config_name is None:
        base_config = OmegaConf.create({})
    else:
        # Load the primary config
        base_config = _load_config(config_name, ctx.config_search_path)
    
    # Process defaults list if present
    if "defaults" in base_config:
        base_config = _process_defaults(base_config, ctx.config_search_path)
    
    # Apply overrides
    if overrides:
        base_config = _apply_overrides(base_config, overrides)
    
    # Wrap in DictConfig
    result = DictConfig(base_config)
    
    return result


def _load_config(config_name: str, search_path: Optional[Path]) -> Any:
    """Load a configuration file.
    
    Args:
        config_name: Name of the config file (without .yaml extension)
        search_path: Path to search for the config
        
    Returns:
        Loaded config as OmegaConf DictConfig
        
    Raises:
        ConfigCompositionError: If the config file cannot be found or loaded
    """
    if search_path is None:
        search_path = Path.cwd()
    
    # Try with .yaml extension
    config_file = search_path / f"{config_name}.yaml"
    if not config_file.exists():
        # Try with .yml extension
        config_file = search_path / f"{config_name}.yml"
    
    if not config_file.exists():
        # Try to get from ConfigStore
        cs = ConfigStore.instance()
        stored_config = cs.get(config_name)
        if stored_config is not None:
            return OmegaConf.structured(stored_config)
        
        raise ConfigCompositionError(
            f"Config file not found: {config_name} in {search_path}"
        )
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if content is None:
                content = {}
            return OmegaConf.create(content)
    except Exception as e:
        raise ConfigCompositionError(
            f"Failed to load config from {config_file}: {e}"
        )


def _process_defaults(config: Any, search_path: Optional[Path]) -> Any:
    """Process the defaults list in a config.
    
    Args:
        config: The config with a defaults list
        search_path: Path to search for configs
        
    Returns:
        Config with defaults merged in
    """
    defaults = config.get("defaults", [])
    
    # Remove defaults from the base config
    result = OmegaConf.create(dict(config))
    if "defaults" in result:
        del result["defaults"]
    
    # Process each default
    for default in defaults:
        # Convert OmegaConf containers to plain Python types
        if OmegaConf.is_config(default):
            default = OmegaConf.to_container(default)
        
        if isinstance(default, str):
            # Simple string default like "model: resnet50"
            # This is a shorthand for {model: resnet50}
            if ":" in default:
                group, name = default.split(":", 1)
                group = group.strip()
                name = name.strip()
            else:
                # Just a config name
                group = None
                name = default
        elif isinstance(default, dict):
            # Dict format like {model: resnet50}
            if len(default) != 1:
                raise ConfigCompositionError(
                    f"Default entry must have exactly one key: {default}"
                )
            group, name = list(default.items())[0]
        else:
            raise ConfigCompositionError(
                f"Invalid default entry: {default}"
            )
        
        # Load the group config
        if group:
            group_str = str(group)  # Ensure group is a string
            name_str = str(name)  # Ensure name is a string
            group_path = search_path / group_str if search_path else Path(group_str)
            group_config = _load_config(name_str, group_path)
            
            # Nest the group config under the group name
            nested_config = OmegaConf.create({group_str: group_config})
            result = OmegaConf.merge(result, nested_config)
        else:
            name_str = str(name)
            group_config = _load_config(name_str, search_path)
            # Merge directly if no group
            result = OmegaConf.merge(result, group_config)
    
    return result


def _apply_overrides(config: Any, overrides: list[str]) -> Any:
    """Apply command-line style overrides to a config.
    
    Args:
        config: The base config
        overrides: List of override strings
        
    Returns:
        Config with overrides applied
    """
    result = config
    
    for override in overrides:
        # Parse override (simple implementation for now)
        if "=" not in override:
            raise ConfigCompositionError(
                f"Invalid override format: {override} (expected key=value)"
            )
        
        key, value = override.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        # Handle special prefixes
        if key.startswith("+"):
            # Add new key
            key = key[1:]
            mode = "add"
        elif key.startswith("~"):
            # Override or add
            key = key[1:]
            mode = "override_or_add"
        else:
            # Normal override
            mode = "override"
        
        # Convert value to appropriate type
        typed_value = _parse_value(value)
        
        # Apply the override using OmegaConf
        OmegaConf.update(result, key, typed_value, merge=False)
    
    return result


def _parse_value(value: str) -> Any:
    """Parse a string value to its appropriate type.
    
    Args:
        value: String value to parse
        
    Returns:
        Parsed value with appropriate type
    """
    # Handle special values
    if value.lower() == "null" or value.lower() == "none":
        return None
    elif value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    
    # Try to parse as number
    try:
        if "." in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass
    
    # Return as string
    return value
