"""O4A — Planner types.

ExecutionPlan is immutable (frozen) and serializable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Immutable execution plan.

    Contains exclusively:
    - plan_id: deterministic sha256 of a canonical representation of the plan.
    - ordered: deterministic topological order (restricted to the requested closure).
    - to_build: deterministic subsequence of ordered.
    - cached: deterministic subsequence of ordered.
    """

    plan_id: str
    ordered: Tuple[str, ...]
    to_build: Tuple[str, ...]
    cached: Tuple[str, ...]
