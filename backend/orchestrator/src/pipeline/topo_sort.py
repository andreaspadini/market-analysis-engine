"""O4A — Deterministic topological sort + cycle detection.

Tie-break rule (frozen): lexicographic ascending on node_id.

This module is runtime-free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple


@dataclass(frozen=True, slots=True)
class CycleError(ValueError):
    """Raised when a cycle is detected in a DAG."""

    cycle_nodes: Tuple[str, ...]

    def __str__(self) -> str:  # pragma: no cover
        return f"Cycle detected involving: {', '.join(self.cycle_nodes)}"


def topo_sort(nodes: Iterable[str], deps: Mapping[str, Sequence[str]]) -> Tuple[str, ...]:
    """Return deterministic topological ordering.

    Args:
        nodes: iterable of node ids.
        deps: mapping node_id -> dependency node_ids

    Raises:
        CycleError if the graph contains a cycle.
    """
    # Determinism requires lexicographic tie-break. To avoid heap-based O(log V)
    # selection while keeping deterministic ordering, we:
    # 1) compute a stable rank by sorting node_ids once,
    # 2) maintain an "available" boolean array keyed by rank,
    # 3) advance a pointer to pick the next smallest available rank.
    #
    # After the initial sort, the selection loop is O(V+E) (pointer advances at
    # most V times, each edge processed once).
    node_set: Set[str] = set(nodes)
    ordered_nodes: List[str] = sorted(node_set)
    rank: Dict[str, int] = {n: i for i, n in enumerate(ordered_nodes)}

    # in-degree counts for Kahn's algorithm
    indeg: Dict[str, int] = {n: 0 for n in node_set}
    reverse: Dict[str, List[str]] = {n: [] for n in node_set}

    for n in node_set:
        for d in deps.get(n, ()):
            if d not in node_set:
                # Ignore deps outside the requested set.
                continue
            indeg[n] += 1
            reverse[d].append(n)

    available = [False] * len(ordered_nodes)
    for n, k in indeg.items():
        if k == 0:
            available[rank[n]] = True

    ordered: List[str] = []
    i = 0
    while True:
        while i < len(available) and not available[i]:
            i += 1
        if i >= len(available):
            break

        cur = ordered_nodes[i]
        available[i] = False
        ordered.append(cur)

        next_i = i + 1
        for nxt in reverse[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                r = rank[nxt]
                available[r] = True
                if r < next_i:
                    next_i = r

        i = next_i

    if len(ordered) != len(node_set):
        # Remaining nodes with indeg > 0 are part of at least one cycle.
        cycle_nodes = tuple(sorted(n for n, k in indeg.items() if k > 0))
        raise CycleError(cycle_nodes=cycle_nodes)

    return tuple(ordered)