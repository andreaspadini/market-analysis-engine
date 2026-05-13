from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING

# For type-checkers: always expose real class names (not runtime aliases).
if TYPE_CHECKING:
    # If your repo exposes these elsewhere, point to the canonical location.
    # This is ONLY for static analysis; runtime import happens below.
    from orchestrator.types import ProducedArtifact, CoreResult  # type: ignore
else:
    try:
        # Runtime reuse if already present
        from orchestrator.types import ProducedArtifact, CoreResult  # type: ignore
    except Exception:
        @dataclass(frozen=True)
        class ProducedArtifact:
            name: str
            path: str  # absolute path inside run_dir

        @dataclass(frozen=True)
        class CoreResult:
            success: bool
            produced_artifacts: list[ProducedArtifact]
            logs_path: Optional[str]
            execution_metadata: dict[str, Any]

