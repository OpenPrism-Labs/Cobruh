"""Global context management for Cobruh."""

from typing import Optional
from pathlib import Path
import inspect


class GlobalContext:
    """Global context for Cobruh configuration management.
    
    Manages global state like config search paths, job names, and other
    runtime configuration for Cobruh.
    """
    
    _instance: Optional["GlobalContext"] = None
    
    def __init__(self) -> None:
        """Initialize the global context."""
        self._config_search_path: Optional[Path] = None
        self._job_name: Optional[str] = None
        self._initialized: bool = False
    
    @classmethod
    def instance(cls) -> "GlobalContext":
        """Get the singleton instance of the global context.
        
        Returns:
            The GlobalContext singleton instance
        """
        if cls._instance is None:
            cls._instance = GlobalContext()
        return cls._instance
    
    def initialize(
        self,
        config_path: Optional[str] = None,
        job_name: Optional[str] = None,
        caller_stack_depth: int = 1,
    ) -> None:
        """Initialize the global context.
        
        Args:
            config_path: Path to the config directory
            job_name: Name for this job (affects output directory)
            caller_stack_depth: Stack depth for determining caller location
        """
        # Determine config path
        if config_path is not None:
            self._config_search_path = Path(config_path).resolve()
        else:
            # Try to find the caller's directory
            frame = inspect.currentframe()
            for _ in range(caller_stack_depth + 1):
                if frame is not None:
                    frame = frame.f_back
            
            if frame is not None:
                caller_file = frame.f_code.co_filename
                caller_dir = Path(caller_file).parent
                
                # Look for a 'configs' directory
                configs_dir = caller_dir / "configs"
                if configs_dir.exists():
                    self._config_search_path = configs_dir
                else:
                    self._config_search_path = caller_dir
            else:
                self._config_search_path = Path.cwd()
        
        self._job_name = job_name or "app"
        self._initialized = True
    
    @property
    def config_search_path(self) -> Optional[Path]:
        """Get the config search path.
        
        Returns:
            The config search path
        """
        return self._config_search_path
    
    @property
    def job_name(self) -> Optional[str]:
        """Get the job name.
        
        Returns:
            The job name
        """
        return self._job_name
    
    @property
    def is_initialized(self) -> bool:
        """Check if the context is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._initialized
    
    def clear(self) -> None:
        """Clear the global context."""
        self._config_search_path = None
        self._job_name = None
        self._initialized = False


def initialize(
    config_path: Optional[str] = None,
    job_name: Optional[str] = None,
    caller_stack_depth: int = 1,
) -> None:
    """Initialize Cobruh global context.
    
    Must be called before compose() in programmatic usage.
    Not needed when using @cobruh.main() decorator.
    
    Args:
        config_path: Search path for configs
        job_name: Name for this job (affects output directory)
        caller_stack_depth: Stack depth for determining caller location
        
    Example:
        >>> import cobruh
        >>> cobruh.initialize(config_path="configs")
        >>> cfg = cobruh.compose(config_name="config")
    """
    ctx = GlobalContext.instance()
    ctx.initialize(
        config_path=config_path,
        job_name=job_name,
        caller_stack_depth=caller_stack_depth + 1,
    )
