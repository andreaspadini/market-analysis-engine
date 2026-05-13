# O4B — Engine Wiring Adapter (Controlled)
## M1 — Invarianti (Freeze)

### Boundary invariants (non negoziabili)
1. Tutto il codice O4B vive in `packages/orchestrator/`.
2. O4B **non** modifica O4A (Planner, DAGModel, ExecutionPlan).
3. O4B **non** importa `packages/core/*` (Core è raggiunto solo via `CorePort`).
4. Core non conosce Orchestrator (nessun import inverso; ACL in Orchestrator).
5. Storage: O4B userà **solo** O3 `ArtifactStorePort` (in M2+). Nessuna scrittura diretta a filesystem.

### Execution invariants
6. Esecuzione **sequenziale** su ordered plan (nessuna concorrenza).
7. O4B **non** introduce logica DAG: niente scheduling, topological sort, resolution di dipendenze.
   L’ordine è già deciso dal Planner (O4A) e consumato “as-is”.
8. Cache-hit vs rebuild:
   - la decisione di cache-hit deriva da input data-only (node_id -> bool),
     tipicamente ottenuto interrogando O3.
   - se cache-hit, O4B evita invocazione Core.
   - O4B non reinterpreta il planner e non introduce euristiche quantitative.

### Data-only invariants
9. `CoreInvocation`, `CoreResult`, `ExecutionItem`, `ExecutionOutcome` sono data-only:
   - nessuna logica quantitativa
   - nessuno stato runtime
   - contenuti JSON-serializzabili (responsabilità del chiamante garantire la serializzabilità)

### Non-goals (espliciti)
- Job queue / worker pool
- Retry/backoff policy avanzata
- Event streaming
- API layer
- GUI integration
