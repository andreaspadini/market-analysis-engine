from __future__ import annotations


class IntentLayerError(Exception):
    """Base exception for the intent layer."""
    pass


class IntentParseError(IntentLayerError):
    """Raised when an input intent cannot be parsed."""
    pass


class IntentValidationError(IntentLayerError):
    """Raised when a parsed intent is structurally invalid or unsupported."""
    pass


class IntentMappingError(IntentLayerError):
    """Raised when semantic mapping to canonical query fields fails."""
    pass


class QueryBuildError(IntentLayerError):
    """Raised when canonical query spec build fails."""
    pass