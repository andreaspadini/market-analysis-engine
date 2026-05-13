from pathlib import Path
from datetime import datetime
import pandas as pd
import json

from engines.root_engine.enrichments.market_levels.enrich_breakouts import (
    enrich_breakouts_with_levels,
)


def export_breakouts_csv(
    breakouts,
    raw_config,
    bars,
    timeframe: str = "5m",
):
    if not breakouts:
        print("[EXPORT] Nessun breakout da esportare.")
        return

    # ==================================
    # MARKET LEVELS ENRICHMENT
    # ==================================
    try:
        enriched_rows = enrich_breakouts_with_levels(
            breakouts=breakouts,
            bars=bars,
            config=raw_config,
        )
    except Exception as e:
        print("[LEVELS ENRICHMENT ERROR]", str(e))
        enriched_rows = [b.model_dump(mode="json", exclude_none=False) for b in breakouts]

    df = pd.DataFrame(enriched_rows)
    df["schema_version"] = "1.1.0"

    # ==================================
    # OUTPUT PATH RESOLUTION
    # ==================================

    artifact_output_path = raw_config.get("artifact_output_path")

    if artifact_output_path:

        # -------------------------------
        # ORCHESTRATOR ARTIFACT MODE
        # -------------------------------
        artifact_root = Path(artifact_output_path)

        output_dir = artifact_root / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "root_output_dataset.csv"

        # Manifest path
        manifest_path = artifact_root / "manifest.json"

    else:

        # -------------------------------
        # LOCAL DEBUG MODE
        # -------------------------------
        output_dir = Path("exports_production")
        output_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        tf = raw_config.get("dataset", {}).get("timeframe", timeframe)

        output_file = output_dir / f"breakouts_v0.2.1_{date_str}_{tf}.csv"

        manifest_path = None

    # ==================================
    # SAVE DATASET
    # ==================================
    df.to_csv(output_file, index=False)

    # ==================================
    # MANIFEST CREATION (O3 STORE)
    # ==================================

    if manifest_path:

        manifest = {
            "tool_id": "root_engine",
            "schema_version": "1.1.0",
            "artifacts": [
                {
                    "name": "root_output_dataset.csv",
                    "path": "outputs/root_output_dataset.csv",
                    "type": "dataset/csv"
                }
            ]
        }

        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    print(f"[EXPORT PRODUZIONE] File creato: {output_file}")