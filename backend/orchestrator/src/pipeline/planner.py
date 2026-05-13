"""O4A — Pure deterministic planner.

Planner inputs:
- dag: DAGModel
- targets: list[str]
- cache_hits: dict[node_id, bool] (precomputed externally)
- run_fingerprint: str (used ONLY for plan_id)

Planner is a pure function:
- no filesystem
- no adapters
- no mutation of inputs

Tie-break rule: lexicographic ascending on node_id everywhere.
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, Iterable, List, Mapping, Set, Tuple

from .dag_builder import deterministic_topo
from .dag_model import DAGModel
from .planner_types import ExecutionPlan


def _closure_with_deps(dag: DAGModel, targets: Iterable[str]) -> Set[str]:
    """Return set of all nodes needed to build targets (including deps)."""
    dag.validate_contains(targets)
    needed: Set[str] = set()
    stack: List[str] = list(targets)
    while stack:
        n = stack.pop()
        if n in needed:
            continue
        needed.add(n)
        for d in dag.dependencies_of(n):
            if d not in needed:
                stack.append(d)
    return needed


def _canonical_plan_payload(
    *,
    run_fingerprint: str,
    ordered: Tuple[str, ...],
    to_build: Tuple[str, ...],
    cached: Tuple[str, ...],
) -> str:
    """Canonical JSON payload used for plan_id.

    Keep stable:
    - fixed keys
    - compact separators
    - no whitespace
    """
    payload = {
        "run_fingerprint": run_fingerprint,
        "ordered": ordered,
        "to_build": to_build,
        "cached": cached,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def plan(
    *,
    dag: DAGModel,
    targets: List[str],
    cache_hits: Mapping[str, bool],
    run_fingerprint: str,
) -> ExecutionPlan:
    """Create an ExecutionPlan.

    Minimal rebuild policy:
    - Compute closure(targets).
    - Topologically order closure deterministically.
    - A node is scheduled in to_build if:
        - cache_hits[node] is False (or missing), OR
        - any dependency is scheduled in to_build (propagation).
    """
    if not run_fingerprint:
        # Still deterministic, but run_fingerprint is required by spec.
        raise ValueError("run_fingerprint must be non-empty")

    # Deterministic targets ordering (tie-break rule).
    targets_sorted = sorted(set(targets))
    closure = _closure_with_deps(dag, targets_sorted)

    # Deterministic global topo then filter to closure.
    global_order = deterministic_topo(dag)
    ordered = tuple([n for n in global_order if n in closure])

    # Propagate rebuild requirement in topo order.
    needs_build: Dict[str, bool] = {}
    for n in ordered:
        hit = bool(cache_hits.get(n, False))
        dep_build = any(needs_build[d] for d in dag.dependencies_of(n) if d in closure)
        needs_build[n] = (not hit) or dep_build

    to_build = tuple([n for n in ordered if needs_build[n]])
    cached = tuple([n for n in ordered if not needs_build[n]])

    payload = _canonical_plan_payload(
        run_fingerprint=run_fingerprint,
        ordered=ordered,
        to_build=to_build,
        cached=cached,
    )
    plan_id = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    return ExecutionPlan(plan_id=plan_id, ordered=ordered, to_build=to_build, cached=cached)
