"""In-process runtime trace observer for O5A.

Normative constraints:
- NOT an event bus
- NOT a public contract
- NOT persisted
- Only for local debug/telemetry hooks (optional)

Implementation provides a tiny observer API used by scheduler/worker/state.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from .runtime_types import Status, TraceEvent


class RuntimeTrace:
    """A lightweight, in-process trace sink.

    By default it's disabled (no-op). A collecting trace can be used in tests.
    """

    def __init__(self, sink: Optional[Callable[[TraceEvent], None]] = None):
        self._sink = sink

    @staticmethod
    def disabled() -> "RuntimeTrace":
        return RuntimeTrace(sink=None)

    @staticmethod
    def collecting() -> "CollectingRuntimeTrace":
        return CollectingRuntimeTrace()

    def emit(self, event: TraceEvent) -> None:
        if self._sink is not None:
            self._sink(event)

    def on_transition(self, node_id: str, *, from_status: Status, to_status: Status, attempt: int, detail: str | None = None) -> None:
        self.emit(
            TraceEvent(
                node_id=str(node_id),
                from_status=from_status,
                to_status=to_status,
                attempt=int(attempt),
                detail=detail,
            )
        )


class CollectingRuntimeTrace(RuntimeTrace):
    """Collects trace events in memory (useful for tests)."""

    def __init__(self):
        self.events: List[TraceEvent] = []
        super().__init__(sink=self.events.append)
