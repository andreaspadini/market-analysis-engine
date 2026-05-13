import hashlib
import json

from .dataset_schema import DatasetInputView


def _to_input_hash_payload(input_view: DatasetInputView) -> dict[str, object]:
    """
    Project DatasetInputView into the minimal JSON-ready structure used
    for deterministic hashing.

    D4 does not re-canonicalize values. It only materializes the DTO into
    the canonical top-level payload expected by the hashing formula.
    """
    return {
        "tool_id": input_view.tool_id,
        "inputs": input_view.inputs,
        "parameters": input_view.parameters,
    }


def _to_canonical_json(payload: dict[str, object]) -> str:
    """
    Serialize payload to canonical JSON for deterministic hashing.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_input_hash(input_view: DatasetInputView) -> str:
    """
    Compute the deterministic input hash for a DatasetInputView.

    Formula:
        input_hash = sha256(canonical_json(DatasetInputView))
    """
    canonical_json = _to_canonical_json(_to_input_hash_payload(input_view))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()