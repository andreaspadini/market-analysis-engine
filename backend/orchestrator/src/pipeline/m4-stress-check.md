# O4A — M4 Stress & Purity Check (Summary)

This package is **pure planning logic** (no runtime execution).

## Checks (non-negotiable invariants)
- No imports from `adapters/*` (pipeline layer is standalone).
- No filesystem access, no network calls, no environment dependence.
- No mutation of input structures; outputs are immutable/frozen where required.
- Deterministic tie-break rule: **lexicographic ascending `node_id`** everywhere.
- Complexity: algorithms are linear in graph size **O(V + E)**.
- Determinism tests: repeated runs produce identical ordering and `plan_id`.

## Scope
- DAG model + builder + topo sort
- Pure planner producing `ExecutionPlan` (frozen + serializable)

