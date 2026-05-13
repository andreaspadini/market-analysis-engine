from __future__ import annotations

import json
from typing import Any, Dict


class ManifestJsonError(ValueError):
    """Raised when JSON encoding/decoding or canonical checks fail."""


def dumps_canonical_json(data: Dict[str, Any]) -> str:
    """
    Canonical JSON string (deterministic):
      - UTF-8 friendly (ensure_ascii=False)
      - sorted keys
      - no extra whitespace (separators=(",", ":"))
    """
    try:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except (TypeError, ValueError) as e:
        raise ManifestJsonError(f"Unable to serialize manifest to JSON: {e}") from e


def dump_manifest_json_bytes(data: Dict[str, Any]) -> bytes:
    """Canonical JSON bytes in UTF-8."""
    s = dumps_canonical_json(data)
    return s.encode("utf-8")


def load_manifest_json_bytes(payload: bytes) -> Dict[str, Any]:
    """Load JSON bytes (UTF-8) into a dict."""
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ManifestJsonError("manifest.json must be valid UTF-8.") from e

    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise ManifestJsonError(f"manifest.json is not valid JSON: {e}") from e

    if not isinstance(obj, dict):
        raise ManifestJsonError("manifest.json root must be a JSON object.")
    return obj


def assert_canonical_json_bytes(payload: bytes) -> None:
    """
    Enforce canonical JSON representation.
    If payload is not exactly the canonical encoding of its parsed content -> error.
    """
    obj = load_manifest_json_bytes(payload)
    canonical = dump_manifest_json_bytes(obj)
    if payload != canonical:
        raise ManifestJsonError("manifest.json is not in canonical form (deterministic encoding required).")
