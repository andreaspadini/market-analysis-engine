from __future__ import annotations
from ..runtime.execution_scheduler import ExecutionPlanLike, ExecutionScheduler
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, BinaryIO, Callable, Dict, List, Mapping, Optional, Protocol, Sequence, Set, Tuple

from .dto_v1 import (
    DtoValidationError,
    ManifestGetResponse,
    NodeSummaryV1,
    QueryRunSubmitRequest,
    RootRunSubmitRequest,
    StatisticalRunSubmitRequest,
    PatternRunSubmitRequest,
    RunGetResponse,
    RunNodesResponse,
    RunSubmitRequest,
    RunSubmitResponse,
)
from .errors_v1 import (
    ErrorEnvelopeV1,
    invalid_config,
    invalid_intent,
    invalid_request,
    not_found,
)
from .mapper_v1 import _NodeLike, map_nodes, map_run_status, summarize
from .contracts.validate import PublicIntentValidationError
from .contracts.artifact_ref_v1 import ArtifactRefV1
from ..adapters.storage.filesystem_store import ArtifactNotFoundError

# O2
from ..config.config_validator import validate_config as o2_validate_config
from ..config.config_fingerprint import compute_config_fingerprint as o2_compute_config_fingerprint

# O1
from ..artifacts.manifest_validator import validate_manifest as o1_validate_manifest
from ..artifacts.lineage_v1 import canonicalize_lineage_v1

# O3
from ..adapters.storage.ports import ArtifactStorePort as O3ArtifactStorePort, Manifest as O3Manifest

# O5
from ..runtime.execution_scheduler import ExecutionScheduler
from ..runtime.execution_state import ExecutionState
from ..runtime.execution_queue import ExecutionQueue
from ..runtime.runtime_trace import RuntimeTrace

# C3
from ..artifacts.identity import compute_o3_fingerprint

from ..pipeline.planner import plan as build_execution_plan
from ..pipeline.dag_model import DAGModel, Node



# -------------------------
# Scheduler adapter (O5 -> O6 mapper input)
# -------------------------


class SchedulerPort(Protocol):
    def start(self) -> None: ...
    def get_nodes(self) -> List[_NodeLike]: ...


# api/api_impl_v1.py (o dove hai ExecutionSchedulerAdapter)

class ExecutionSchedulerAdapter(SchedulerPort):
    def __init__(self, scheduler: ExecutionScheduler, *, plan: Optional[ExecutionPlanLike] = None) -> None:
        self._scheduler = scheduler
        self._plan = plan

    def start(self) -> None:
        s = self._scheduler

        # 0) Se lo scheduler espone giÃ  nodi, non rischedulare (idempotente).
        if hasattr(s, "get_nodes") and callable(getattr(s, "get_nodes")):
            try:
                existing = list(getattr(s, "get_nodes")())
                if existing:
                    return
            except Exception:
                # Se introspezione fallisce, continuiamo comunque con scheduling.
                pass

        # 1) Se esiste schedule(plan), Ã¨ il path corretto per O5A
        if hasattr(s, "schedule") and callable(getattr(s, "schedule")):
            if self._plan is None:
                raise RuntimeError("ExecutionSchedulerAdapter.start(): schedule() requires a plan but plan is None")
            s.schedule(self._plan)
            return

        # 2) fallback: start() (solo se schedule non esiste)
        if hasattr(s, "start") and callable(getattr(s, "start")):
            s.start()
            return

        raise RuntimeError("Scheduler implementation does not expose schedule() or start()")
  
    def get_nodes(self) -> List[_NodeLike]:
        s = self._scheduler

        candidates: list[Any] = []

        if hasattr(s, "get_nodes") and callable(getattr(s, "get_nodes")):
            candidates = list(getattr(s, "get_nodes")())
        elif hasattr(s, "nodes"):
            candidates = list(getattr(s, "nodes"))
        elif hasattr(s, "state") and hasattr(getattr(s, "state"), "all_records"):
            recs = getattr(getattr(s, "state"), "all_records")()
            candidates = [recs[nid] for nid in sorted(recs.keys())]
        elif hasattr(s, "state") and hasattr(getattr(s, "state"), "nodes"):
            candidates = list(getattr(getattr(s, "state"), "nodes"))
        elif hasattr(s, "execution_state") and hasattr(getattr(s, "execution_state"), "nodes"):
            candidates = list(getattr(getattr(s, "execution_state"), "nodes"))
        else:
            # DEV fallback: runtime scheduler does not expose nodes; return empty deterministic view
            return []
        out: List[_NodeLike] = []
        for i, n in enumerate(candidates):
            name = getattr(n, "name", None) or getattr(n, "tool_id", None) or f"node[{i}]"
            status = getattr(n, "status", None)
            is_cached = bool(getattr(n, "is_cached", False) or getattr(n, "cached", False))
            is_skipped = bool(getattr(n, "is_skipped", False) or getattr(n, "skipped", False))
            err = getattr(n, "error", None)
            if err is not None and not isinstance(err, dict):
                err = {"message": str(err)}
            out.append(_NodeLike(name=str(name), status=status, is_cached=is_cached, is_skipped=is_skipped, error=err))
        return out


