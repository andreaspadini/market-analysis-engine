from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .events_v1 import (
    EventEnvelopeV1,
    RunSubmittedPayload,
    RunStartedPayload,
    NodeStartedPayload,
    NodeSucceededPayload,
    NodeFailedPayload,
    NodeSkippedPayload,
    RunSucceededPayload,
    RunFailedPayload,
    EventType,
)
from .event_store_port import EventStorePort


class _RunSequencer:
    """
    Guardrail (2): seq monotonic per run, thread-safe, assigned BEFORE write, no duplicates.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._seq_by_run: Dict[str, int] = {}

    def next(self, run_id: str) -> int:
        with self._lock:
            cur = self._seq_by_run.get(run_id, 0) + 1
            self._seq_by_run[run_id] = cur
            return cur


@dataclass(frozen=True)
class EventRecorder:
    """
    Guardrail (1): best-effort, side-effect safe.
    No exception from store must propagate into runtime.
    """
    store: EventStorePort
    _sequencer: _RunSequencer = _RunSequencer()

    def _emit(self, *, run_id: str, type: EventType, payload_obj: Any) -> None:
        seq = self._sequencer.next(run_id)  # assign before writing
        try:
            env = EventEnvelopeV1.new(run_id=run_id, seq=seq, type=type, payload=payload_obj)
            self.store.append(env.__dict__)
        except Exception:
            # swallow (best-effort): must not impact runtime
            return

    # --- Hooks to be called by runtime (non-invasive) ---

    def on_run_submitted(self, *, run_id: str, pipeline: str, config_fingerprint: str) -> None:
        self._emit(run_id=run_id, type="RunSubmitted", payload_obj=RunSubmittedPayload(pipeline=pipeline, config_fingerprint=config_fingerprint))

    def on_run_started(self, *, run_id: str) -> None:
        self._emit(run_id=run_id, type="RunStarted", payload_obj=RunStartedPayload())

    def on_node_started(self, *, run_id: str, node_id: str) -> None:
        self._emit(run_id=run_id, type="NodeStarted", payload_obj=NodeStartedPayload(node_id=node_id))

    def on_node_succeeded(self, *, run_id: str, node_id: str) -> None:
        self._emit(run_id=run_id, type="NodeSucceeded", payload_obj=NodeSucceededPayload(node_id=node_id))

    def on_node_failed(self, *, run_id: str, node_id: str, error: BaseException) -> None:
        self._emit(
            run_id=run_id,
            type="NodeFailed",
            payload_obj=NodeFailedPayload(node_id=node_id, error_type=type(error).__name__, error_message=str(error)),
        )

    def on_node_skipped(self, *, run_id: str, node_id: str, reason: str) -> None:
        self._emit(run_id=run_id, type="NodeSkipped", payload_obj=NodeSkippedPayload(node_id=node_id, reason=reason))

    def on_run_succeeded(self, *, run_id: str) -> None:
        self._emit(run_id=run_id, type="RunSucceeded", payload_obj=RunSucceededPayload())

    def on_run_failed(self, *, run_id: str, error: BaseException) -> None:
        self._emit(run_id=run_id, type="RunFailed", payload_obj=RunFailedPayload(error_type=type(error).__name__, error_message=str(error)))
