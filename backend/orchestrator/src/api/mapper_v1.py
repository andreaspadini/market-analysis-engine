from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .dto_v1 import NodeSummaryV1, SummaryV1


# O6: status pubblici (stringhe) — non leakiamo enum/classi runtime
RUN_STATUS_PENDING = "PENDING"
RUN_STATUS_RUNNING = "RUNNING"
RUN_STATUS_SUCCEEDED = "SUCCEEDED"
RUN_STATUS_FAILED = "FAILED"

NODE_STATUS_PENDING = "PENDING"
NODE_STATUS_RUNNING = "RUNNING"
NODE_STATUS_SUCCEEDED = "SUCCEEDED"
NODE_STATUS_FAILED = "FAILED"
NODE_STATUS_CACHED = "CACHED"
NODE_STATUS_SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class _NodeLike:
    """
    Adapter minimale per rendere il mapper testabile senza dipendere da classi runtime.

    Campi attesi:
      - name: str
      - status: str | enum (qualunque cosa stringabile)
      - is_cached: bool
      - is_skipped: bool
      - error: Optional[dict] (già sanitizzato)
    """
    name: str
    status: Any
    is_cached: bool
    is_skipped: bool
    error: Optional[Dict[str, Any]] = None


def _norm_status(value: Any) -> str:
    # enum -> .value / .name spesso; fallback a str
    if value is None:
        return ""
    if hasattr(value, "value") and isinstance(getattr(value, "value"), str):
        return getattr(value, "value")
    if hasattr(value, "name") and isinstance(getattr(value, "name"), str):
        return getattr(value, "name")
    return str(value)


def map_node_status(node: _NodeLike) -> str:
    # cached/skipped sono orthogonal: prevalgono sullo "status" runtime
    if node.is_skipped:
        return NODE_STATUS_SKIPPED
    if node.is_cached:
        return NODE_STATUS_CACHED

    s = _norm_status(node.status).upper()
    if s in ("PENDING", "QUEUED"):
        return NODE_STATUS_PENDING
    if s in ("RUNNING", "IN_PROGRESS"):
        return NODE_STATUS_RUNNING
    if s in ("SUCCEEDED", "SUCCESS", "DONE"):
        return NODE_STATUS_SUCCEEDED
    if s in ("FAILED", "ERROR"):
        return NODE_STATUS_FAILED

    # Unknown runtime statuses must not leak; degrade safely
    return NODE_STATUS_PENDING


def map_run_status(nodes: Iterable[_NodeLike]) -> str:
    # derivato SOLO da runtime in-memory (lista nodi)
    mapped = [map_node_status(n) for n in nodes]
    if not mapped:
        return RUN_STATUS_PENDING

    if any(s == NODE_STATUS_FAILED for s in mapped):
        return RUN_STATUS_FAILED
    if any(s == NODE_STATUS_RUNNING for s in mapped):
        return RUN_STATUS_RUNNING

    # se tutti terminali
    terminals = {NODE_STATUS_SUCCEEDED, NODE_STATUS_CACHED, NODE_STATUS_SKIPPED}
    if all(s in terminals for s in mapped):
        return RUN_STATUS_SUCCEEDED

    return RUN_STATUS_PENDING


def summarize(nodes: Iterable[_NodeLike]) -> SummaryV1:
    mapped = [map_node_status(n) for n in nodes]
    total = len(mapped)

    pending = sum(1 for s in mapped if s == NODE_STATUS_PENDING)
    running = sum(1 for s in mapped if s == NODE_STATUS_RUNNING)
    succeeded = sum(1 for s in mapped if s == NODE_STATUS_SUCCEEDED)
    failed = sum(1 for s in mapped if s == NODE_STATUS_FAILED)
    cached = sum(1 for s in mapped if s == NODE_STATUS_CACHED)
    skipped = sum(1 for s in mapped if s == NODE_STATUS_SKIPPED)

    return SummaryV1(
        total_nodes=total,
        pending=pending,
        running=running,
        succeeded=succeeded,
        failed=failed,
        cached=cached,
        skipped=skipped,
    )


def map_nodes(nodes: Iterable[_NodeLike]) -> List[NodeSummaryV1]:
    out: List[NodeSummaryV1] = []
    for n in nodes:
        out.append(
            NodeSummaryV1(
                name=n.name,
                status=map_node_status(n),
                is_cached=bool(n.is_cached),
                is_skipped=bool(n.is_skipped),
                error=n.error,
            )
        )
    return out
