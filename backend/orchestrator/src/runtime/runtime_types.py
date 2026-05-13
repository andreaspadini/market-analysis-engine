"""Runtime types for O5A.

This module is **data-only**: no business logic.
All types are considered internal/private to orchestrator runtime (non-contract).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class Status(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class RuntimeRecord:
    """Per-node runtime record.

    Notes:
      - `attempt` is 1-based and represents the next attempt to be executed.
      - `meta` is strictly in-memory and optional.
    """

    node_id: str
    status: Status = Status.PENDING
    attempt: int = 1
    meta: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class TraceEvent:
    """Private trace event (in-process only, non-persisted, non-contract)."""

    node_id: str
    from_status: Status
    to_status: Status
    attempt: int
    detail: Optional[str] = None
