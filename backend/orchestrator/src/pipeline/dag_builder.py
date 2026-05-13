"""O4A — DAGBuilder: PipelineDefinition -> DAGModel.

Responsibilities (M2):
- Build DAGModel from PipelineDefinition (normalized input).
- Validate structural invariants.
- Cycle detection (deterministic) via topo_sort.

No runtime, no adapters, no filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .dag_model import DAGModel, Node
from .pipeline_definition import PipelineDefinition
from .topo_sort import CycleError, topo_sort


@dataclass(frozen=True, slots=True)
class DAGBuildError(ValueError):
    message: str

    def __str__(self) -> str:  # pragma: no cover
        return self.message


def build_dag(definition: PipelineDefinition, *, validate_acyclic: bool = True) -> DAGModel:
    """Build a DAGModel from a normalized PipelineDefinition."""
    # Definition is expected normalized, but we still enforce determinism: sort deps.
    seen: Dict[str, Node] = {}

    # Check unique ids
    for spec in definition.nodes:
        if not spec.node_id:
            raise DAGBuildError("Node id must be non-empty")
        if spec.node_id in seen:
            raise DAGBuildError(f"Duplicate node_id: {spec.node_id}")
        if not spec.tool_id:
            raise DAGBuildError(f"tool_id must be non-empty for node {spec.node_id}")
        deps = tuple(sorted(spec.dependencies))
        if spec.node_id in deps:
            raise DAGBuildError(f"Node {spec.node_id} cannot depend on itself")
        seen[spec.node_id] = Node(id=spec.node_id, dependencies=deps, tool_id=spec.tool_id)

    # Validate deps exist
    missing = []
    for node in seen.values():
        for dep in node.dependencies:
            if dep not in seen:
                missing.append((node.id, dep))
    if missing:
        # deterministic message: sort by (node, dep)
        missing_sorted = ", ".join([f"{n}->{d}" for n, d in sorted(missing)])
        raise DAGBuildError(f"Unknown dependency reference(s): {missing_sorted}")

    dag = DAGModel(nodes=dict(seen))

    if validate_acyclic:
        _ = topo_sort(dag.node_ids(), {nid: dag.dependencies_of(nid) for nid in dag.node_ids()})

    return dag


def deterministic_topo(dag: DAGModel) -> Tuple[str, ...]:
    """Convenience wrapper: deterministic topo order for the whole DAG."""
    return topo_sort(dag.node_ids(), {nid: dag.dependencies_of(nid) for nid in dag.node_ids()})
