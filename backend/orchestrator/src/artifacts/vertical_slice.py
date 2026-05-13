from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from ..adapters.storage.ports import ArtifactStorePort
from artifacts.identity import compute_o3_fingerprint
from artifacts.input_hash import compute_input_hash
from artifacts.materializer import (
    ArtifactMaterializer,
    MaterializeRequest,
    ProducedArtifact,
)
from ..config.config_fingerprint import compute_config_fingerprint
from ..config.config_validator import validate_config


@dataclass(frozen=True)
class VerticalSliceResult:
    tool_id: str
    fingerprint: str
    manifest: Mapping[str, Any]
    was_cache_hit: bool
    # audit/debug (NON entra nella key O3)
    input_hash: str
    config_hash: str
    engine_version: str


def materialize_single_output(
    *,
    store: ArtifactStorePort,
    tool_id: str,
    tool_version: str,
    engine_version: str,
    config: Mapping[str, Any],
    produced_bytes: bytes,
    inputs: Mapping[str, Any],
    parameters: Mapping[str, Any],
    resources: Optional[Mapping[str, Any]] = None,
) -> VerticalSliceResult:
    """
    C3 Vertical Slice harness (library-only).

    - tool_id: source of truth (callsite vicino al binding adapter)
    - config_hash: O2 compute_config_fingerprint(config) (audit/telemetria)
    - input_hash: sha256(canonical_json_bytes(input_view)) sui campi semantici
    - fingerprint(O3): artifact_identity_hash = sha256(input_hash + config_hash + engine_version)
    - materializzazione reale via ArtifactMaterializer -> O3.put_artifact (atomic/staging gestito da O3)
    """
    if not isinstance(produced_bytes, (bytes, bytearray, memoryview)):
        raise TypeError("produced_bytes must be bytes-like")
    if not isinstance(engine_version, str) or not engine_version.strip():
        raise TypeError("engine_version must be a non-empty str")

    # O2 strict validation (freeze)
    validated_cfg: Dict[str, Any] = validate_config(dict(config), strict=True)

    # O2 config_hash (audit)
    config_hash = compute_config_fingerprint(validated_cfg, strict=True, validate=False)

    # C3 input_view (solo campi semantici e deterministici)
    input_view: Dict[str, Any] = {
        "tool_id": tool_id,
        "inputs": dict(inputs),
        "parameters": dict(parameters),
    }
    if resources is not None:
        input_view["resources"] = dict(resources)

    input_hash = compute_input_hash(input_view=input_view)

    # O3 key component: fingerprint := artifact_identity_hash
    fingerprint = compute_o3_fingerprint(
        input_hash=input_hash,
        config_hash=config_hash,
        engine_version=engine_version,
    )

    produced = ProducedArtifact(bytes_payload=bytes(produced_bytes))

    mat = ArtifactMaterializer(store=store)
    res = mat.materialize(
        MaterializeRequest(
            tool_id=tool_id,
            fingerprint=fingerprint,
            tool_version=tool_version,
            produced=produced,
            payload=None,
            metadata=None,
        )
    )

    return VerticalSliceResult(
        tool_id=tool_id,
        fingerprint=fingerprint,
        manifest=res.manifest,
        was_cache_hit=res.was_cache_hit,
        input_hash=input_hash,
        config_hash=config_hash,
        engine_version=engine_version,
    )
