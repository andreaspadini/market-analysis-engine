"""O2 Config fingerprinting (M3).

Deterministic fingerprint based exclusively on the canonical JSON representation
of a validated O2 Config.

Frozen canonical JSON (config-spec.md):
- json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
- UTF-8 bytes

Algorithm: sha256 -> hex string.

The fingerprint includes the entire config content, including `metadata`.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .config_validator import validate_config


def canonical_json_bytes(config: Any, *, strict: bool = True, validate: bool = True) -> bytes:
    """Return canonical UTF-8 JSON bytes for the given config.

    Args:
        config: candidate config object
        strict: forwarded to validator (unknown fields rejected when True)
        validate: when True (default), validate config before canonicalization

    Returns:
        Canonical UTF-8 encoded JSON bytes.

    Notes:
        - Does not mutate the input.
        - Canonicalization is frozen: sort_keys + separators + allow_nan=False.
    """
    obj = config
    if validate:
        obj = validate_config(config, strict=strict)

    s = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return s.encode("utf-8")


def compute_config_fingerprint(config: Any, *, strict: bool = True, validate: bool = True) -> str:
    """Compute deterministic sha256 fingerprint of the canonical config JSON.

    Args:
        config: candidate config object
        strict: forwarded to validator (unknown fields rejected when True)
        validate: when True (default), validate config before fingerprinting

    Returns:
        64-char lowercase hex sha256 digest.
    """
    data = canonical_json_bytes(config, strict=strict, validate=validate)
    return hashlib.sha256(data).hexdigest()
