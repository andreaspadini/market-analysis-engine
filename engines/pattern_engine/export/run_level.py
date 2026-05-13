from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .export_engine import ExportArtifacts, export_pattern_run


def export_run_level(
    *,
    output_dir: str | Path,
    engine_version: str,
    run_id: str,
    pattern_definition: Any,
    matches: list[Any],
    stats: Any,
    bars_df: Any,
    config_snapshot: Mapping[str, Any],
    export_parquet: bool = False,
    export_schema_json: bool = False,
) -> ExportArtifacts:
    """
    Run-level export API (Cap.9 public contract).

    Stable, discoverable wrapper around export_pattern_run.
    """
    return export_pattern_run(
        frozen_root=Path(output_dir),
        engine_version=engine_version,
        run_id=run_id,
        pattern_definition=pattern_definition,
        matches=matches,
        stats=stats,
        bars_df=bars_df,
        config_snapshot=config_snapshot,
        export_parquet=export_parquet,
        export_schema_json=export_schema_json,
    )
