# packages/orchestrator/src/api/http/dependencies.py
from __future__ import annotations
import hashlib
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
import importlib.metadata as _metadata
from ..mapper_v1 import _NodeLike
from ..api_impl_v1 import ApiImplV1, SchedulerPort, _dag_and_targets_from_config
from ..contracts.validate import validate_pipeline_parameters_v1
from ...config.config_fingerprint import compute_config_fingerprint as o2_compute_config_fingerprint
from ...artifacts.manifest_validator import validate_manifest as o1_validate_manifest
from ..contracts.root_run_parameters_v1 import RootRunParametersV1
from ..contracts.validate import validate_root_run_parameters_v1
from ..contracts.validate import validate_statistical_run_parameters_v1
from ..contracts.validate import validate_query_run_parameters_v1
from ..contracts.validate import validate_pattern_run_parameters_v1
from ..contracts.validate import PipelineParametersValidationError

from ...pipeline.planner import plan as build_execution_plan

from ...runtime.execution_state import ExecutionState
from ...runtime.execution_queue import ExecutionQueue
from ...runtime.runtime_trace import RuntimeTrace
from ...runtime.execution_scheduler import ExecutionScheduler
from ...runtime.execution_worker import ExecutionWorker
from ...runtime.retry_policy import RetryPolicy
from ...runtime.run_context import RunExecutionContext
from ...runtime.artifact_resolver import ArtifactResolver
from ...runtime.runtime_types import Status


from ...runtime.tool_registry import ToolRegistry
from ...adapters.storage.filesystem_store import FilesystemArtifactStore
from ...adapters.storage.ports import ArtifactStorePort

from ...adapters.core.execution_engine import ExecutionEngine, ExecutionItem
from ...adapters.core.core_adapter import CoreAdapter
from ...adapters.core.core_port import CorePort, CoreInvocation, CoreResult
from ...dataset.dataset_policy import validate_dataset_selection
from ...dataset.dataset_resolver import resolve_dataset
from ...dataset.dataset_schema import DatasetSelection
from ...dataset.input_view_builder import build_dataset_input_view
from ...artifacts.lineage_v1 import (
    build_query_from_statistical_lineage,
    build_root_standalone_lineage,
    build_statistical_from_root_lineage,
    canonicalize_lineage_v1,
)


logger = logging.getLogger(__name__)

def validate_root_runtime_config(cfg: dict) -> dict:
    model = validate_root_run_parameters_v1(cfg)

    dumped = model.model_dump(
        mode="python",
        by_alias=False,
        exclude_none=False,
    )

    return {
        "api_version": dumped["api_version"],
        "dataset": dumped["dataset"],
        "pipeline": {
            "id": "o7_root_pipeline_v1",
            "steps": [
                {
                    "step_id": "root",
                    "op": "root_engine",
                    "with": {},
                }
            ],
        },
        "parameters": {
            "root": dumped["config"],
        },
        "lineage": build_root_standalone_lineage(),
    }

def validate_statistical_runtime_config(cfg: dict) -> dict:
    model = validate_statistical_run_parameters_v1(cfg)

    dumped = model.model_dump(
        mode="python",
        by_alias=False,
        exclude_none=False,
    )

    return {
        "api_version": dumped["api_version"],
        "pipeline": {
            "id": "o7_statistical_from_artifact_v1",
            "steps": [
                {
                    "step_id": "stat",
                    "op": "statistical_engine",
                    "with": {
                        "root_artifact_ref": dumped["root_artifact_ref"],
                    },
                }
            ],
        },
        "parameters": {
            "statistical": dumped["config"],
        },
        "lineage": build_statistical_from_root_lineage(
            dumped["root_artifact_ref"]
        ),
    }

