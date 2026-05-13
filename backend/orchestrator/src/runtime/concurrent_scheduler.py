from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

from .lock_registry import LockRegistry
from .ready_set import PlanView, compute_ready
from .worker_pool import WorkerPool


@dataclass(frozen=True)
class NodeResult:
    """
    Execution result returned by the injected executor.
    - final_state: "SUCCESS" | "FAILED" | "PENDING" (PENDING means "retry needed")
    - attempts_used: how many attempts were used by this call (usually 1)
    """
    final_state: str
    attempts_used: int = 1


class ConcurrentScheduler:
    """
    O5B scheduler:
      - dispatch solo READY
      - lock node-level
      - retry deterministico (node torna PENDING e rientra nel ready-set ordinato)
      - fail-fast: stop scheduling nuovo lavoro al primo FAILED finale; join RUNNING;
                  restanti PENDING
      - no storage/FS access
    """

    def __init__(
        self,
        plan: PlanView,
        *,
        max_workers: int,
        execute: Callable[[str, int], NodeResult],
    ) -> None:
        self._plan = plan
        self._execute = execute
        self._pool = WorkerPool(max_workers=max_workers)
        self._locks = LockRegistry()

        # runtime state
        self._state: Dict[str, str] = {nid: "PENDING" for nid in plan.to_build}
        # cached handled by caller; but we provide helper: if node not in to_build, ignore.
        self._attempts: Dict[str, int] = {nid: 0 for nid in plan.to_build}

        self._fail_fast_triggered = False

    @property
    def state(self) -> Mapping[str, str]:
        return dict(self._state)

    @property
    def attempts(self) -> Mapping[str, int]:
        return dict(self._attempts)

    def mark_cached_skipped(self, cached: Sequence[str]) -> None:
        for nid in cached:
            if nid in self._state:
                self._state[nid] = "SKIPPED"

    def run(self) -> Tuple[Mapping[str, str], Mapping[str, int]]:
        """
        Blocking run.
        Returns (state_by_node, attempts_by_node).
        """
        running: Dict[object, str] = {}  # future -> node_id

        def submit_node(node_id: str) -> None:
            # Lock must be acquired before running
            if not self._locks.try_acquire(node_id):
                return

            # Transition to RUNNING
            self._state[node_id] = "RUNNING"
            attempt_no = self._attempts[node_id] + 1

            def _task() -> NodeResult:
                return self._execute(node_id, attempt_no)

            fut = self._pool.submit(_task)
            running[fut] = node_id

        try:
            while True:
                # 1) Harvest completed futures (deterministic: sort by node_id of completed set)
                done = [f for f in list(running.keys()) if f.done()]
                if done:
                    done.sort(key=lambda f: running[f])  # deterministic completion processing
                    for f in done:
                        node_id = running.pop(f)
                        self._locks.release(node_id)

                        res: NodeResult = f.result()
                        # attempts increments deterministically on completion
                        self._attempts[node_id] += res.attempts_used

                        if res.final_state == "SUCCESS":
                            self._state[node_id] = "SUCCESS"
                        elif res.final_state == "FAILED":
                            self._state[node_id] = "FAILED"
                            # fail-fast decision deterministic at first final FAILED
                            self._fail_fast_triggered = True
                        elif res.final_state == "PENDING":
                            # retry path: return to PENDING (re-enters ready-set)
                            self._state[node_id] = "PENDING"
                        else:
                            raise ValueError(f"Unknown final_state: {res.final_state}")

                # 2) fail-fast stop scheduling; join RUNNING; leave rest PENDING
                if self._fail_fast_triggered:
                    # no new scheduling; wait for all RUNNING to complete
                    if not running:
                        break
                    # keep looping until running becomes empty
                    continue

                # 3) if all nodes are final (SUCCESS/FAILED/SKIPPED) -> done
                if all(self._state[nid] in ("SUCCESS", "FAILED", "SKIPPED") for nid in self._plan.to_build):
                    break

                # 4) schedule READY nodes until capacity
                # capacity = max_workers - len(running)
                # Note: ThreadPoolExecutor doesn't expose max_workers, but we can approximate:
                # we schedule at most len(ready) nodes per iteration, but avoid overscheduling:
                # we keep a local cap by reading current running size and a stored value.
                # We'll store max_workers in pool by closure.
                # To avoid changing WorkerPool API, we infer cap via an attribute.
                max_workers = getattr(self._pool._executor, "_max_workers", 1)
                cap = max_workers - len(running)
                if cap > 0:
                    ready = compute_ready(self._plan, self._state)
                    # schedule in ready order deterministically
                    for node_id in ready:
                        if cap <= 0:
                            break
                        # skip if already running for any reason
                        if self._state.get(node_id) != "PENDING":
                            continue
                        submit_node(node_id)
                        # only count if it really became RUNNING
                        if self._state.get(node_id) == "RUNNING":
                            cap -= 1

                # 5) If nothing is running and nothing is ready, we're stuck (cycle or missing deps)
                # In foundation layer, we fail fast with explicit error.
                if not running:
                    ready_now = compute_ready(self._plan, self._state)
                    if not ready_now:
                        pending = [nid for nid in self._plan.to_build if self._state[nid] == "PENDING"]
                        raise RuntimeError(f"Deadlock: no READY nodes but pending exist: {pending}")

            return dict(self._state), dict(self._attempts)

        finally:
            self._pool.shutdown(wait=True)
