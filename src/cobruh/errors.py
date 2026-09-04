"""Public Cobruh exception hierarchy."""


class CobruhError(Exception):
    """Base exception for all expected Cobruh failures."""


class ConfigError(CobruhError):
    """Configuration source, composition, or interpolation failure."""


class IntegrationError(CobruhError):
    """Optional experiment-tracker integration failure."""


class OverrideError(ConfigError):
    """Invalid or inapplicable configuration override."""


class TargetError(CobruhError):
    """Target resolution or construction failure."""
