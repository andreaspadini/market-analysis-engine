from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Protocol, Dict, Any, List


class EventStorePort(Protocol):
    """
    Pure port (no business logic).
    """

    def append(self, event: Dict[str, Any]) -> None:
        ...

    def read_all(self, run_id: str) -> List[Dict[str, Any]]:
        ...
