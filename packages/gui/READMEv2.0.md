GUI v2.0 — Stepwise Workspace Architecture

(Post G4.9 + G4.10A + G4.11 Root/Statistical Canonical Alignment + G5 Pattern Tool & UI Unification)

Overview

The GUI is a stepwise, contract-driven execution client.

It acts as a thin orchestration layer:

consumes API contracts
builds deterministic payloads
executes stages independently
renders artifact-driven outputs
exposes chaining explicitly

The system has evolved into:

route-driven
artifact-driven
contract-aligned
guided configuration
guided query UX
statistical visualization
query inline results
standalone analysis tools
interactive analysis layer
advanced statistical dashboard
canonical payload alignment
semantic breakout consistency
time-consistent visualization
dedicated dataset exploration
runtime statistical target alignment
statistical results full runtime parity
canonical query semantic alignment
backend-driven public intent catalog
deprecated metric visibility
query results semantic normalization
pattern-driven analysis tooling (G5)
visual pattern vs match comparison (G5)
workspace-level UI consistency (G5)
brand system introduction (SPADITOOLS)
Architectural Principles
1. Stepwise Execution Model

The GUI mirrors the orchestrator execution model:

Root        → /runs/root
Statistical → /runs/statistical
Query       → /runs/query
Pattern     → /runs/pattern

Each stage is:

isolated
explicitly triggered
independently observable

There is no implicit chaining.

Artifact references are explicit.

2. Contract-Driven UI

The GUI:

builds payloads
sends requests
renders responses

The GUI does NOT:

validate domain semantics
infer missing configuration
reconstruct pipelines
interpret query intent
reinterpret query intent
invent semantic aliases
hardcode runtime truth

The backend remains the only source of truth.

3. Strict Backend Alignment

The backend enforces strict schema validation:

extra = "forbid"

Implications:

missing field → INVALID_CONFIG
extra field → INVALID_CONFIG
wrong type → INVALID_CONFIG

Therefore:

The GUI must produce exact payload shape.

No legacy compatibility should be assumed.

Query Semantic Canonical Alignment

(Post G4.12C)

Problem Solved

Before G4.12C:

GUI still treated:

success_rate

as the primary query success metric.

This was semantically ambiguous because:

non failed ≠ true breakout

and the frontend still relied on partially hardcoded intent assumptions.

Canonical Query Semantics
Canonical Metric
true_breakout_rate

defined as:

breakout_outcome == true_breakout
Explicit Legacy Metric
non_failed_rate

defined as:

is_failed == False
Deprecated Compatibility Alias
success_rate

kept only for backward compatibility.

It is now explicitly deprecated.

The GUI reflects exactly this structure.

No semantic reinterpretation exists client-side.

Backend Public Intent Catalog
New Route
GET /query/public-intents

Used as runtime source of truth for query intent discovery.

Returned fields include:

intent_id
deprecated
replacement_intent_id
semantic_note
example_description
example_params

This guarantees:

public contract == executable runtime reality
Default Query Canonicalization

Default query changed from:

success_rate

to:

true_breakout_rate

with default params:

{
  "group_by": ["session"]
}
Deprecated Warning System

If query metadata contains:

{
  "deprecated_intent_id": "success_rate",
  "replacement_intent_id": "true_breakout_rate"
}

the GUI shows:

Deprecated metric detected → use true_breakout_rate
Semantic Result Order

Results are now shown in this order:

true_breakout_rate
non_failed_rate
success_rate

never the opposite.

Orchestrator Alignment Addendum
Canonical Query semantics ✅
Backend public intent catalog ✅
Deprecated metric visibility ✅
Statistical Results Visualization

(Post G4.5 → G4.11 + Full Runtime Statistical Alignment)

Evolution

From:

basic rendering
textual outputs

To:

full analytical dashboard
runtime-aligned statistical visualization
dedicated dataset page
target family classification
bucketizer-aware analysis
expanded interactive analysis layer
Artifact-Driven Rendering
artifactRef
→ manifest
→ outputs
→ CSV / parquet load
→ parsing
→ visualization

The UI never reconstructs results.

It only renders artifacts.

Runtime Statistical Alignment (G4.11)
Problem Solved

Before G4.11:

GUI Results rendered only a partial legacy interpretation of Statistical outputs.

After:

E2.1A — Capability Reintegration
E2.2B — Statistical Config Canonicalization
Verified Runtime Structure

Statistical runtime exposes:

100 runtime columns

