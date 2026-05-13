"""Configuration contract (O2).

This package provides:
- Structural validation for the run config (strict-by-default)
- Canonical JSON serialization primitives
- Deterministic config fingerprinting (sha256 of canonical JSON)
"""

from .config_validator import ConfigValidationError, validate_config
from .config_fingerprint import canonical_json_bytes, compute_config_fingerprint

__all__ = [
    "ConfigValidationError",
    "validate_config",
    "canonical_json_bytes",
    "compute_config_fingerprint",
]
