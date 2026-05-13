Artifact Manifest Spec v1

Orchestrator — Foundation (O1)

Status: Frozen (v1)
Scope: packages/orchestrator
Ownership: Orchestrator — Foundation

1. Purpose

The Artifact Manifest defines the minimal, stable and deterministic contract describing artifacts materialized by the Orchestrator.

The Manifest:

Describes what was materialized

Does not describe how it was stored

Does not expose storage backend details

Does not reference DAG, Core engine, or runtime internals

Is not a cross-layer DTO

Principle:

The DAG plans.
The runtime executes.
The storage materializes.
The Manifest describes.

2. Versioning Policy (Frozen)

Field:

manifest_version: "major.minor"


Rules:

Must match regex: ^\d+\.\d+$

Major must be 1

Validator accepts 1.*

Any other major is rejected

Evolution policy:

Change Type	Allowed in 1.x
Add optional field	✅
Add required field	❌
Change field type	❌
Remove field	❌
Semantic change	❌
Breaking structure change	v2 required
3. Manifest Structure (v1)
{
  "manifest_version": "1.0",
  "producer": {
    "tool_id": "csv-writer",
    "tool_version": "2.3.1"
  },
  "outputs": [
    {
      "relpath": "runs/2026-02-11/report.csv",
      "bytes": 1048576,
      "checksum": {
        "alg": "sha256",
        "value": "..."
      }
    }
  ]
}

4. Field Definitions and Invariants
4.1 manifest_version

Type: string
Required: yes

Must match ^\d+\.\d+$
Major must equal 1.

Purpose:

Enables multi-version parsing

Supports clean v2 migration

Ensures deterministic validation path

4.2 producer

Structure:

producer:
  tool_id: string
  tool_version: string


Required: yes

4.2.1 tool_id

Must be a stable identifier.

It identifies the component that physically materializes the artifact.

It must NOT:

Be a marketing name

Depend on runtime configuration

Identify the DAG

Identify the quantitative engine

Recommended format (not enforced syntactically in v1):

kebab-case (e.g. csv-writer)

dotted.namespace (e.g. orchestrator.runner)

4.2.2 tool_version

String identifying the version of the materializing component.

Purpose:

Audit

Reproducibility

Forensic debugging

4.3 outputs

Type: non-empty list
Required: yes

Invariant:

len(outputs) >= 1


Each item:

relpath: string
bytes: integer >= 0
checksum:
  alg: "sha256"
  value: string

4.3.1 relpath

Must be relative to store root.

Forbidden:

Leading /

Windows drive prefix (C:)

Backslashes (\)

Path traversal (..)

Empty segments (//, trailing slash)

Purpose:

Security

Determinism

Backend independence

All relpath values must be unique within the manifest.

4.3.2 bytes

Integer ≥ 0
Represents materialized file size in bytes.

Purpose:

Integrity check

Audit consistency

4.3.3 checksum

Structure:

checksum:
  alg: "sha256"
  value: string


In v1:

Only "sha256" is allowed.

value must be non-empty.

Cryptographic verification is not part of structural validation.

Future algorithms require minor version update.

5. JSON Persistence Format (Frozen)

The manifest is persisted as:

JSON

UTF-8 encoded

Canonical / deterministic

Canonical encoding requirements:

json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)


Implications:

Same manifest object → identical byte representation

No whitespace variability

Deterministic ordering

Canonical form may be enforced.

6. Validator Modes

Function signature:

validate_manifest(data: dict, strict: bool = True)


Behavior:

Mode	Unknown Fields
strict=True (default)	Error
strict=False	Allowed (forward-compatibility within 1.x)

Validator is:

Pure function

Stateless

Side-effect free

Filesystem independent

7. Round-Trip Guarantees (M3)

The following is guaranteed:

Serialize → Validate → Deserialize preserves structure

Canonical encoding is deterministic

Structural validity is independent of storage implementation

Optional filesystem consistency checks do not introduce O3 coupling

8. Scalability Analysis (M4)
8.1 Multi-Tool Support

producer.tool_id enables multiple independent materializers.

8.2 Multi-Output Support

outputs list supports large artifact bundles.

Validator complexity: O(n).

8.3 High Cardinality

Relpath uniqueness is enforced in O(n).

No backend assumptions exist.

9. Non-Goals (Explicit)

Manifest v1 does NOT contain:

DAG ID

Run ID

Timestamp

Core configuration

Storage backend ID

Retention policy

Signing block

Content addressing

Multiple checksums

These belong to future evolution or separate concerns.

10. Migration Path to v2

Breaking changes requiring v2:

Multi-algorithm checksums

Signed manifests

Content-addressable artifacts

Storage tier metadata

Chunked artifact trees

manifest_version guarantees clean multi-parser support.

11. Stability Statement

Artifact Manifest Spec v1 is:

Minimal

Deterministic

Backend-agnostic

Strictly versioned

Long-term stable

O1 is formally complete upon acceptance of this document.