"""Deterministic in-memory FIFO queue for O5A."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, Iterator, Optional


@dataclass(frozen=True)
class QueueItem:
    node_id: str


class ExecutionQueue:
    """Single-process FIFO queue.

    Deterministic properties:
      - `enqueue_many` preserves the provided order.
      - `dequeue` always returns the oldest enqueued item.
    """

    def __init__(self, items: Optional[Iterable[QueueItem]] = None):
        self._q: Deque[QueueItem] = deque(items or [])

    def __len__(self) -> int:
        return len(self._q)

    def is_empty(self) -> bool:
        return not self._q

    def enqueue(self, node_id: str) -> None:
        self._q.append(QueueItem(node_id=str(node_id)))

    def enqueue_many(self, node_ids: Iterable[str]) -> None:
        for nid in node_ids:
            self.enqueue(str(nid))

    def dequeue(self) -> QueueItem:
        return self._q.popleft()

    def peek(self) -> QueueItem:
        return self._q[0]

    def iter_node_ids(self) -> Iterator[str]:
        for item in self._q:
            yield item.node_id

    def snapshot(self) -> list[str]:
        """Returns a deterministic snapshot of the queue contents."""
        return list(self.iter_node_ids())
