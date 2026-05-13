"""ExecutionWorker: consumes queue, executes nodes via O4B, retries deterministically.

Constraints enforced:
- Worker MUST NOT call CorePort.
- Worker invokes only O4B.ExecutionEngine.execute(...) (injected dependency).
- Single-thread, fail-fast by default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol

from .execution_queue import ExecutionQueue
from .execution_state import ExecutionState
from .retry_policy import RetryPolicy
from .runtime_trace import RuntimeTrace
from .runtime_types import Status


class ExecutionEngineLike(Protocol):
    """O4B ExecutionEngine interface (entrypoint only).

    We intentionally keep it minimal to avoid coupling; tests provide stubs.
    """

    def execute(self, *, node_id: str, attempt: int, context: Optional[dict[str, Any]] = None) -> bool: ...


@dataclass(frozen=True)
class WorkerResult:
    processed: list[str]
    failed_node: Optional[str] = None


class ExecutionWorker:
    def __init__(
        self,
        *,
        state: ExecutionState,
        queue: ExecutionQueue,
        engine: ExecutionEngineLike,
        retry_policy: RetryPolicy | None = None,
        trace: RuntimeTrace | None = None,
        fail_fast: bool = True,
        context: Optional[dict[str, Any]] = None,
    ):
        self._state = state
        self._queue = queue
        self._engine = engine
        self._retry = retry_policy or RetryPolicy()
        self._trace = trace or RuntimeTrace.disabled()
        self._fail_fast = bool(fail_fast)
        self._context = context or {}

    def run(self) -> WorkerResult:
        processed: list[str] = []
        failed_node: Optional[str] = None

        while not self._queue.is_empty():
            item = self._queue.dequeue()
            node_id = item.node_id
            rec_before = self._state.get(node_id)

            # PENDING -> RUNNING
            self._state.mark_running(node_id)
            self._trace.on_transition(
                node_id,
                from_status=rec_before.status,
                to_status=Status.RUNNING,
                attempt=rec_before.attempt,
            )

            attempt = self._state.get(node_id).attempt

            try:
                ok = self._engine.execute(node_id=node_id, attempt=attempt, context=dict(self._context))
                if ok is not True:
                    raise RuntimeError("ExecutionEngine.execute returned non-true result")

                # RUNNING -> SUCCESS
                rec_running = self._state.get(node_id)
                self._state.mark_success(node_id)
                self._trace.on_transition(
                    node_id,
                    from_status=rec_running.status,
                    to_status=Status.SUCCESS,
                    attempt=attempt,
                )
                processed.append(node_id)

            except BaseException as exc:  # noqa: BLE001
                rec_running = self._state.get(node_id)

                # Determine retry deterministically based on current attempt.
                if self._retry.should_retry(attempt=attempt, exc=exc):
                    # RUNNING -> PENDING (retry) and re-enqueue deterministically.
                    self._state.mark_pending_for_retry(node_id)
                    self._trace.on_transition(
                        node_id,
                        from_status=rec_running.status,
                        to_status=Status.PENDING,
                        attempt=attempt,
                        detail=f"retry:{type(exc).__name__}",
                    )
                    self._queue.enqueue(node_id)
                else:
                    # Persist minimal deterministic error into meta for API introspection (in-memory only).
                    err: dict[str, Any] = {"type": type(exc).__name__}
                    msg = str(exc)
                    if msg:
                        err["message"] = msg

                    meta = dict(rec_running.meta or {})
                    meta["error"] = err
                    self._state.set_meta(node_id, meta)

                    # RuntimeRecord is frozen; update backing store deterministically (runtime-internal).
                    if hasattr(self._state, "_records"):
                        from dataclasses import replace

                        self._state._records[node_id] = replace(rec_running, meta=meta)  # type: ignore[attr-defined]

                    # RUNNING -> FAILED (final)
                    self._state.mark_failed(node_id)
                    self._trace.on_transition(
                        node_id,
                        from_status=rec_running.status,
                        to_status=Status.FAILED,
                        attempt=attempt,
                        detail=f"failed:{type(exc).__name__}",
                    )
                    processed.append(node_id)
                    failed_node = node_id
                    if self._fail_fast:
                        break

        return WorkerResult(processed=processed, failed_node=failed_node)