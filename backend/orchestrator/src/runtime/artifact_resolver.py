from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..adapters.core.execution_engine import ExecutionItem
from ..adapters.storage.ports import ArtifactStorePort
from ..adapters.storage.workspace_layout import WorkspaceLayout
from ..artifacts.manifest_validator import validate_manifest
from .execution_state import ExecutionState
from .runtime_types import Status

from ..artifacts.lineage_v1 import (
    build_query_from_statistical_lineage,
    build_statistical_from_root_lineage,
)


class ArtifactResolutionError(RuntimeError):
    """Raised when upstream artifact resolution fails deterministically."""


class ArtifactResolver:
    """
    O5.x / O7.2 Artifact Resolution Layer

    Supported bindings:
      - statistical_engine <- explicit root_artifact_ref
      - statistical_engine <- root_engine (legacy upstream needs)
      - query_engine <- statistical_engine

    Rules:
      - no fallback to dataset/direct source
      - deterministic fail-fast
      - no in-place mutation
    """

    def resolve(
        self,
        item: ExecutionItem,
        state: ExecutionState,
        store: ArtifactStorePort,
    ) -> ExecutionItem:
        if item.tool_id == "statistical_engine":
            return self._resolve_statistical(item=item, state=state, store=store)

        if item.tool_id == "query_engine":
            return self._resolve_query(item=item, state=state, store=store)

        return item

    def _resolve_statistical(
        self,
        *,
        item: ExecutionItem,
        state: ExecutionState,
        store: ArtifactStorePort,
    ) -> ExecutionItem:
        explicit_ref = self._read_explicit_artifact_ref(
            item=item,
            input_key="root_artifact_ref",
        )
        if explicit_ref is not None:
            root_ref = self._resolve_from_artifact_ref(
                artifact_ref=explicit_ref,
                expected_tool_id="root_engine",
            )
            return self._bind_root_artifact(
                item=item,
                store=store,
                root_ref=root_ref,
                source="explicit_ref",
            )

        needs = self._read_needs(item)
        if not needs:
            raise ArtifactResolutionError(
                f"statistical_engine node '{item.node_id}' requires either "
                f"inputs['root_artifact_ref'] or at least one upstream dependency"
            )

        root_ref = self._resolve_single_upstream_ref(
            needs=needs,
            state=state,
            expected_tool_id="root_engine",
        )
        return self._bind_root_artifact(
            item=item,
            store=store,
            root_ref=root_ref,
            source="upstream_needs",
        )

    def _bind_root_artifact(
        self,
        *,
        item: ExecutionItem,
        store: ArtifactStorePort,
        root_ref: dict[str, str],
        source: str,
    ) -> ExecutionItem:
        manifest_relpath = self._validate_manifest_and_find_output_relpath(
            store=store,
            tool_id=root_ref["tool_id"],
            fingerprint=root_ref["fingerprint"],
            expected_relpath="outputs/root_output_dataset.csv",
        )

        with store.open_output(
            tool_id=root_ref["tool_id"],
            fingerprint=root_ref["fingerprint"],
            relpath=manifest_relpath,
        ):
            pass

        artifact_dir = self._artifact_dir(
            store=store,
            tool_id=root_ref["tool_id"],
            fingerprint=root_ref["fingerprint"],
        )

        resolved_inputs = dict(item.inputs)
        resolved_inputs["root_artifact_path"] = str(artifact_dir)

        binding_meta = {
            "tool_id": root_ref["tool_id"],
            "fingerprint": root_ref["fingerprint"],
            "status": root_ref["status"],
            "relpath": manifest_relpath,
            "source": source,
        }
        if root_ref.get("node_id"):
            binding_meta["from_node"] = root_ref["node_id"]
        if root_ref.get("manifest_version"):
            binding_meta["manifest_version"] = root_ref["manifest_version"]
        if root_ref.get("producer_version"):
            binding_meta["producer_version"] = root_ref["producer_version"]

        resolution_meta = {
            "bindings": {
                "root_artifact_path": binding_meta,
            }
        }

        resolved_metadata = dict(item.metadata or {})
        resolved_metadata["artifact_resolution"] = resolution_meta
        resolved_metadata["lineage"] = build_statistical_from_root_lineage(
            {
                "tool_id": root_ref["tool_id"],
                "fingerprint": root_ref["fingerprint"],
                "manifest_version": root_ref.get("manifest_version") or None,
                "producer_version": root_ref.get("producer_version") or None,
            }
        )

        return replace(
            item,
            inputs=resolved_inputs,
            metadata=resolved_metadata,
        )

    def _resolve_query(
        self,
        *,
        item: ExecutionItem,
        state: ExecutionState,
        store: ArtifactStorePort,
    ) -> ExecutionItem:
        explicit_ref = self._read_explicit_artifact_ref(
            item=item,
            input_key="statistical_artifact_ref",
        )
        if explicit_ref is not None:
            statistical_ref = self._resolve_from_artifact_ref(
                artifact_ref=explicit_ref,
                expected_tool_id="statistical_engine",
            )
        else:
            needs = self._read_needs(item)
            if not needs:
                raise ArtifactResolutionError(
                    f"query_engine node '{item.node_id}' requires either "
                    f"inputs['statistical_artifact_ref'] or at least one upstream dependency"
                )

            statistical_ref = self._resolve_single_upstream_ref(
                needs=needs,
                state=state,
                expected_tool_id="statistical_engine",
            )

        manifest_relpath = self._validate_manifest_and_find_output_relpath(
            store=store,
            tool_id=statistical_ref["tool_id"],
            fingerprint=statistical_ref["fingerprint"],
            expected_relpath="outputs/statistical_dataset.parquet",
        )

        with store.open_output(
            tool_id=statistical_ref["tool_id"],
            fingerprint=statistical_ref["fingerprint"],
            relpath=manifest_relpath,
        ):
            pass

        artifact_dir = self._artifact_dir(
            store=store,
            tool_id=statistical_ref["tool_id"],
            fingerprint=statistical_ref["fingerprint"],
        )

        resolved_inputs = dict(item.inputs)
        resolved_inputs["statistical_artifact_path"] = str(artifact_dir)

        binding_meta = {
            "tool_id": statistical_ref["tool_id"],
            "fingerprint": statistical_ref["fingerprint"],
            "status": statistical_ref["status"],
            "relpath": manifest_relpath,
            "source": "explicit_ref" if explicit_ref is not None else "upstream_needs",
        }
        if statistical_ref.get("node_id"):
            binding_meta["from_node"] = statistical_ref["node_id"]
        if statistical_ref.get("manifest_version"):
            binding_meta["manifest_version"] = statistical_ref["manifest_version"]
        if statistical_ref.get("producer_version"):
            binding_meta["producer_version"] = statistical_ref["producer_version"]

        resolution_meta = {
            "bindings": {
                "statistical_artifact_path": binding_meta,
            }
        }

        resolved_metadata = dict(item.metadata or {})
        resolved_metadata["artifact_resolution"] = resolution_meta
        resolved_metadata["lineage"] = build_query_from_statistical_lineage(
            {
                "tool_id": statistical_ref["tool_id"],
                "fingerprint": statistical_ref["fingerprint"],
                "manifest_version": statistical_ref.get("manifest_version") or None,
                "producer_version": statistical_ref.get("producer_version") or None,
            }
        )

        return replace(
            item,
            inputs=resolved_inputs,
            metadata=resolved_metadata,
        )

    def _read_explicit_artifact_ref(
        self,
        *,
        item: ExecutionItem,
        input_key: str,
    ) -> dict[str, str] | None:
        raw = dict(item.inputs or {}).get(input_key)
        if raw is None:
            return None

        if not isinstance(raw, dict):
            raise ArtifactResolutionError(
                f"ExecutionItem.inputs['{input_key}'] must be a dict for node '{item.node_id}'"
            )

        out: dict[str, str] = {}
        for key in ("tool_id", "fingerprint", "manifest_version", "producer_version"):
            value = raw.get(key)
            if value is None:
                continue
            if not isinstance(value, str) or not value:
                raise ArtifactResolutionError(
                    f"ExecutionItem.inputs['{input_key}'].{key} must be a non-empty string "
                    f"for node '{item.node_id}'"
                )
            out[key] = value

        if "tool_id" not in out or "fingerprint" not in out:
            raise ArtifactResolutionError(
                f"ExecutionItem.inputs['{input_key}'] must contain tool_id and fingerprint "
                f"for node '{item.node_id}'"
            )

        return out

    def _read_needs(self, item: ExecutionItem) -> list[str]:
        metadata = dict(item.metadata or {})
        raw = metadata.get("needs")
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise ArtifactResolutionError(
                f"ExecutionItem.metadata['needs'] must be a list for node '{item.node_id}'"
            )
        out: list[str] = []
        for dep in raw:
            if not isinstance(dep, str) or not dep:
                raise ArtifactResolutionError(
                    f"ExecutionItem.metadata['needs'] contains invalid dependency for node '{item.node_id}'"
                )
            out.append(dep)
        return out

    def _resolve_from_artifact_ref(
        self,
        *,
        artifact_ref: dict[str, str],
        expected_tool_id: str,
    ) -> dict[str, str]:
        tool_id = artifact_ref.get("tool_id")
        fingerprint = artifact_ref.get("fingerprint")

        if tool_id != expected_tool_id:
            raise ArtifactResolutionError(
                f"ArtifactRef tool_id mismatch: expected {expected_tool_id}, got {tool_id}"
            )
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ArtifactResolutionError("ArtifactRef fingerprint is missing or invalid")

        return {
            "node_id": "",
            "tool_id": tool_id,
            "fingerprint": fingerprint,
            "status": Status.SUCCESS.value,
            "manifest_version": artifact_ref.get("manifest_version", ""),
            "producer_version": artifact_ref.get("producer_version", ""),
        }

    def _resolve_single_upstream_ref(
        self,
        *,
        needs: list[str],
        state: ExecutionState,
        expected_tool_id: str,
    ) -> dict[str, str]:
        matches: list[dict[str, str]] = []

        for dep_node_id in needs:
            rec = state.get(dep_node_id)
            meta = dict(rec.meta or {})
            artifact_ref = meta.get("artifact_ref")

            if not isinstance(artifact_ref, dict):
                continue

            tool_id = artifact_ref.get("tool_id")
            fingerprint = artifact_ref.get("fingerprint")
            status = artifact_ref.get("status")

            if not isinstance(tool_id, str) or not tool_id:
                raise ArtifactResolutionError(
                    f"Invalid artifact_ref.tool_id for upstream node '{dep_node_id}'"
                )
            if not isinstance(fingerprint, str) or not fingerprint:
                raise ArtifactResolutionError(
                    f"Invalid artifact_ref.fingerprint for upstream node '{dep_node_id}'"
                )
            if not isinstance(status, str) or not status:
                raise ArtifactResolutionError(
                    f"Invalid artifact_ref.status for upstream node '{dep_node_id}'"
                )

            if tool_id != expected_tool_id:
                continue

            if status != Status.SUCCESS.value:
                raise ArtifactResolutionError(
                    f"Upstream {expected_tool_id} node '{dep_node_id}' is not SUCCESS (status={status})"
                )

            matches.append(
                {
                    "node_id": dep_node_id,
                    "tool_id": tool_id,
                    "fingerprint": fingerprint,
                    "status": status,
                }
            )

        if not matches:
            raise ArtifactResolutionError(
                f"No SUCCESS {expected_tool_id} artifact_ref found in upstream dependencies"
            )
        if len(matches) != 1:
            raise ArtifactResolutionError(
                f"Expected exactly 1 {expected_tool_id} upstream artifact_ref, found {len(matches)}"
            )

        return matches[0]

    def _validate_manifest_and_find_output_relpath(
        self,
        *,
        store: ArtifactStorePort,
        tool_id: str,
        fingerprint: str,
        expected_relpath: str,
    ) -> str:
        try:
            manifest = store.get_manifest(tool_id=tool_id, fingerprint=fingerprint)
        except Exception as e:  # noqa: BLE001
            raise ArtifactResolutionError(
                f"Artifact not found for ref {tool_id}/{fingerprint}: {e}"
            ) from e

        if not isinstance(manifest, dict):
            raise ArtifactResolutionError("Upstream manifest is not a dict")

        try:
            validate_manifest(dict(manifest), strict=True)
        except Exception as e:  # noqa: BLE001
            raise ArtifactResolutionError(
                f"Upstream manifest for {tool_id}/{fingerprint} is not valid O1 strict: {e}"
            ) from e

        outputs = manifest.get("outputs")
        if not isinstance(outputs, list):
            raise ArtifactResolutionError("Upstream manifest.outputs must be a list")

        for item in outputs:
            if not isinstance(item, dict):
                continue
            relpath = item.get("relpath")
            if relpath == expected_relpath:
                return expected_relpath

        raise ArtifactResolutionError(
            f"Required upstream output not found in manifest: {expected_relpath}"
        )

    def _artifact_dir(
        self,
        *,
        store: ArtifactStorePort,
        tool_id: str,
        fingerprint: str,
    ) -> Path:
        store_root = getattr(store, "store_root", None)
        if store_root is None:
            store_root = Path(".orchestrator").resolve()

        layout = WorkspaceLayout(store_root=Path(store_root).resolve())
        return layout.artifact_dir(tool_id=tool_id, fingerprint=fingerprint).resolve()