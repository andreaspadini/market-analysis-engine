from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple

from artifacts.manifest_validator import validate_manifest
from ..adapters.storage.ports import ArtifactPayload, ArtifactStorePort, Manifest, OutputItem

from .manifest_builder import O1Producer, build_o1_manifest_v1


@dataclass(frozen=True)
class ProducedArtifact:
    """
    C3 input: bytes deterministici prodotti dall'adapter (C2).
    Di default li materializziamo come singolo output JSON.
    """
    bytes_payload: bytes
    logical_name: str = "result"
    filename: str = "result.json"


@dataclass(frozen=True)
class _PayloadFromOutputs:
    items: tuple[OutputItem, ...]

    def iter_outputs(self) -> Iterable[OutputItem]:
        return iter(self.items)


@dataclass(frozen=True)
class MaterializeRequest:
    # Guardrail: tool_id SoT (arriva dal binding adapter / plan, non ricostruito)
    tool_id: str
    # O3 key component: fingerprint (== artifact_identity_hash)
    fingerprint: str

    # tool_version finisce nel manifest producer.tool_version (O1)
    tool_version: str

    # Una delle due modalità:
    # (A) payload già in forma ArtifactPayload (multi-output)
    payload: Optional[ArtifactPayload] = None
    # (B) bytes deterministici singolo output
    produced: Optional[ProducedArtifact] = None

    # opzionale: metadata passthrough (non entra nel manifest top-level se non previsto da O1)
    metadata: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class MaterializeResult:
    tool_id: str
    fingerprint: str
    manifest: Manifest
    was_cache_hit: bool


class ArtifactMaterializer:
    """
    C3 Materializer:
    - idempotenza via O3.exists(key)
    - costruzione manifest O1 v1.0 (strict)
    - validate_manifest(..., strict=True) come gate hard
    - put_artifact(...) via O3 (atomic/staging è responsabilità dello store)
    """

    def __init__(self, *, store: ArtifactStorePort) -> None:
        self._store = store

    def materialize(self, req: MaterializeRequest) -> MaterializeResult:
        # Cache check (Guardrail idempotenza)
        if self._store.exists(tool_id=req.tool_id, fingerprint=req.fingerprint):
            # Non tocchiamo store/manifest: no-op
            # (manifest potrà essere recuperato via get_manifest se serve)
            return MaterializeResult(
                tool_id=req.tool_id,
                fingerprint=req.fingerprint,
                manifest={},
                was_cache_hit=True,
            )

        payload, outputs_for_manifest = self._resolve_payload(req)

        # Build manifest O1 (strict-by-default)
        producer = O1Producer(tool_id=req.tool_id, tool_version=req.tool_version)
        manifest = build_o1_manifest_v1(producer=producer, outputs=outputs_for_manifest)

        # Gate hard prima dello store finale
        validate_manifest(dict(manifest), strict=True)

        # Materialize via O3
        self._store.put_artifact(
            tool_id=req.tool_id,
            fingerprint=req.fingerprint,
            payload=payload,
            manifest=manifest,
        )

        return MaterializeResult(
            tool_id=req.tool_id,
            fingerprint=req.fingerprint,
            manifest=manifest,
            was_cache_hit=False,
        )

    def _resolve_payload(self, req: MaterializeRequest) -> tuple[ArtifactPayload, list[OutputItem]]:
        """
        Ritorna (payload, outputs_for_manifest) coerenti con O1.
        """
        if req.payload is not None and req.produced is not None:
            raise ValueError("Provide either payload or produced, not both.")
        if req.payload is None and req.produced is None:
            raise ValueError("Provide payload or produced.")

        if req.payload is not None:
            # Multi-output: payload è già ArtifactPayload
            outputs = list(req.payload.iter_outputs())
            return req.payload, outputs

        produced = req.produced
        assert produced is not None
        if not isinstance(produced.bytes_payload, (bytes, bytearray, memoryview)):
            raise TypeError("ProducedArtifact.bytes_payload must be bytes-like")

        item = OutputItem(
            logical_name=produced.logical_name,
            filename=produced.filename,
            data=bytes(produced.bytes_payload),
        )
        payload = _PayloadFromOutputs(items=(item,))
        return payload, [item]
