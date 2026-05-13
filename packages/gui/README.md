GUI v2.0 — Stepwise Workspace Architecture (Post G4.10A)

This package contains the full GUI execution client for the orchestrator runtime.

The system has evolved from a simple run launcher into a fully stepwise, artifact-driven, contract-aligned execution workspace.

It now includes:

Design System & Layout Foundation (G1)
Run Creation + O6 Submit Integration (G2 / G2.3 / G2.4)
Run Status Polling (G3.1)
Results Snapshot Fetch (G3.2)
Results Visualization Layer (G3.3)
Stepwise Workspace Architecture (G4.3)
Root Visualization Layer (G4.4)
Balance Visualization Refinement (G4.5)
Query Visualization Layer (G4.6)
Pattern Tool + Workspace Navigation Refactor (G4.7 / G4.7A)
Statistical Visualization Layer (G4.9)
Root Runtime Canonical Alignment (G4.10)
Root Breakout Canonical GUI Completion (G4.10A)
Scope
G1 — Foundation
Includes
App shell (header, sidebar, layout)
Stable routing
Neutral design system
Layout primitives
Print-safe CSS foundation
Skeleton loader
UI-level ErrorBoundary
Explicitly excludes
Engine logic
Runtime orchestration
Planner logic
Global state manager
API integration (initially)
G2 — Run Creation + O6 Integration
Includes
Production runner (apps/gui-web)
Run Creation page (/run/new)
Preset management (localStorage)
HTTP integration with O6 (POST /runs)
Provider-based baseUrl injection
Redirect to /results/:runId
Excludes
Polling
Streaming
Artifact rendering
Planner logic
Runtime orchestration
G2.3 — Full Parameter Form Rendering (DTO-Driven)
Includes
Full PipelineParametersV1 state model
Strict DTO mapper
Structured parameter sections:
Dataset
Root Engine
Statistical Engine
Query Engine
Pattern Engine (Pattern Tool only)
Strict preset storage (DTO JSON)
Strict O6 contract submission
Excludes
Planner logic
Runtime logic
Engine logic
Hashing
Artifact rendering

GUI acts exclusively as a declarative contract builder.

G2.4 — Configuration Usability & Execution Readiness
Includes
Single source of truth (RunCreationState)
Removal of fragmented local state
Explicit state injection into sections
Correct UI → DTO wiring
Reliable CTA gating
Preset lifecycle fully validated
UX improvements
Reduced manual errors
Controlled inputs
Clear required vs optional separation
Validated behavior
Full configuration → CTA enabled
Submit → POST /runs triggered
Navigation flow executed
Known limitation

Requires:

VITE_O6_BASE_URL
G3.1 — Run Status & Polling
Includes
GET /runs/{run_id}
Polling (2500ms)
Stop on terminal state
Cleanup
Excludes
Streaming
WebSockets
Retry logic
Artifact rendering
G3.2 — Results Snapshot Fetch
Includes
GET /runs/{run_id}/results
Fetch only on SUCCEEDED
Single fetch
ResultsSnapshotView
Excludes
Charts
Aggregations
Transformations
G3.3 — Results Visualization Layer
Completed
Root View
Statistical View
Query View
Rules
No interpretation
No derived logic
No enrichment
G4.3 — Stepwise Workspace Architecture

Introduces the new workspace model:

/workspace → stepwise execution
Stages
Root → /runs/root
Statistical → /runs/statistical
Query → /runs/query
Principles
stage isolation
explicit execution
artifact-driven chaining
contract-driven UI
no shared implicit state

GUI becomes:

thin orchestration client
G4.4 — Root Visualization Layer

Introduces external, artifact-driven visualization for Root.

New Routes
/workspace/root/:toolId/:fingerprint/results
/workspace/root/:toolId/:fingerprint/charts
Root Results Page

Includes:

Manifest read
Artifact CSV fetch
Summary metrics:
Total
Failed
Success
Up
Down
Summary chart
Breakout table
Minimal UI
Failed highlighting
First 100 rows
Root Charts Page

Includes:

Data sources
root_input_dataset.csv
root_output_dataset.csv

resolved via:

GET /manifests/{tool_id}/{fingerprint}
GET /artifacts/{tool_id}/{fingerprint}/{relpath}
Visualization
OHLC candlestick chart
breakout overlay
failed breakout overlay
initial balance overlay

