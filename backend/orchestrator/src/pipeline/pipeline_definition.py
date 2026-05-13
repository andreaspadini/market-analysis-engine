"""O4A — PipelineDefinition (data-only + normalization).

Invariants
- Pure data: no runtime state, no callables.
- Deterministic normalization:
  - Node specs are sorted lexicographically by node_id.
  - Each node's dependencies are sorted lexicographically and de-duplicated.

This is the only accepted input for the DAGBuilder in O4A.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True, slots=True)
class PipelineNodeSpec:
    """Data-only node spec used to build a DAG."""

    node_id: str
    tool_id: str
    dependencies: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PipelineDefinition:
    """Normalized pipeline definition.

    Nodes are unique by node_id.
    """

    nodes: Tuple[PipelineNodeSpec, ...]

    @staticmethod
    def normalize(nodes: Iterable[PipelineNodeSpec]) -> "PipelineDefinition":
        """Return a normalized definition with deterministic ordering."""
        specs = []
        for n in nodes:
            deps = tuple(sorted(set(n.dependencies)))
            specs.append(PipelineNodeSpec(node_id=n.node_id, tool_id=n.tool_id, dependencies=deps))
        specs.sort(key=lambda s: s.node_id)
        return PipelineDefinition(nodes=tuple(specs))

    def node_ids(self) -> Tuple[str, ...]:
        return tuple(n.node_id for n in self.nodes)