def validate_query_runtime_config(cfg: dict) -> dict:
    model = validate_query_run_parameters_v1(cfg)

    dumped = model.model_dump(
        mode="python",
        by_alias=False,
        exclude_none=False,
    )

    return {
        "api_version": dumped["api_version"],
        "pipeline": {
            "id": "o7_query_from_artifact_v1",
            "steps": [
                {
                    "step_id": "qry",
                    "op": "query_engine",
                    "with": {
                        "statistical_artifact_ref": dumped["statistical_artifact_ref"],
                        "query": dumped["query"],
                    },
                }
            ],
        },
        "parameters": {},
        "lineage": build_query_from_statistical_lineage(
            dumped["statistical_artifact_ref"]
        ),
    }

def validate_pattern_runtime_config(cfg: dict) -> dict:
    model = validate_pattern_run_parameters_v1(cfg)

    dumped = model.model_dump(
        mode="json",
        by_alias=False,
        exclude_none=False,
    )

    return {
        "api_version": dumped["api_version"],
        "dataset": dumped["dataset"],
        "pipeline": {
            "id": "o7_pattern_standalone_v1",
            "steps": [
                {
                    "step_id": "pattern",
                    "op": "pattern_engine",
                    "with": {},
                }
            ],
        },
        "parameters": {
            "pattern": dumped["config"],
        },
        "lineage": {},
    }

def validate_runtime_config(cfg: dict) -> dict:
    if "root_artifact_ref" in cfg or "statistical_artifact_ref" in cfg:
        raise PipelineParametersValidationError(
            "Stepwise payloads are not accepted by /runs; use /runs/statistical or /runs/query."
        )

    if "config" in cfg and "dataset" in cfg:
        raise PipelineParametersValidationError(
            "Stepwise root payloads are not accepted by /runs; use /runs/root."
        )

    model = validate_pipeline_parameters_v1(cfg)

    dumped = model.model_dump(
        mode="python",
        by_alias=False,
        exclude_none=False,
    )

    return {
        "api_version": dumped["api_version"],
        "dataset": dumped["dataset"],
        "pipeline": {
            "id": "o7_6_legacy_full_pipeline_v1",
            "steps": [
                {
                    "step_id": "root",
                    "op": "root_engine",
                    "with": {},
                },
                {
                    "step_id": "stat",
                    "op": "statistical_engine",
                    "needs": ["root"],
                    "with": {},
                },
                {
                    "step_id": "qry",
                    "op": "query_engine",
                    "needs": ["stat"],
                    "with": {
                        "query": dumped["engines"]["query"],
                    },
                },
            ],
        },
        "parameters": {
            "root": dumped["engines"]["root"],
            "statistical": dumped["engines"]["statistical"],
            "query": dumped["engines"]["query"],
        },
    }
def _build_artifact_store() -> ArtifactStorePort:
    return FilesystemArtifactStore(store_root=Path(".orchestrator").resolve())

