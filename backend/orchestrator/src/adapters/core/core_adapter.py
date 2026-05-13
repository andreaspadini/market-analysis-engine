from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from ...artifacts.manifest_validator import validate_manifest
from ..storage.ports import ArtifactPayload, ArtifactStorePort, Manifest, OutputItem
from ...artifacts.lineage_v1 import canonicalize_lineage_v1

from .core_port import CoreInvocation, CorePort, CoreResult

@dataclass(frozen=True)
class _PayloadFromOutputs:
    items: tuple[OutputItem, ...]

    def iter_outputs(self) -> Iterable[OutputItem]:
        return iter(self.items)


def _canonical_json_bytes(obj: Any) -> bytes:
    # Deterministico: sort_keys + separators
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True, slots=True)
class StoredArtifactRef:
    """
    Data-only reference to a stored artifact.
    """
    node_id: str
    fingerprint: str


class CoreAdapter:
    """
    Wiring layer tra ExecutionEngine, Core e O3 ArtifactStorePort.

    Chiave store congelata: (tool_id, fingerprint).
    """

    def __init__(
        self,
        core: CorePort,
        store: ArtifactStorePort,
        *,
        tool_version: str = "0.0",
    ) -> None:
        self._core = core
        self._store = store
        self._tool_version = tool_version

    def execute_node(
        self,
        *,
        node_id: str,
        fingerprint: str,
        tool_id: str,
        inputs: Mapping[str, Any],
        parameters: Mapping[str, Any],
        resources: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> tuple[bool, CoreResult | None]:
        """
        Returns:
            (was_cache_hit, core_result_if_any)
        """

        # Cache check via O3 (key: tool_id+fingerprint)
        if self._store.exists(tool_id=tool_id, fingerprint=fingerprint):
            return True, None

        invocation = CoreInvocation(
            tool_id=tool_id,
            inputs=inputs,
            parameters=parameters,
            resources=resources,
            metadata=metadata,
        )
        result = self._core.invoke(invocation)

        # Payload handling: if Core already returns ArtifactPayload use it,
        # otherwise wrap into a single deterministic JSON output.
        payload_obj = result.payload
        if hasattr(payload_obj, "iter_outputs") and callable(getattr(payload_obj, "iter_outputs")):
            payload: ArtifactPayload = payload_obj  # type: ignore[assignment]
            outputs_for_manifest = list(payload.iter_outputs())
        else:
            data = _canonical_json_bytes(payload_obj)
            item = OutputItem(
                logical_name="result",
                filename="result.json",
                data=data,
            )
            payload = _PayloadFromOutputs(items=(item,))
            outputs_for_manifest = [item]

        # Build O1 manifest (strict-by-default schema)
        outputs_manifest = []
        for it in outputs_for_manifest:
            relpath = f"outputs/{it.filename}"
            outputs_manifest.append(
                {
                    "relpath": f"outputs/{it.filename}",
                    "bytes": int(len(it.data)),
                    "checksum": {"alg": "sha256", "value": _sha256_hex(it.data)},
                }
            )

        manifest: Manifest = {
            "manifest_version": "1.0",
            "producer": {"tool_id": tool_id, "tool_version": self._tool_version},
            "outputs": outputs_manifest,
        }

        lineage = None
        if isinstance(metadata, Mapping):
            raw_lineage = metadata.get("lineage")
            if isinstance(raw_lineage, Mapping):
                lineage = canonicalize_lineage_v1(raw_lineage)

        if lineage is not None:
            manifest["lineage"] = lineage

        # Validate before storing (keeps O1 contract tight)
        validate_manifest(dict(manifest), strict=True)

        # Materialize via O3
        self._store.put_artifact(
            tool_id=tool_id,
            fingerprint=fingerprint,
            payload=payload,
            manifest=manifest,
        )

        return False, result

