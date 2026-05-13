from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True, slots=True)
class RunExecutionContext:
    """
    C4: internal run context (data-only).

    Guardrails:
    - Not a DTO (not in O6).
    - Not persisted.
    - Not serialized.
    - Not used by planner (O4A frozen).
    """

    # O2 fingerprint of validated config (audit/plan_id)
    config_hash: str

    # runtime engine version (run-level string)
    engine_version: str

    # Optional debug-only fields (internal)
    input_hash: Optional[str] = None
    artifact_identity_hash: Optional[str] = None
    extra: Optional[Mapping[str, Any]] = None

