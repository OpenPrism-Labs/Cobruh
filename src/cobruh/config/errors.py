"""Custom exceptions for Cobruh configuration management."""

from typing import Any, Optional


class CobruhException(Exception):
    """Base exception for all Cobruh errors."""

    pass


class ConfigCompositionError(CobruhException):
    """Raised when configuration composition fails."""

    pass


class ConfigAttributeError(CobruhException, AttributeError):
    """Raised when accessing a non-existent configuration attribute."""

    def __init__(self, key: str, parent_path: Optional[str] = None) -> None:
        """Initialize ConfigAttributeError.
        
        Args:
            key: The key that was not found
            parent_path: Path to the parent config where the key was accessed
        """
        self.key = key
        self.parent_path = parent_path
        
        if parent_path:
            msg = f"Key '{key}' not found in config at path '{parent_path}'"
        else:
            msg = f"Key '{key}' not found in config"
        
        super().__init__(msg)


class ConfigKeyError(CobruhException, KeyError):
    """Raised when accessing a non-existent configuration key."""

    def __init__(self, key: str, parent_path: Optional[str] = None) -> None:
        """Initialize ConfigKeyError.
        
        Args:
            key: The key that was not found
            parent_path: Path to the parent config where the key was accessed
        """
        self.key = key
        self.parent_path = parent_path
        
        if parent_path:
            msg = f"Key '{key}' not found in config at path '{parent_path}'"
        else:
            msg = f"Key '{key}' not found in config"
        
        super().__init__(msg)


class MissingMandatoryValue(CobruhException):
    """Raised when trying to access a mandatory value that is missing."""

    def __init__(self, key: str) -> None:
        """Initialize MissingMandatoryValue.
        
        Args:
            key: The key with the missing value
        """
        self.key = key
        super().__init__(f"Missing mandatory value for key: {key}")


class ValidationError(CobruhException):
    """Raised when configuration validation fails."""

    pass


class InterpolationResolutionError(CobruhException):
    """Raised when interpolation resolution fails."""

    def __init__(self, key: str, interpolation: str, reason: str) -> None:
        """Initialize InterpolationResolutionError.
        
        Args:
            key: The key with the interpolation
            interpolation: The interpolation expression
            reason: Why the interpolation failed
        """
        self.key = key
        self.interpolation = interpolation
        self.reason = reason
        super().__init__(
            f"Failed to resolve interpolation '{interpolation}' for key '{key}': {reason}"
        )


class CircularReferenceError(InterpolationResolutionError):
    """Raised when a circular reference is detected in interpolations."""

    def __init__(self, key: str, chain: list[str]) -> None:
        """Initialize CircularReferenceError.
        
        Args:
            key: The key where the circular reference was detected
            chain: The chain of keys showing the circular reference
        """
        self.chain = chain
        reason = f"Circular reference detected: {' -> '.join(chain)}"
        super().__init__(key, key, reason)


class ConfigTypeError(CobruhException, TypeError):
    """Raised when a configuration value has the wrong type."""

    def __init__(self, key: str, expected_type: type, actual_value: Any) -> None:
        """Initialize ConfigTypeError.
        
        Args:
            key: The key with the type error
            expected_type: The expected type
            actual_value: The actual value that was provided
        """
        self.key = key
        self.expected_type = expected_type
        self.actual_value = actual_value
        
        actual_type = type(actual_value).__name__
        expected_name = getattr(expected_type, "__name__", str(expected_type))
        
        super().__init__(
            f"Type mismatch for key '{key}': expected {expected_name}, "
            f"got {actual_type} (value: {actual_value!r})"
        )


class ReadOnlyConfigError(CobruhException):
    """Raised when trying to modify a read-only configuration."""

    def __init__(self, key: Optional[str] = None) -> None:
        """Initialize ReadOnlyConfigError.
        
        Args:
            key: The key that was attempted to be modified (if applicable)
        """
        self.key = key
        
        if key:
            msg = f"Cannot modify read-only configuration at key '{key}'"
        else:
            msg = "Cannot modify read-only configuration"
        
        super().__init__(msg)
