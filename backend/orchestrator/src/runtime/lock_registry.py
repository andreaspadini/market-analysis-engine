from __future__ import annotations

import threading


class LockRegistry:
    """
    Node-level lock registry (in-memory, single-process).
    Normativa: lock_key = node_id
    Vincolo: un node_id non può essere RUNNING su più worker contemporaneamente.
    """

    def __init__(self) -> None:
        self._mu = threading.Lock()
        self._held: set[str] = set()

    def try_acquire(self, node_id: str) -> bool:
        """Return True if acquired, False if already held."""
        with self._mu:
            if node_id in self._held:
                return False
            self._held.add(node_id)
            return True

    def release(self, node_id: str) -> None:
        """Idempotent release."""
        with self._mu:
            self._held.discard(node_id)

    def is_held(self, node_id: str) -> bool:
        with self._mu:
            return node_id in self._held