def _canon_hash(obj: Any) -> str:
    """
    Deterministic canonical hash helper.
    """
    s = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _prepare_query_cli_inputs(
    *,
    base_tmp: Path,
    run_fp: str,
    node_id: str,
    original_inputs: dict[str, Any],
) -> dict[str, Any]:
    """
    Prepara i path richiesti da QueryCliAdapter in modo deterministico.
    """
    run_dir = (base_tmp / f"run_{run_fp}" / f"node_{node_id}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic file locations
    queryplan_path = (run_dir / "queryplan.json").resolve()
    spec_path = (run_dir / "spec.json").resolve()
    frozen_root = (run_dir / "frozen_root").resolve()
    frozen_root.mkdir(parents=True, exist_ok=True)

    # --- Ensure deterministic QueryPlan and Spec files ---

    # QueryPlan (minimal, but passes api_version check)
    if not queryplan_path.exists():
        qp_obj = {
            "api_version": "1.0.0",
            "intent": {
                "name": "spec_path",
                "spec": "specs/spec.json",
            },
            "query": original_inputs.get("query", ""),
        }
        queryplan_path.write_text(
            json.dumps(qp_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False),
            encoding="utf-8",
        )

    # Spec
    spec_obj = {
        "api_version": "1.0.0",
        "spec_version": "1.0",
        "name": "demo_df_master",
        "dataset": "df_master",
        "filters": [],
        "metrics": [],
        "groupby": [],
    }
    spec_path.write_text(
        json.dumps(spec_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )

    # Always return enriched inputs (not inside the if!)
    enriched = dict(original_inputs)
    enriched["queryplan_path"] = str(queryplan_path)
    enriched["spec_path"] = str(spec_path)
    enriched["frozen_root"] = str(frozen_root)
    return enriched

def _normalize_dataset_instruments(values: Any) -> tuple[str, ...]:
    """
    Minimal pre-policy normalization authorized for EDI-1:
    - trim whitespace
    - uppercase normalization

    Explicitly does NOT perform:
    - deduplication
    - sorting
    - dataset_id construction
    """
    normalized: list[str] = []

    for value in values or ():
        normalized.append(str(value).strip().upper())

    return tuple(normalized)

def _resolve_runtime_dataset(cfg: Mapping[str, Any]):
    """
    Runtime bridge:
    config.dataset -> DatasetSelection -> policy -> resolver.
    """
    raw_dataset = dict(cfg.get("dataset") or {})

    selection = DatasetSelection(
        instruments=_normalize_dataset_instruments(raw_dataset.get("instruments")),
        timeframe=str(raw_dataset.get("timeframe") or ""),
        start_date=str(raw_dataset.get("start_date") or ""),
        end_date=str(raw_dataset.get("end_date") or ""),
    )

    validate_dataset_selection(selection)
    return resolve_dataset(selection)


def _scheduler_factory(cfg: Mapping[str, Any], fp: str) -> SchedulerPort:
    # 1) runtime pieces
    state = ExecutionState()
    queue = ExecutionQueue()
    trace = RuntimeTrace.collecting()
    sched = ExecutionScheduler(state=state, queue=queue, trace=trace)

    # 2) DAG builder (real DAG model)
    dag, targets = _dag_and_targets_from_config(cfg)

    node_ids = list(dag.node_ids())  # deterministic sorted
    logger.debug(
        "dag.built fingerprint=%s dag.node_count=%s dag.node_ids=%s targets=%s",
        fp,
        len(node_ids),
        node_ids,
        list(targets),
    )

    dataset_resolved = None
    if "dataset" in cfg:
        dataset_resolved = _resolve_runtime_dataset(cfg)

    # 3) Cache evaluation (pre-runtime) — deterministic, explicit
    # For REA-1: no cache short-circuit -> all False
    cache_hits = {nid: False for nid in node_ids}
    hit_ids = [nid for nid in node_ids if cache_hits.get(nid, False)]

    # 4) Planner (O4A) — build ExecutionPlan reale
    plan = build_execution_plan(
        dag=dag,
        targets=targets,
        cache_hits=cache_hits,
        run_fingerprint=fp,
    )

    logger.debug(
        "planner.plan_built fingerprint=%s plan_id=%s dag.node_count=%s "
        "plan.ordered_count=%s plan.to_build_count=%s plan.cached_count=%s "
        "plan.ordered=%s plan.to_build=%s plan.cached=%s",
        fp,
        plan.plan_id,
        len(node_ids),
        len(plan.ordered),
        len(plan.to_build),
        len(plan.cached),
        list(plan.ordered),
        list(plan.to_build),
        list(plan.cached),
    )

    logger.debug(
        "cache.pre_runtime_evaluated fingerprint=%s cache_hits.total=%s cache_hits.node_ids=%s to_build.node_ids=%s",
        fp,
        len(hit_ids),
        hit_ids,
        list(plan.to_build),
    )

    raw_run_lineage = dict(cfg.get("lineage") or {})
    run_lineage = canonicalize_lineage_v1(raw_run_lineage) if raw_run_lineage else None

    # 5) Build ExecutionItems from cfg (1:1 con steps)
    steps = (cfg.get("pipeline") or {}).get("steps") or []
    items_by_node: dict[str, ExecutionItem] = {}
    for st in steps:
        node_id = str(st["step_id"])
        tool_id = str(st["op"])
        inputs = dict(st.get("with") or {})
        all_parameters = dict(cfg.get("parameters") or {})
        needs = [str(x) for x in (st.get("needs") or [])]

        if tool_id == "root_engine":
            parameters = dict(all_parameters.get("root") or {})
        elif tool_id == "statistical_engine":
            statistical_parameters = dict(all_parameters.get("statistical") or {})
            parameters = {"config": statistical_parameters}
        elif tool_id == "query_engine":
            parameters = dict(all_parameters.get("query") or {})
        elif tool_id == "pattern_engine":
            parameters = dict(all_parameters.get("pattern") or {})
        else:
            parameters = {}

        # Query CLI requires filesystem paths
        if tool_id == "query_cli":
            inputs = _prepare_query_cli_inputs(
                base_tmp=Path("tmp").resolve(),
                run_fp=fp,
                node_id=node_id,
                original_inputs=inputs,
            )

        if dataset_resolved is not None:
            dataset_input_view = build_dataset_input_view(
                tool_id=tool_id,
                dataset=dataset_resolved,
                inputs=inputs,
                parameters=parameters,
            )
            final_inputs = dataset_input_view.inputs
            final_parameters = dataset_input_view.parameters
        else:
            final_inputs = dict(inputs)
            final_parameters = dict(parameters)

        item_metadata: dict[str, Any] = {"needs": needs}
        if run_lineage is not None:
            item_metadata["lineage"] = run_lineage

        items_by_node[node_id] = ExecutionItem(
            node_id=node_id,
            tool_id=tool_id,
            inputs=final_inputs,
            parameters=final_parameters,
            resources=None,
            metadata=item_metadata,
        )


    # 6) Runtime wiring
    store = _build_artifact_store()
    engine_version="dev"
    ctx = RunExecutionContext(
        config_hash=fingerprint_runtime_config(cfg),
        engine_version=engine_version,
    )

    artifact_resolver = ArtifactResolver()
    last_fp: dict[str, str] = {}

    class _WorkerEngine:
        def execute(self, *, node_id: str, attempt: int, context: Optional[dict[str, Any]] = None) -> bool:
            item = items_by_node[node_id]

            resolved_item = artifact_resolver.resolve(
                item=item,
                state=state,
                store=store,
            )

            from ...adapters.core.execution_engine import _fingerprint_for_item

            fp2 = _fingerprint_for_item(item=resolved_item, ctx=ctx)
            last_fp["value"] = fp2

            core: CorePort = ToolRegistry.resolve(resolved_item.tool_id, tmp_root=Path("tmp").resolve())
            core_adapter = CoreAdapter(core=core, store=store, tool_version=engine_version)
            eng = ExecutionEngine(adapter=core_adapter)

            outcomes = eng.run_sequential([resolved_item], ctx=ctx)
            outcome = outcomes[node_id]

            meta = dict(state.get(node_id).meta or {})
            resolution_meta = dict(resolved_item.metadata or {}).get("artifact_resolution")
            if isinstance(resolution_meta, dict):
                meta["artifact_resolution"] = resolution_meta
                state.set_meta(node_id, meta)

            if outcome.was_cache_hit or outcome.core_result is not None:
                state.set_artifact_ref(
                    node_id,
                    tool_id=resolved_item.tool_id,
                    fingerprint=fp2,
                    status=Status.SUCCESS.value,
                )

            return True

    worker = ExecutionWorker(
        state=state,
        queue=queue,
        engine=_WorkerEngine(),
        retry_policy=RetryPolicy(),
        trace=trace,
        fail_fast=True,
        context={},
    )

    class _LiveScheduler(SchedulerPort):

        @property
        def fingerprint_override(self) -> Optional[str]:
            return last_fp.get("value")

        def start(self) -> None:
            # Scheduler
            sched.schedule(plan)
            # Worker (exec reale)
            worker.run()

        def get_nodes(self):
            # Adapt RuntimeRecord -> _NodeLike (what mapper expects)
            recs = sched.get_nodes()  # list[RuntimeRecord] in deterministic order
            out = []
            for r in recs:
                status = getattr(r, "status", None)
                s = getattr(status, "name", str(status)).upper()

                meta = getattr(r, "meta", None) or {}
                err = meta.get("error")

                out.append(
                    _NodeLike(
                        name=str(getattr(r, "node_id", "")),
                        status=status,
                        is_cached=(s == "SKIPPED"),
                        is_skipped=False,
                        error=err if isinstance(err, dict) else None,
                    )
                )
            return out

    return _LiveScheduler()


@lru_cache(maxsize=1)
def get_api_service(*, engine_version: str = "dev") -> ApiImplV1:
    store = _build_artifact_store()

 
    def _fp(cfg: Any) -> str:
        return fingerprint_runtime_config(cfg)

    def _validate_manifest(m: dict) -> None:
        o1_validate_manifest(m, strict=True)

    return ApiImplV1(
        validate_config=validate_runtime_config,
        fingerprint_config=fingerprint_runtime_config,
        scheduler_factory=_scheduler_factory,
        artifact_store=_build_artifact_store(),
        validate_manifest=o1_validate_manifest,
        engine_version=engine_version,
        producer_tool_id=None,
    )


def get_api_service_v1() -> ApiImplV1:
    return get_api_service(engine_version="dev")

from datetime import date, datetime

@lru_cache(maxsize=1)
def get_api_service_root(*, engine_version: str = "dev") -> ApiImplV1:
    return ApiImplV1(
        validate_config=validate_root_runtime_config,
        fingerprint_config=fingerprint_runtime_config,
        scheduler_factory=_scheduler_factory,
        artifact_store=_build_artifact_store(),
        validate_manifest=o1_validate_manifest,
        engine_version=engine_version,
        producer_tool_id="root_engine",
    )

def get_api_service_v1_root() -> ApiImplV1:
    return get_api_service_root(engine_version="dev")


@lru_cache(maxsize=1)
def get_api_service_statistical(*, engine_version: str = "dev") -> ApiImplV1:
    return ApiImplV1(
        validate_config=validate_statistical_runtime_config,
        fingerprint_config=fingerprint_runtime_config,
        scheduler_factory=_scheduler_factory,
        artifact_store=_build_artifact_store(),
        validate_manifest=o1_validate_manifest,
        engine_version=engine_version,
        producer_tool_id="statistical_engine",
    )

def get_api_service_v1_statistical() -> ApiImplV1:
    return get_api_service_statistical(engine_version="dev")


@lru_cache(maxsize=1)
def get_api_service_query(*, engine_version: str = "dev") -> ApiImplV1:
    return ApiImplV1(
        validate_config=validate_query_runtime_config,
        fingerprint_config=fingerprint_runtime_config,
        scheduler_factory=_scheduler_factory,
        artifact_store=_build_artifact_store(),
        validate_manifest=o1_validate_manifest,
        engine_version=engine_version,
        producer_tool_id="query_engine",
    )

def get_api_service_v1_query() -> ApiImplV1:
    return get_api_service_query(engine_version="dev")

@lru_cache(maxsize=1)
def get_api_service_pattern(*, engine_version: str = "dev") -> ApiImplV1:
    return ApiImplV1(
        validate_config=validate_pattern_runtime_config,
        fingerprint_config=fingerprint_runtime_config,
        scheduler_factory=_scheduler_factory,
        artifact_store=_build_artifact_store(),
        validate_manifest=o1_validate_manifest,
        engine_version=engine_version,
        producer_tool_id="pattern_engine",
    )

def get_api_service_v1_pattern() -> ApiImplV1:
    return get_api_service_pattern(engine_version="dev")

def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def fingerprint_runtime_config(cfg: dict) -> str:
    s = json.dumps(
        cfg,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=_json_default,
    )
    return hashlib.sha256(s.encode("utf-8")).hexdigest()