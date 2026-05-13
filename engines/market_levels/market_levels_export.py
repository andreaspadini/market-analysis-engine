import os
import csv
from collections import defaultdict
from typing import List, Dict, Any

from engines.market_levels.session_levels_schema import (
    SessionLevelsModel
)


def export_session_levels_csv(
    levels: List[SessionLevelsModel],
    raw_config: Dict[str, Any],
) -> None:
    if not levels:
        print("[SESSION LEVELS EXPORT] Nessun livello da esportare.")
        return

    export_cfg = raw_config.get("export", {})
    export_dir = export_cfg.get("output_dir", "exports_levels")
    filename_prefix = export_cfg.get("filename_prefix", "market_levels")

    os.makedirs(export_dir, exist_ok=True)

    # 🔹 raggruppo i livelli per DATA
    levels_by_date = defaultdict(list)
    for lvl in levels:
        levels_by_date[lvl.date].append(lvl)

    version = levels[0].version if levels else "unknown"

    for d, date_levels in sorted(levels_by_date.items()):
        date_str = d.strftime("%Y-%m-%d")
        filename = f"{filename_prefix}_v{version}_{date_str}.csv"
        filepath = os.path.join(export_dir, filename)

        fieldnames = list(date_levels[0].model_dump().keys())

        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for row_model in date_levels:
                row = row_model.model_dump()
                # serializzo dict/list come string
                for k, v in row.items():
                    if isinstance(v, (dict, list)):
                        row[k] = str(v)
                writer.writerow(row)

        print(f"[SESSION LEVELS EXPORT] Livelli esportati in: {filepath}")

