"""Main decorator for Cobruh applications."""

from typing import Any, Callable, Optional
import sys
from functools import wraps

from cobruh.config.dictconfig import DictConfig
from cobruh.core.global_context import GlobalContext
from cobruh.core.composer import compose


def main(
    config_path: Optional[str] = None,
    config_name: str = "config",
    version_base: Optional[str] = None,
) -> Callable[[Callable[[DictConfig], Any]], Callable[[], Any]]:
    """Decorator for main application entry point.
    
    Args:
        config_path: Path to config directory (absolute or relative to caller)
                    If None, looks for 'configs' directory next to script
        config_name: Name of the primary config file (without .yaml extension)
        version_base: Cobruh version for compatibility (e.g., "1.0")
        
    Returns:
        Decorator function that wraps the main application function
        
    Example:
        >>> @cobruh.main(config_path="configs", config_name="config")
        ... def my_app(cfg: DictConfig) -> None:
        ...     print(cfg.model.name)
        ...     model = cobruh.utils.instantiate(cfg.model)
    """
    
    def decorator(func: Callable[[DictConfig], Any]) -> Callable[[], Any]:
        """Inner decorator function.
        
        Args:
            func: The function to decorate
            
        Returns:
            Wrapped function
        """
        
        @wraps(func)
        def wrapper() -> Any:
            """Wrapper function that composes config and calls the decorated function.
            
            Returns:
                Return value of the decorated function
            """
            # Initialize global context
            ctx = GlobalContext.instance()
            ctx.initialize(config_path=config_path, caller_stack_depth=2)
            
            # Parse command-line arguments
            overrides = _parse_command_line()
            
            # Compose configuration
            cfg = compose(
                config_name=config_name,
                overrides=overrides,
            )
            
            # Call the decorated function
            return func(cfg)
        
        return wrapper
    
    return decorator


def _parse_command_line() -> list[str]:
    """Parse command-line arguments for overrides.
    
    Returns:
        List of override strings
    """
    overrides = []
    
    # Skip the script name (sys.argv[0])
    for arg in sys.argv[1:]:
        # Skip known flags that aren't overrides
        if arg.startswith("--help") or arg.startswith("-h"):
            continue
        
        # If it looks like an override (contains =), add it
        if "=" in arg:
            overrides.append(arg)
    
    return overrides
