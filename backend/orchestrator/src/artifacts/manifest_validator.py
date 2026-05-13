from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set
from ..artifacts.lineage_v1 import validate_lineage_v1


_MANIFEST_VERSION_RE = re.compile(r"^\d+\.\d+$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


class ManifestValidationError(ValueError):
    """Raised when a manifest does not conform to Artifact Manifest Spec v1.*."""


def validate_manifest(data: dict, strict: bool = True) -> None:
    """
    Validate Artifact Manifest Spec v1.*.

    Rules:
      - Pure function: does not mutate input
      - Raises ManifestValidationError on any validation failure
      - Returns None on success

    Strict mode:
      - strict=True (default): unknown fields => error
      - strict=False: unknown fields allowed (forward-compatibility within 1.x)
    """
    if not isinstance(data, dict):
        raise ManifestValidationError("Manifest must be a dict.")

    _validate_root(data, strict=strict)


def _validate_root(m: Mapping[str, Any], strict: bool) -> None:
    required = {"manifest_version", "producer", "outputs"}
    allowed = set(required) | {"lineage"}

    _require_keys(m, required, where="root")
    _check_unknown_keys(m, allowed, strict=strict, where="root")

    mv = m.get("manifest_version")
    _validate_manifest_version(mv)

    producer = m.get("producer")
    _validate_producer(producer, strict=strict)

    outputs = m.get("outputs")
    _validate_outputs(outputs, strict=strict)

    if "lineage" in m:
        _validate_lineage(m.get("lineage"), strict=strict)


def _validate_manifest_version(value: Any) -> None:
    if not isinstance(value, str):
        raise ManifestValidationError("manifest_version must be a string.")
    if not _MANIFEST_VERSION_RE.match(value):
        raise ManifestValidationError("manifest_version must match ^\\d+\\.\\d+$ (e.g. '1.0').")

    major_str, _minor_str = value.split(".", 1)
    try:
        major = int(major_str)
    except ValueError:
        raise ManifestValidationError("manifest_version major must be an integer.") from None

    if major != 1:
        raise ManifestValidationError("Unsupported manifest_version major. Only 1.* is accepted.")


def _validate_producer(value: Any, strict: bool) -> None:
    if not isinstance(value, dict):
        raise ManifestValidationError("producer must be an object/dict.")

    required = {"tool_id", "tool_version"}
    allowed = set(required)

    _require_keys(value, required, where="producer")
    _check_unknown_keys(value, allowed, strict=strict, where="producer")

    tool_id = value.get("tool_id")
    tool_version = value.get("tool_version")

    if not isinstance(tool_id, str) or not tool_id.strip():
        raise ManifestValidationError("producer.tool_id must be a non-empty string.")
    if not isinstance(tool_version, str) or not tool_version.strip():
        raise ManifestValidationError("producer.tool_version must be a non-empty string.")

    # NOTE (spec M1): tool_id semantics = stable identifier.
    # Validator does not enforce a specific syntax (kebab-case/dotted namespace)
    # to avoid unnecessarily tightening v1 beyond structural constraints.


def _validate_outputs(value: Any, strict: bool) -> None:
    if not isinstance(value, list):
        raise ManifestValidationError("outputs must be a list.")
    if len(value) == 0:
        raise ManifestValidationError("outputs must be a non-empty list.")

    seen_relpaths: Set[str] = set()

    for i, item in enumerate(value):
        if not isinstance(item, dict):
            raise ManifestValidationError(f"outputs[{i}] must be an object/dict.")

        required = {"relpath", "bytes", "checksum"}
        allowed = set(required)

        _require_keys(item, required, where=f"outputs[{i}]")
        _check_unknown_keys(item, allowed, strict=strict, where=f"outputs[{i}]")

        relpath = item.get("relpath")
        _validate_relpath(relpath, where=f"outputs[{i}].relpath")

        if relpath in seen_relpaths:
            raise ManifestValidationError(f"Duplicate relpath in outputs: '{relpath}'.")
        seen_relpaths.add(relpath)

        bytes_val = item.get("bytes")
        _validate_bytes(bytes_val, where=f"outputs[{i}].bytes")

        checksum = item.get("checksum")
        _validate_checksum(checksum, strict=strict, where=f"outputs[{i}].checksum")

def _validate_lineage(value: Any, strict: bool) -> None:
    if not isinstance(value, dict):
        raise ManifestValidationError("lineage must be an object/dict.")

    required = {"derivation_type", "parent_artifacts"}
    allowed = set(required)

    _require_keys(value, required, where="lineage")
    _check_unknown_keys(value, allowed, strict=strict, where="lineage")

    try:
        validate_lineage_v1(value)
    except Exception as e:
        raise ManifestValidationError(f"Invalid lineage: {e}") from e


def _validate_relpath(value: Any, where: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ManifestValidationError(f"{where} must be a non-empty string.")

    p = value

    # Absolute paths (POSIX) are forbidden.
    if p.startswith("/"):
        raise ManifestValidationError(f"{where} must be relative (no leading '/').")

    # Backslashes are forbidden to avoid Windows-path ambiguity and mixed separators.
    if "\\" in p:
        raise ManifestValidationError(f"{where} must use forward slashes only ('/'); backslashes are forbidden.")

    # Windows drive paths are forbidden (e.g. C: or D:).
    if _WINDOWS_DRIVE_RE.match(p):
        raise ManifestValidationError(f"{where} must not be a Windows drive path (e.g. 'C:...').")

    # No empty segments => prevents //, leading/trailing slash.
    segments = p.split("/")
    if any(seg == "" for seg in segments):
        raise ManifestValidationError(f"{where} must not contain empty path segments (no '//' or trailing '/').")

    # No traversal.
    if any(seg == ".." for seg in segments):
        raise ManifestValidationError(f"{where} must not contain '..' (path traversal forbidden).")


def _validate_bytes(value: Any, where: str) -> None:
    if not isinstance(value, int):
        raise ManifestValidationError(f"{where} must be an integer.")
    if value < 0:
        raise ManifestValidationError(f"{where} must be >= 0.")


def _validate_checksum(value: Any, strict: bool, where: str) -> None:
    if not isinstance(value, dict):
        raise ManifestValidationError(f"{where} must be an object/dict.")

    required = {"alg", "value"}
    allowed = set(required)

    _require_keys(value, required, where=where)
    _check_unknown_keys(value, allowed, strict=strict, where=where)

    alg = value.get("alg")
    cval = value.get("value")

    if not isinstance(alg, str) or not alg.strip():
        raise ManifestValidationError(f"{where}.alg must be a non-empty string.")
    if alg != "sha256":
        raise ManifestValidationError(f"{where}.alg must be 'sha256' in v1.")

    if not isinstance(cval, str) or not cval.strip():
        raise ManifestValidationError(f"{where}.value must be a non-empty string.")


def _require_keys(obj: Mapping[str, Any], keys: Set[str], where: str) -> None:
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ManifestValidationError(f"Missing required field(s) at {where}: {', '.join(missing)}.")


def _check_unknown_keys(obj: Mapping[str, Any], allowed: Set[str], strict: bool, where: str) -> None:
    if not strict:
        return
    unknown = [k for k in obj.keys() if k not in allowed]
    if unknown:
        raise ManifestValidationError(f"Unknown field(s) at {where} (strict=True): {', '.join(unknown)}.")
