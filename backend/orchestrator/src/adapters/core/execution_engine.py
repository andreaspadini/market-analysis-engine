from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional

from ...artifacts.identity import compute_o3_fingerprint
from ...dataset.dataset_resolver import resolve_dataset
from ...dataset.dataset_schema import DatasetSelection
from ...dataset.input_hash import compute_input_hash
from ...dataset.input_view_builder import build_dataset_input_view
from ...runtime.run_context import RunExecutionContext
from ...artifacts.input_hash import compute_input_hash as compute_legacy_input_hash

from .core_adapter import CoreAdapter
from .core_port import CoreInvocation, CorePort, CoreResult


def _fingerprint_for_item(*, item: "ExecutionItem", ctx: RunExecutionContext) -> str:
    """
    C3 identity derivation (artifact_identity_hash).

    EDI-1 runtime path:
      DatasetResolved
          -> DatasetInputView
          -> input_hash
          -> fingerprint

    Compatibility fallback:
      for legacy direct ExecutionItem callers that do not provide
      inputs["dataset"], preserve the pre-EDI inline hashing path.
    """
    raw_dataset = item.inputs.get("dataset")

    if isinstance(raw_dataset, Mapping):
        dataset_resolved = resolve_dataset(
            DatasetSelection(
                instruments=tuple(raw_dataset.get("instruments") or ()),
                timeframe=str(raw_dataset.get("timeframe") or ""),
                start_date=str(raw_dataset.get("start_date") or ""),
                end_date=str(raw_dataset.get("end_date") or ""),
            )
        )

        input_view = build_dataset_input_view(
            tool_id=item.tool_id,
            dataset=dataset_resolved,
            inputs=dict(item.inputs),
            parameters=dict(item.parameters),
        )

        input_hash = compute_input_hash(input_view)
    else:
        legacy_input_view: dict[str, Any] = {
            "tool_id": item.tool_id,
            "inputs": dict(item.inputs),
            "parameters": dict(item.parameters),
        }
        if item.resources is not None:
            legacy_input_view["resources"] = dict(item.resources)

        input_hash = compute_legacy_input_hash(input_view=legacy_input_view)

    return compute_o3_fingerprint(
        input_hash=input_hash,
        config_hash=ctx.config_hash,
        engine_version=ctx.engine_version,
    )

@dataclass(frozen=True, slots=True)
class ExecutionItem:
    node_id: str
    tool_id: str
    inputs: Mapping[str, Any]
    parameters: Mapping[str, Any]
    resources: Optional[Mapping[str, Any]] = None
    metadata: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True, slots=True)
class ExecutionOutcome:
    node_id: str
    was_cache_hit: bool
    core_result: Optional[CoreResult] = None


class ExecutionEngine:
    """
    Engine sequenziale.

    Compatibilità:
    - M1: ExecutionEngine(core)  -> invoca CorePort direttamente (senza store)
    - C4: ExecutionEngine(adapter=CoreAdapter) -> usa store + identity + O1 strict via adapter
    """

    def __init__(self, core: CorePort | None = None, *, adapter: CoreAdapter | None = None) -> None:
        if adapter is None and core is None:
            raise TypeError("ExecutionEngine requires either core or adapter")
        if adapter is not None and core is not None:
            raise TypeError("ExecutionEngine accepts either core or adapter, not both")

        self._core = core
        self._adapter = adapter

    def run_sequential(
        self,
        ordered_plan: Iterable[ExecutionItem],
        *,
        cache_hits: Optional[Mapping[str, bool]] = None,
        ctx: RunExecutionContext | None = None,
    ) -> Dict[str, ExecutionOutcome]:
        """
        Esegue in ordine.

        - Se costruito con core (M1): usa cache_hits se passato, e invoca core quando non-hit.
        - Se costruito con adapter (C4): richiede ctx e calcola fingerprint per item;
          delega a CoreAdapter.execute_node(...) che fa O3 exists/put e manifest strict.
        """
        outcomes: Dict[str, ExecutionOutcome] = {}

        # --- C4 path: adapter ---
        if self._adapter is not None:
            if ctx is None:
                raise TypeError("ctx is required when ExecutionEngine is constructed with adapter")

            for item in ordered_plan:
                if item.node_id in outcomes:
                    raise ValueError(f"Duplicate node_id in ordered_plan: {item.node_id}")

                fp = _fingerprint_for_item(item=item, ctx=ctx)

                was_hit, core_res = self._adapter.execute_node(
                    node_id=item.node_id,
                    fingerprint=fp,
                    tool_id=item.tool_id,
                    inputs=item.inputs,
                    parameters=item.parameters,
                    resources=item.resources,
                    metadata=item.metadata,
                )

                outcomes[item.node_id] = ExecutionOutcome(
                    node_id=item.node_id,
                    was_cache_hit=bool(was_hit),
                    core_result=core_res,
                )

            return outcomes

        # --- M1 path: core ---
        assert self._core is not None
        hits = cache_hits or {}

        for item in ordered_plan:
            if item.node_id in outcomes:
                raise ValueError(f"Duplicate node_id in ordered_plan: {item.node_id}")

            is_hit = bool(hits.get(item.node_id, False))
            if is_hit:
                outcomes[item.node_id] = ExecutionOutcome(
                    node_id=item.node_id,
                    was_cache_hit=True,
                    core_result=None,
                )
                continue

            invocation = CoreInvocation(
                tool_id=item.tool_id,
                inputs=item.inputs,
                parameters=item.parameters,
                resources=item.resources,
                metadata=item.metadata,
            )
            result = self._core.invoke(invocation)

            outcomes[item.node_id] = ExecutionOutcome(
                node_id=item.node_id,
                was_cache_hit=False,
                core_result=result,
            )

        return outcomes