# -------------------------
# Run registry (in-process)
# -------------------------


@dataclass
class _RunContext:
    fingerprint: str
    scheduler: SchedulerPort
    lineage: Dict[str, Any]


# -------------------------
# Public error wrapper (O6)
# -------------------------


class ApiErrorV1(RuntimeError):
    def __init__(self, envelope: ErrorEnvelopeV1) -> None:
        super().__init__(envelope.message)
        self.envelope = envelope


# -------------------------
# API Impl v1
# -------------------------
@dataclass(frozen=True)
class _DevSingleNodePlan:
    _node_id: str

    @property
    def to_build(self) -> Sequence[str]:
        return (self._node_id,)

    @property
    def cached(self) -> Set[str]:
        return set()

class ApiImplV1:
    """
    Concrete O6 API implementation.

    - in-process run registry only (freeze M1)
    - validates + fingerprints config via O2 (freeze M1)
    - manifest lookup via O3 (store) + O1 (validator) (freeze M1)
    """

    def __init__(
        self,
        *,
        # injected for testability, defaulted to real O2/O5/O3/O1 in factory below
        validate_config: Callable[[Any], Dict[str, Any]],
        fingerprint_config: Callable[[Any], Dict[str, Any]],
        scheduler_factory: Callable[[Mapping[str, Any], str], SchedulerPort],
        artifact_store: O3ArtifactStorePort,
        validate_manifest: Callable[[dict], None],
        engine_version: str,  # C3: must come from execution context (no hardcode here)
        producer_tool_id: Optional[str] = None,
    ) -> None:
        self._validate_config = validate_config
        self._fingerprint_config = fingerprint_config
        self._scheduler_factory = scheduler_factory
        self._artifact_store = artifact_store
        self._validate_manifest = validate_manifest
        self._engine_version = engine_version
        self._producer_tool_id = producer_tool_id

        self._runs: Dict[str, _RunContext] = {}

    # ------------- helpers -------------

    @staticmethod
    def _ensure_version_1x(api_version: str) -> None:
        # Keep local + strict
        parts = api_version.split(".")
        if len(parts) != 2:
            raise DtoValidationError("api_version must be in 'major.minor' format, e.g. '1.0'")
        try:
            major = int(parts[0])
            minor = int(parts[1])
        except ValueError as e:
            raise DtoValidationError("api_version major/minor must be integers") from e
        if major != 1 or minor < 0:
            raise DtoValidationError("Only api_version 1.* is supported")

    @staticmethod
    def _canonical_json_bytes(obj: Any) -> bytes:
        s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return s.encode("utf-8")

    @staticmethod
    def _sha256_hex(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _compute_input_hash(self, request: RunSubmitRequest) -> str:
        """
        C3 input_hash: sha256(canonical_json_bytes(input_view))

        Con il DTO attuale, l'unico input disponibile nel request Ã¨ `config`.
        Quindi: input_hash = sha256(canonical_json_bytes(request.config)).
        """
        raw = self._canonical_json_bytes(request.config)
        return self._sha256_hex(raw)

    # ------------- API -------------
    def submit_root_run(self, request: RootRunSubmitRequest) -> RunSubmitResponse:
        self._ensure_version_1x(request.api_version)

        legacy_request = RunSubmitRequest(
            api_version=request.api_version,
            config={
                "api_version": request.api_version,
                "dataset": request.dataset,
                "config": request.config,
            },
        )

        return self.submit_run(legacy_request)
    
    def submit_statistical_run(self, request: StatisticalRunSubmitRequest) -> RunSubmitResponse:
        self._ensure_version_1x(request.api_version)

        root_artifact_ref = request.root_artifact_ref
        if root_artifact_ref.tool_id != "root_engine":
            raise ApiErrorV1(
                invalid_request(
                    request.api_version,
                    details={"reason": "root_artifact_ref.tool_id must be 'root_engine'"},
                )
            )

        runtime_config: Dict[str, Any] = {
            "api_version": request.api_version,
            "root_artifact_ref": root_artifact_ref.model_dump(exclude_none=True),
            "config": dict(request.config),
        }

        legacy_request = RunSubmitRequest(
            api_version=request.api_version,
            config=runtime_config,
        )

        return self.submit_run(legacy_request)
    
    def submit_query_run(self, request: QueryRunSubmitRequest) -> RunSubmitResponse:
        self._ensure_version_1x(request.api_version)

        statistical_artifact_ref = request.statistical_artifact_ref
        if statistical_artifact_ref.tool_id != "statistical_engine":
            raise ApiErrorV1(
                invalid_request(
                    request.api_version,
                    details={"reason": "statistical_artifact_ref.tool_id must be 'statistical_engine'"},
                )
            )

        runtime_config: Dict[str, Any] = {
            "api_version": request.api_version,
            "statistical_artifact_ref": statistical_artifact_ref.model_dump(exclude_none=True),
            "query": {
                "intent_id": request.intent_id,
                "params": dict(request.params),
            },
        }

        legacy_request = RunSubmitRequest(
            api_version=request.api_version,
            config=runtime_config,
        )

        return self.submit_run(legacy_request)
    
    def submit_pattern_run(self, request: PatternRunSubmitRequest) -> RunSubmitResponse:
        self._ensure_version_1x(request.api_version)

        legacy_request = RunSubmitRequest(
            api_version=request.api_version,
            config={
                "api_version": request.api_version,
                "dataset": request.dataset,
                "config": (
                    request.config.model_dump(mode="json", exclude_none=True)
                    if hasattr(request.config, "model_dump")
                    else request.config
                ),
            },
        )

        return self.submit_run(legacy_request)

    def submit_run(self, request: RunSubmitRequest) -> RunSubmitResponse:
        self._ensure_version_1x(request.api_version)

        # O6 must validate config itself (freeze M1)
        try:
            validated = self._validate_config(request.config)
        except PublicIntentValidationError as e:
            raise ApiErrorV1(
                invalid_intent(request.api_version, details={"reason": str(e)})
            ) from e
        except Exception as e:
            raise ApiErrorV1(
                invalid_config(request.api_version, details={"reason": str(e)})
            ) from e
        
        raw_lineage = dict(validated.get("lineage") or {})
        run_lineage = canonicalize_lineage_v1(raw_lineage) if raw_lineage else {}

        # O2 (audit/telemetria): resta disponibile come config_hash
        config_hash = self._fingerprint_config(validated)

        # C3: input_hash deterministico (col DTO attuale coincide con hash canonico della config)
        input_hash = self._compute_input_hash(request)

        # C3: engine_version dal contesto runtime (no hardcode)
        engine_version = self._engine_version

        # O3 key component: fingerprint := artifact_identity_hash
        fingerprint = compute_o3_fingerprint(
            input_hash=input_hash,
            config_hash=config_hash,
            engine_version=engine_version,
        )

        try:
            # DEV plan: singolo nodo = pipeline.id (sufficiente per smoke test O6-T1)
            pid = str(validated.get("pipeline", {}).get("id", "demo"))
            plan: ExecutionPlanLike = _DevSingleNodePlan(pid)

            scheduler = self._scheduler_factory(validated, fingerprint)
            scheduler.start()

                    # If runtime produced a definitive artifact fingerprint, override run fingerprint
            fp_override = getattr(scheduler, "fingerprint_override", None)
            if isinstance(fp_override, str) and fp_override:
                fingerprint = fp_override

        except Exception as e:
            raise ApiErrorV1(invalid_request(request.api_version, details={"reason": str(e)})) from e

        run_id = str(uuid.uuid4())
        self._runs[run_id] = _RunContext(
            fingerprint=fingerprint,
            scheduler=scheduler,
            lineage=run_lineage,
        )

        status = map_run_status(scheduler.get_nodes())
        artifact = None
        if self._producer_tool_id is not None:
            artifact = ArtifactRefV1(
                tool_id=self._producer_tool_id,
                fingerprint=fingerprint,
            )
        return RunSubmitResponse(
            api_version=request.api_version,
            run_id=run_id,
            fingerprint=fingerprint,
            status=status,
            artifact=artifact,
        )

    def get_run(self, run_id: str, *, api_version: str = "1.0") -> RunGetResponse:
        self._ensure_version_1x(api_version)

        ctx = self._runs.get(run_id)
        if ctx is None:
            raise ApiErrorV1(not_found(api_version, message="run_id not found"))

        nodes = ctx.scheduler.get_nodes()
        return RunGetResponse(
            api_version=api_version,
            run_id=run_id,
            fingerprint=ctx.fingerprint,
            status=map_run_status(nodes),
            summary=summarize(nodes),
        )

    def list_nodes(self, run_id: str, *, api_version: str = "1.0") -> RunNodesResponse:
        self._ensure_version_1x(api_version)

        ctx = self._runs.get(run_id)
        if ctx is None:
            raise ApiErrorV1(not_found(api_version, message="run_id not found"))

        nodes = ctx.scheduler.get_nodes()
        node_dtos: List[NodeSummaryV1] = map_nodes(nodes)

        return RunNodesResponse(
            api_version=api_version,
            run_id=run_id,
            fingerprint=ctx.fingerprint,
            nodes=node_dtos,
        )
    
    @staticmethod
    def _manifest_output_relpaths(manifest: Mapping[str, Any]) -> set[str]:
        outputs = manifest.get("outputs") or []
        relpaths: set[str] = set()

        if not isinstance(outputs, list):
            raise ValueError("manifest.outputs must be a list")

        for i, item in enumerate(outputs):
            if not isinstance(item, Mapping):
                raise ValueError(f"manifest.outputs[{i}] must be an object")

            relpath = item.get("relpath")
            if not isinstance(relpath, str) or not relpath:
                raise ValueError(f"manifest.outputs[{i}].relpath must be a non-empty string")

            relpaths.add(relpath)

        return relpaths

    def get_manifest(self, tool_id: str, fingerprint: str, *, api_version: str = "1.0") -> ManifestGetResponse:
        self._ensure_version_1x(api_version)

        try:
            manifest: O3Manifest = self._artifact_store.get_manifest(tool_id=tool_id, fingerprint=fingerprint)
        except Exception as e:
            raise ApiErrorV1(not_found(api_version, message="manifest not found", details={"reason": str(e)})) from e

        # O6 must validate manifest via O1 (freeze M1)
        try:
            self._validate_manifest(manifest)
        except Exception as e:
            raise ApiErrorV1(invalid_request(api_version, message="invalid manifest", details={"reason": str(e)})) from e

        return ManifestGetResponse(
            api_version=api_version,
            tool_id=tool_id,
            fingerprint=fingerprint,
            manifest=dict(manifest),
        )
    
    def open_artifact_output(
        self,
        tool_id: str,
        fingerprint: str,
        relpath: str,
        *,
        api_version: str = "1.0",
    ) -> BinaryIO:
        self._ensure_version_1x(api_version)

        try:
            manifest: O3Manifest = self._artifact_store.get_manifest(
                tool_id=tool_id,
                fingerprint=fingerprint,
            )
        except Exception as e:
            raise ApiErrorV1(
                not_found(
                    api_version,
                    message="manifest not found",
                    details={"reason": str(e)},
                )
            ) from e

        try:
            self._validate_manifest(manifest)
        except Exception as e:
            raise ApiErrorV1(
                invalid_request(
                    api_version,
                    message="invalid manifest",
                    details={"reason": str(e)},
                )
            ) from e

        try:
            allowed_relpaths = self._manifest_output_relpaths(manifest)
        except Exception as e:
            raise ApiErrorV1(
                invalid_request(
                    api_version,
                    message="invalid manifest outputs",
                    details={"reason": str(e)},
                )
            ) from e

        if relpath not in allowed_relpaths:
            raise ApiErrorV1(
                invalid_request(
                    api_version,
                    message="relpath not declared in manifest",
                    details={"relpath": relpath},
                )
            )

        try:
            return self._artifact_store.open_output(
                tool_id=tool_id,
                fingerprint=fingerprint,
                relpath=relpath,
            )
        except ArtifactNotFoundError as e:
            raise ApiErrorV1(
                not_found(
                    api_version,
                    message="artifact file not found",
                    details={"relpath": relpath, "reason": str(e)},
                )
            ) from e
        except Exception as e:
            raise ApiErrorV1(
                invalid_request(
                    api_version,
                    message="invalid artifact relpath",
                    details={"relpath": relpath, "reason": str(e)},
                )
            ) from e

def _dag_and_targets_from_config(cfg: Mapping[str, Any]) -> tuple[DAGModel, list[str]]:
    pipeline = cfg.get("pipeline") or {}
    pid = str(pipeline.get("id", "demo"))

    steps = pipeline.get("steps")
    if not steps:
        # minimal 1-node DAG
        n = Node(id=pid, dependencies=tuple(), tool_id=pid)
        dag = DAGModel(nodes={pid: n})
        return dag, [pid]

    # steps schema: [{step_id, op, with?, needs?}]
    nodes: dict[str, Node] = {}

    # First pass: build nodes from steps
    for st in steps:
        sid = str(st["step_id"])
        deps = tuple(str(x) for x in (st.get("needs") or ()))
        tool_id = str(st.get("op"))  # O4A: tool_id is required on Node
        nodes[sid] = Node(id=sid, dependencies=deps, tool_id=tool_id)

    # Ensure all deps exist as nodes (defensive)
    for sid, node in list(nodes.items()):
        for d in node.dependencies:
            if d not in nodes:
                # tool_id unknown for implicit dep; keep deterministic placeholder = dep id
                nodes[d] = Node(id=d, dependencies=tuple(), tool_id=d)

    dag = DAGModel(nodes=nodes)

    # compute leaf targets (no outgoing edges) deterministically
    outdeg: dict[str, int] = {nid: 0 for nid in nodes.keys()}
    for nid, node in nodes.items():
        for d in node.dependencies:
            outdeg[d] = outdeg.get(d, 0) + 1

    targets = sorted([nid for nid, od in outdeg.items() if od == 0])
    if not targets:
        targets = [sorted(nodes.keys())[0]]

    return dag, targets

# -------------------------
# Real wiring factory (uses O2/O5/O1/O3)
# -------------------------
def create_api_v1(*, artifact_store: O3ArtifactStorePort, engine_version: str) -> ApiImplV1:
    """
    Production wiring for O6 v1. No persistence. No hidden storage.
    """

    def _validate(cfg: Any) -> Dict[str, Any]:
        return o2_validate_config(cfg, strict=True)

    def _fp(cfg: Any) -> str:
        # cfg is already validated; avoid double-validate
        return o2_compute_config_fingerprint(cfg, strict=True, validate=False)

    from runtime.execution_state import ExecutionState
    from runtime.execution_queue import ExecutionQueue
    from runtime.runtime_trace import RuntimeTrace
    from runtime.execution_scheduler import ExecutionScheduler

    def _scheduler_factory(cfg: Mapping[str, Any], fp: str) -> SchedulerPort:
        state = ExecutionState()
        queue = ExecutionQueue()
        trace = RuntimeTrace()
        sched = ExecutionScheduler(state=state, queue=queue, trace=trace)

        dag, targets = _dag_and_targets_from_config(cfg)
        plan = build_execution_plan(dag, targets=targets)

        return ExecutionSchedulerAdapter(sched, plan=plan)

    def _validate_manifest(m: dict) -> None:
        o1_validate_manifest(m, strict=True)

    return ApiImplV1(
        validate_config=_validate,
        fingerprint_config=_fp,
        scheduler_factory=_scheduler_factory,
        artifact_store=artifact_store,
        validate_manifest=_validate_manifest,
        engine_version=engine_version,
        producer_tool_id=None,
    )


