from __future__ import annotations

from typing import Any, Mapping


_ALLOWED_DERIVATION_TYPES = {
    "root_standalone",
    "statistical_from_root_artifact",
    "query_from_statistical_artifact",
}


def canonicalize_artifact_ref_v1(ref: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(ref, Mapping):
        raise ValueError("ArtifactRefV1 must be a mapping.")

    tool_id = ref.get("tool_id")
    fingerprint = ref.get("fingerprint")
    manifest_version = ref.get("manifest_version", None)
    producer_version = ref.get("producer_version", None)

    if not isinstance(tool_id, str) or not tool_id.strip():
        raise ValueError("ArtifactRefV1.tool_id must be a non-empty string.")
    if not isinstance(fingerprint, str) or not fingerprint.strip():
        raise ValueError("ArtifactRefV1.fingerprint must be a non-empty string.")

    if manifest_version is not None and (not isinstance(manifest_version, str) or not manifest_version.strip()):
        raise ValueError("ArtifactRefV1.manifest_version must be a non-empty string or None.")
    if producer_version is not None and (not isinstance(producer_version, str) or not producer_version.strip()):
        raise ValueError("ArtifactRefV1.producer_version must be a non-empty string or None.")

    return {
        "tool_id": tool_id,
        "fingerprint": fingerprint,
        "manifest_version": manifest_version,
        "producer_version": producer_version,
    }


def _parent_sort_key(ref: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(ref.get("tool_id") or ""),
        str(ref.get("fingerprint") or ""),
        str(ref.get("manifest_version") or ""),
        str(ref.get("producer_version") or ""),
    )


def canonicalize_lineage_v1(obj: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(obj, Mapping):
        raise ValueError("LineageV1 must be a mapping.")

    derivation_type = obj.get("derivation_type")
    parent_artifacts_raw = obj.get("parent_artifacts")

    if not isinstance(derivation_type, str) or not derivation_type.strip():
        raise ValueError("LineageV1.derivation_type must be a non-empty string.")
    if derivation_type not in _ALLOWED_DERIVATION_TYPES:
        raise ValueError(f"Unsupported LineageV1.derivation_type: {derivation_type}")
    if not isinstance(parent_artifacts_raw, list):
        raise ValueError("LineageV1.parent_artifacts must be a list.")

    parents = [canonicalize_artifact_ref_v1(item) for item in parent_artifacts_raw]
    parents.sort(key=_parent_sort_key)

    return {
        "derivation_type": derivation_type,
        "parent_artifacts": parents,
    }


def validate_lineage_v1(obj: Mapping[str, Any]) -> None:
    canonicalize_lineage_v1(obj)


def build_root_standalone_lineage() -> dict[str, Any]:
    return {
        "derivation_type": "root_standalone",
        "parent_artifacts": [],
    }


def build_statistical_from_root_lineage(root_ref: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "derivation_type": "statistical_from_root_artifact",
        "parent_artifacts": [
            canonicalize_artifact_ref_v1(root_ref),
        ],
    }


def build_query_from_statistical_lineage(statistical_ref: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "derivation_type": "query_from_statistical_artifact",
        "parent_artifacts": [
            canonicalize_artifact_ref_v1(statistical_ref),
        ],
    }