Including:

Direct Targets

t1
t2

ATR Target Scans

t1_0_5ATR
t1_1_0ATR
t1_1_5ATR

Tick Scans

t2_12ticks
t2_20ticks
t2_30ticks
t2_50ticks

Clean Quant

is_clean_quant
clean_quant_label

Bucketizers

compression_bucket
delta_bucket
volume_bucket
atr_bucket
pre_bo_bucket
time_bucket

Derived Metrics

breakout_efficiency
range_atr_ratio
volume_atr_ratio
ml_distance_atr
pre_total_score
Target Classification System

Functions:

detectTargetColumns()
classifyTargetColumns()

Families:

Direct targets
ATR scans
Tick scans
Clean quant
Dataset Page (G4.10A)

Route:

/results/:toolId/:fingerprint/dataset
KPI System Upgrade

Metrics:

Events Analyzed
Target Levels
Avg Max Excursion
Avg Breakout Efficiency
Clean Quant Rate
Heatmap Upgrade

Volume × Delta surface:

normalized buckets
semantic labels
stable ordering
Breakout Semantic Truth

Canonical field:

breakout_outcome

NOT:

success_rate
is_failed

Values:

true_breakout
false_breakout
failed_follow_through
🆕 ROOT / STATISTICAL UI REFACTOR (G4.11 UI LAYER)
Root Stage Layout Refactor
Goal

Introduce clear UI hierarchy:

Dataset = primary input
Configuration = domain logic
Saved Config = utility tool
Layout Model
ROOT STAGE
│
├── Dataset (PRIMARY INPUT)
├── Configuration (DOMAIN LOGIC)
├── Saved Config (UTILITY PANEL)
└── Payload Preview
Dataset vs Saved Config Split
Dataset: dominant input layer
Saved Config: lightweight utility panel
UI Design Rules Introduced
Component	Role	Weight
Dataset	Input core	HIGH
Configuration	Domain logic	HIGH
Saved Config	Utility	LOW
Bucketizers	Feature eng.	MEDIUM
Payload preview	Debug	LOW
Known Limitations
Saved Config still slightly too visible
Statistical stage not aligned yet
inline styles still present
Stack/Grid inconsistency remains
Final Rule

UI must reflect execution hierarchy:

Dataset → Configuration → Utility → Artifact
=========================================
🆕 G5 — PATTERN TOOL + UI UNIFICATION
=========================================
Pattern Tool Introduction

New standalone execution stage:

Pattern → /runs/pattern

Purpose:

define candle-based templates
search historical matches
visually compare pattern vs real data
Pattern Overlay System
Objective

Render:

detected match (real data)
configured pattern (synthetic)

→ in the SAME chart

Overlay Mechanics

Pipeline:

Manual Pattern → normalization → scaling → vertical offset → overlay rendering
Key Properties
same time alignment
same number of candles
normalized price scale
visual separation (vertical offset)
Result

Immediate visual comparison:

Pattern (expected)
vs
Match (real)
Pattern Builder UI
Structure
Pattern Template (CORE)
│
├── Pattern length
├── Candle cards (scrollable)
│   ├── Direction
│   ├── Body / Wick / Volume / Delta
│   └── Close position
Features
inline candle preview
deterministic configuration
horizontal builder
incremental controls (+ / -)
Configuration Layout Alignment

Pattern Tool now follows same hierarchy as Root:

Dataset
Pattern Mode
Pattern Template (CORE)
Matching Sensitivity
Chart Context
Design System Alignment (G5)
Problem

Inputs were:

browser default
visually inconsistent
breaking dark theme
Solution

Unified styling:

background → var(--panel)
border     → var(--border)
color      → var(--text)
Result
consistent inputs across:
Root
Statistical
Query
Pattern
Workspace Navigation Refactor
Before
Stepwise Workspace title
vertical layout
After
tabs only (Root / Statistical / Query)
left aligned
minimal UI noise
Branding System — SPADITOOLS
Introduced

Global header identity:

SPADITOOLS

with:

custom logo (crossed swords)
dark UI integration
Removed
"Statistical Analysis GUI"
"V1 — Foundation"
Goal

Move from:

internal tool feeling

to:

product-grade interface
Final System State

The system is:

✔ structurally correct
✔ functionally stable
✔ visually coherent across stages
✔ pattern-analysis enabled
✔ contract-aligned end-to-end

⚠ inline styles still present
⚠ design system not fully extracted
⚠ no global component library yet