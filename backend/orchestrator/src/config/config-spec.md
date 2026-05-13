# O2 — Config Schema v1 (Draft Spec M1)

## 1. Purpose

This spec defines the **Run Config** contract for Orchestrator — Foundation.

The Config is the **declarative intention of a run**. It is used to:

- Uniquely identify run intention (via fingerprint)
- Drive cache invalidation (disk-first, O3)
- Ensure reproducibility and idempotence

The Config MUST NOT contain:

- Runtime state (status, progress, timings, logs)
- Results or computed data
- Storage / filesystem references (paths, bucket names, URIs)
- Artifact / Manifest data (O1) or any Manifest fingerprint
- Run identifiers or timestamps
- GUI bindings

Boundary principle: **Config describes; Pipeline plans; Runtime executes; Storage materializes; Manifest describes artifacts.**

## 2. Versioning policy (frozen)

Root field:

- `config_version` (required): string `"major.minor"`.

Rules:

- Format: `"X.Y"` where `X` and `Y` are non-negative integers (no leading/trailing spaces).
- Validator MUST accept `1.*`.
- Validator MUST reject `major != 1`.
- Minor bumps (`1.(n+1)`) can only add **optional** fields (forward compatible).
- Major bumps (`2.0+`) are breaking.

## 3. Design goals / invariants

- JSON-serializable only, in the **strict JSON domain** (objects, arrays, strings, numbers, booleans, null)
  - No `NaN` / `Infinity` / `-Infinity`
  - No Python-only types (e.g., `tuple`, `set`, `bytes`, `datetime`, custom classes)
- Deterministic (same semantic config ⇒ same canonical form ⇒ same fingerprint)
- Strict-by-default validation
- Forward-compatible within 1.x (optional additive changes only)
- No implicit defaults that would alter fingerprint (“no invisible defaults”)
- Unknown fields MUST be rejected when `strict=True` (default)

Important nuance:

- Some sub-objects (`parameters`, `resources`, `metadata`) are intentionally **free-form maps** whose *keys are user-defined*.
  - This does not violate strictness: the field itself is known and validated, and its values are constrained to JSON types.

## 4. Config Schema v1.0

### 4.1 Top-level object

The config is a JSON object with the following keys.

**Required:**

- `config_version`: string, see §2
- `pipeline`: object, see §4.2
- `parameters`: object (free-form), see §4.3

**Optional:**

- `resources`: object (free-form), see §4.4
- `metadata`: object (free-form), see §4.5

**Forbidden:**

- Any other top-level keys when `strict=True`.

### 4.2 `pipeline` (declarative pipeline intent)

Purpose: declare **what** pipeline should be executed, without encoding runtime details.

`pipeline` is an object with:

**Required:**

- `id`: string  
  A **stable identifier** of the pipeline definition (e.g., `"etl_v1"`, `"train_model"`).

  **Stability / regex constraint (frozen):**
  - MUST match: `^[a-z][a-z0-9_.-]{2,63}$`
  - Implies: lowercase only, no whitespace, no slashes/paths, length 3–64

**Optional:**

- `revision`: string  
  A pipeline revision hint (e.g., `"2026-02-11"` or `"v3"`). O2 does not interpret it; it is part of intent and therefore part of the fingerprint if provided.
- `steps`: array of objects (see below)  
  A minimal, structural outline of the pipeline. This is intentionally lightweight and does not commit to a specific DAG engine.

**Constraints:**

- Unknown keys inside `pipeline` MUST be rejected in strict mode.

#### 4.2.1 `pipeline.steps` (optional)

If provided, `steps` is an array of step objects with:

**Required:**

- `step_id`: string  
  Unique within the `steps` array.
- `op`: string  
  Symbolic operation name (opaque to config layer).

**Optional:**

- `with`: object (free-form)  
  Operation arguments, JSON-serializable.
- `needs`: array of strings  
  Declares dependencies by referencing other `step_id` values. This is *structural only* (no scheduling semantics in O2).

**Constraints:**

- Unknown keys inside step objects MUST be rejected in strict mode.
- If `steps` is provided, it MUST be **non-empty**.
- `needs` values MUST refer to existing `step_id`s (if `steps` is present).
- `step_id` MUST be unique (case-sensitive).

Rationale:
- `pipeline.id` is the minimal “what to run”.
- `revision` is an explicit part of intent; it avoids hidden coupling to external pipeline registries.
- `steps` is optional because some pipelines may be referenced only by `id`; when present, it enables deterministic intent capture without introducing runtime/DAG coupling.

### 4.3 `parameters` (free-form declarative inputs)

Purpose: capture **run parameters** that influence outputs.

- Type: JSON object (map)
- Keys: user-defined strings
- Values: any JSON value (including nested objects/arrays)

