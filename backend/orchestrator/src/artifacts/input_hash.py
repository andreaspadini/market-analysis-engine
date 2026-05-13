from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def canonical_json_bytes(obj: Any) -> bytes:
    """
    Deterministic canonical JSON bytes:
      - sort_keys=True
      - separators without spaces
      - ensure_ascii=False
    """
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def compute_input_hash(*, input_view: Mapping[str, Any]) -> str:
    """
    C3 input_hash: sha256(canonical_json_bytes(input_view))

    Guardrail:
      - hash is computed ONLY on final UTF-8 bytes, never on raw Python objects.
      - input_view must be JSON-serializable (strict JSON domain recommended).
    """
    if not isinstance(input_view, Mapping):
        raise TypeError("input_view must be a Mapping[str, Any]")
    raw = canonical_json_bytes(dict(input_view))
    return hashlib.sha256(raw).hexdigest()

def compute_input_hash_from_view(input_view: Mapping[str, Any]) -> str:
    """
    Alias stabile per C3 vertical slice.
    """
    return compute_input_hash(input_view=input_view)

