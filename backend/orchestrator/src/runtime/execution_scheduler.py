"""ExecutionScheduler: converts an ExecutionPlan into a deterministic queue.

Guardrails:
- Nodes in plan.cached are marked SKIPPED and are NOT enqueued.
- Only plan.to_build is enqueued, in the order provided by the plan.

This module depends only on O4A's plan *shape* at runtime; for tests we use stubs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, Set

from .execution_queue import ExecutionQueue
from .execution_state import ExecutionState
from .runtime_trace import RuntimeTrace
import logging
logger = logging.getLogger(__name__)

class ExecutionPlanLike(Protocol):
    @property
    def to_build(self) -> Sequence[str]: ...

    @property
    def cached(self) -> Set[str]: ...


@dataclass(frozen=True)
class ScheduleResult:
    enqueued: list[str]
    skipped: list[str]


class ExecutionScheduler:
    def __init__(
        self,
        *,
        state: ExecutionState,
        queue: ExecutionQueue,
        trace: RuntimeTrace | None = None,
    ):
        self._state = state
        self._queue = queue
        self._trace = trace or RuntimeTrace.disabled()

    @property
    def state(self) -> ExecutionState:
        return self._state

    def schedule(self, plan: ExecutionPlanLike) -> ScheduleResult:
        # Ensure all nodes exist in state for introspection.
        for nid in list(plan.cached) + list(plan.to_build):
            self._state.ensure_node(str(nid))

        logger.debug(
            "runtime.execution_started phase=schedule to_build_count=%s cached_count=%s",
            len(list(plan.to_build)),
            len(list(plan.cached)),
        )

        skipped: list[str] = []
        for nid in sorted(plan.cached):
            # Cached marking is deterministic by sorted order (set -> stable order).
            nid_s = str(nid)
            before = self._state.get(nid_s).status
            self._state.mark_skipped_cached(nid_s)
            after = self._state.get(nid_s).status
            self._trace.on_transition(
                nid_s,
                from_status=before,
                to_status=after,
                attempt=self._state.get(nid_s).attempt,
            )
            skipped.append(nid_s)

        enqueued: list[str] = []
        for nid in plan.to_build:
            nid_s = str(nid)
            if nid_s in plan.cached:
                # Must not enqueue cached nodes.
                continue
            # Remains PENDING until worker starts.
            self._queue.enqueue(nid_s)
            enqueued.append(nid_s)

        logger.debug(
            "runtime.execution_finished phase=schedule enqueued_count=%s skipped_count=%s state_records=%s",
            len(enqueued),
            len(skipped),
            len(self._state.all_records()) if hasattr(self._state, "all_records") else -1,
        )

        return ScheduleResult(enqueued=enqueued, skipped=skipped)

    def get_nodes(self):
        """
        API helper for O6: returns node runtime records in deterministic order.
        """
        # 1) via API pubblica ExecutionState
        if hasattr(self._state, "all_records") and callable(getattr(self._state, "all_records")):
            recs = getattr(self._state, "all_records")()
            return [recs[nid] for nid in sorted(recs.keys())]

        # 2) fallback: accesso diretto al backing store (se presente)
        if hasattr(self._state, "_records"):
            recs = getattr(self._state, "_records")
            return [recs[nid] for nid in sorted(recs.keys())]

        return []

