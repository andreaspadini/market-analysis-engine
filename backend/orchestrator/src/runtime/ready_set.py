from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


FINAL_OK = {"SUCCESS", "SKIPPED"}


@dataclass(frozen=True)
class PlanView:
    """
    Minimal view used by O5B:
      - ordered: sequence of node_ids describing canonical plan order
      - to_build: set of node_ids eligible to run
      - deps: mapping node_id -> list of dependencies node_ids
    """
    ordered: Sequence[str]
    to_build: set[str]
    deps: Mapping[str, Sequence[str]]


def is_ready(node_id: str, plan: PlanView, state: Mapping[str, str]) -> bool:
    if node_id not in plan.to_build:
        return False
    if state.get(node_id) != "PENDING":
        return False
    for d in plan.deps.get(node_id, ()):
        if state.get(d) not in FINAL_OK:
            return False
    return True


def _order_key(plan: PlanView, ordered_index: Mapping[str, int], node_id: str) -> tuple[int, str]:
    # tie-break deterministico:
    # 1) posizione in plan.ordered (se presente, altrimenti in coda)
    # 2) lessicografico su node_id
    return (ordered_index.get(node_id, 10**9), node_id)


def compute_ready(plan: PlanView, state: Mapping[str, str]) -> list[str]:
    ordered_index = {nid: i for i, nid in enumerate(plan.ordered)}
    candidates: list[str] = [
        nid for nid in plan.to_build
        if is_ready(nid, plan, state)
    ]
    candidates.sort(key=lambda nid: _order_key(plan, ordered_index, nid))
    return candidates


def next_ready(plan: PlanView, state: Mapping[str, str]) -> str | None:
    r = compute_ready(plan, state)
    return r[0] if r else None
