"""O4A — DAGModel and Node structures.

Normative constraints:
- Node is minimal: id, dependencies, tool_id.
- No fingerprints, no compute logic, no runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Tuple


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    dependencies: Tuple[str, ...]
    tool_id: str


@dataclass(frozen=True, slots=True)
class DAGModel:
    """Immutable in-memory representation of a pipeline DAG."""

    nodes: Mapping[str, Node]

    def node_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self.nodes.keys()))

    def get(self, node_id: str) -> Node:
        return self.nodes[node_id]

    def dependencies_of(self, node_id: str) -> Tuple[str, ...]:
        return self.nodes[node_id].dependencies

    def validate_contains(self, node_ids: Iterable[str]) -> None:
        missing = [n for n in node_ids if n not in self.nodes]
        if missing:
            missing_sorted = ", ".join(sorted(missing))
            raise KeyError(f"Unknown node_id(s): {missing_sorted}")