Library:

lightweight-charts
G4.5 — Balance Visualization Refinement
Includes
improved balance rendering
better balance boundaries visualization
midpoint alignment
cleaner breakout/balance relationship
chart rendering stabilization

GUI remains artifact-driven only.

No engine reconstruction introduced.

G4.6 — Query Visualization Layer

Introduces inline Query execution results and external visualization support.

Includes
guided query UX
intent catalog
inline query execution rendering
external query result visualization
route-driven query results
public intent exposure
query result isolation from runtime execution
Principles
query is contract-driven
GUI does not interpret intent semantics
backend remains source of truth
G4.7 / G4.7A — Pattern Tool + Workspace Navigation Refactor

Introduces standalone Pattern Tool execution and dedicated visualization.

Includes
standalone Pattern Tool execution
dedicated workspace navigation
Pattern Tool card
Pattern result visualization
pattern artifact routing
artifact-driven chart visualization
OHLC dataset exposure for Pattern drill-down
Alignment

Fully aligned with:

O7.12 + O7.13

real engine exports.

No fake visualization.

No synthetic reconstruction.

G4.9 — Statistical Visualization Layer

Introduces artifact-driven visualization for Statistical stage.

Includes
statistical artifact loading
statistical result table rendering
bucketizer metadata visualization
grouped aggregation rendering
breakout outcome alignment
canonical statistical payload visualization
explicit Root → Statistical chaining
Guarantees

GUI renders:

only backend-produced outputs

without recomputation.

G4.10 — Root Runtime Canonical Alignment

Root GUI aligned with backend canonical runtime payload.

Includes

Removal of legacy payload structure:

dataset.date_range
config.engine
config.duration
config.volume
config.delta
legacy breakout blocks
legacy export blocks
legacy rotation blocks

Replacement with canonical runtime payload:

dataset.start_date
dataset.end_date
dataset.instrument
dataset.timeframe

config.rotations
config.balance
config.breakout
config.session_levels

Strict backend validation compatibility:

extra = forbid

No legacy drift remains.

G4.10A — Root Breakout Canonical GUI Completion

Completes the canonical Breakout GUI exposure.

Includes
Structural repair
full JSX repair
Grid / Stack / Collapsible stabilization
removal of broken nesting
compile-safe RootWorkspaceCard
Rotation alignment
min_rotation_bars
whipsawBars
corrected minRotationAmplitude
corrected minRotationAmplitudeMicro
Breakout completion

Reintroduced full canonical controls for:

Strength normalization
ATR
Volatility filter
Follow-through
Placeholder removal

Removed all temporary invalid blocks:

Keep existing block unchanged here
Validation

Verified with:

npx tsc --noEmit

result:

0 errors

Breakout is now fully canonical and production-safe.

Project Structure
packages/gui/
src/

app/
pages/
components/
features/

runCreation/
runresults/
workspace/

api/

apps/gui-web/
Routes
/run/new
/results/:runId

/workspace
/workspace/root
/workspace/statistical
/workspace/query
/workspace/pattern

/workspace/root/:toolId/:fingerprint/results
/workspace/root/:toolId/:fingerprint/charts
API Layer Architecture
createHttpClient
↓
createO6Client
↓
<ApiProvider>
↓
useApi()
Rules
no retries
no interceptors
explicit injection
Performance Model
Execution
poll → state → fetch → render
Visualization
artifact fetch → parse → render
No
streaming
live sync
DEV Configuration
apps/gui-web/.env.local
VITE_O6_BASE_URL=http://127.0.0.1:8000

Required:

backend running
CORS enabled
Architectural Boundaries

GUI does NOT:

interpret engine semantics
compute identity
reconstruct planner logic
execute runtime
mutate execution state
infer hidden config
simulate backend logic

GUI is:

pure contract-driven artifact consumer
Status
G1 — Closed
G2 — Closed
G2.3 — Closed
G2.4 — Closed
G3.1 — Closed
G3.2 — Closed
G3.3 — Closed
G4.3 — Closed
G4.4 — Closed
G4.5 — Closed
G4.6 — Closed
G4.7 — Closed
G4.7A — Closed
G4.9 — Closed
G4.10 — Closed
G4.10A — Closed