Constraints:

- `parameters` MUST be present (may be empty `{}`).
- Values MUST be JSON-serializable.
- The config layer MUST NOT add defaults into `parameters`.

Rationale:
- Parameters are often domain-specific. Strictness is maintained at the field boundary, not on user-defined parameter names.

### 4.4 `resources` (optional free-form references)

Purpose: declare **logical resources** used by the run, without storage binding.

- Type: JSON object (map)
- Keys: user-defined strings (e.g., `"dataset"`, `"catalog"`)
- Values: any JSON value (commonly identifiers like `"ds_123"`, `"imdb_reviews"`, `"s3://..."` is NOT allowed if treated as storage reference; use logical ids instead)

Constraints:

- Values MUST be JSON-serializable.
- The config layer MUST NOT resolve resources or interpret them.

Rationale:
- Allows reproducibility (“which dataset id?”) without coupling config to storage or filesystem.

### 4.5 `metadata` (optional free-form annotations)

Purpose: attach non-operational, declarative annotations that still belong to run intention.

- Type: JSON object (map)
- Keys: user-defined strings
- Values: JSON values

Examples: `{"owner": "team-x", "purpose": "backfill", "ticket": "OPS-1234"}`

Constraints:

- No runtime timestamps.
- No generated run ids.

Rationale:
- Supports auditability and organization without affecting runtime behavior beyond intent identification.

Normative note (frozen):
- `metadata`, if present, **contributes integrally** to the Config fingerprint (no filtering / whitelisting at the config layer).

Important (frozen): **`metadata` contributes integrally to the fingerprint**, exactly as provided (after canonical JSON normalization). Do not place volatile runtime values here.

## 5. Validation rules (M1 scope)

A validator MUST at minimum enforce:

1. Top-level must be a JSON object.
2. `config_version` exists and matches `"X.Y"` and `major == 1`.
3. Required top-level fields exist: `pipeline`, `parameters`.
4. Type checks:
   - `pipeline` object; `pipeline.id` string
   - `parameters` object
   - optional `resources` / `metadata` objects
5. Strict mode (default): unknown fields at top-level and inside `pipeline` / `steps` are errors.
6. If `pipeline.steps` exists:
   - must be an array of objects
   - each step has `step_id` (string) and `op` (string)
   - `step_id` unique
   - `needs` (if present) is an array of strings and references known `step_id`s

Non-goals for validator (explicitly out of scope in O2/M1):

- No schema for `parameters/resources/metadata` keys (free-form)
- No interpretation of `op` names
- No coupling to runtime adapters, storage, or O1 manifest

## 6. Canonical JSON requirement (for fingerprinting)

The fingerprint (M3) MUST be computed on the **normalized / canonical** JSON representation of the config.

Canonicalization requirements (normative):

- Objects:
  - keys MUST be sorted lexicographically (Unicode code point order, i.e., Python’s default `sorted()` on strings)
  - values are canonicalized recursively
- Arrays:
  - order is preserved (arrays are ordered by definition)
  - each element is canonicalized recursively
- JSON serialization:
  - MUST be UTF-8
  - MUST use a JSON representation with:
    - sorted keys (`sort_keys=True`)
    - no insignificant whitespace (MUST be exactly `separators=(",", ":")`)
    - no NaN/Infinity (reject non-JSON numbers)
  - MUST NOT mutate the input object

Frozen canonical form: the canonical JSON bytes are produced by `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")`.

This guarantees:

- same config → same fingerprint
- different key order → same fingerprint
- different whitespace → same fingerprint

## 7. Dummy example config (v1.0)

```json
{
  "config_version": "1.0",
  "pipeline": {
    "id": "example_pipeline",
    "revision": "v1",
    "steps": [
      {
        "step_id": "extract",
        "op": "extract_records",
        "with": { "limit": 1000 }
      },
      {
        "step_id": "transform",
        "op": "clean_records",
        "needs": ["extract"],
        "with": { "drop_nulls": true }
      },
      {
        "step_id": "load",
        "op": "write_table",
        "needs": ["transform"],
        "with": { "table": "clean_table" }
      }
    ]
  },
  "parameters": {
    "seed": 42,
    "mode": "dry_run"
  },
  "resources": {
    "dataset_id": "ds_123",
    "source_system": "crm_prod"
  },
  "metadata": {
    "owner": "team-data",
    "purpose": "example"
  }
}
```

## 8. Notes for 1.x evolution

Allowed in 1.x minor bumps:

- Add new **optional** top-level fields (e.g., `tags`)
- Add new **optional** fields inside `pipeline` or `steps`

Not allowed in 1.x:

- Changing meaning/type of an existing field
- Making an optional field required
- Introducing implicit defaults that change fingerprint

