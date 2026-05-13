from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_adapter import BaseAdapter, RunPaths
from .core_types import ProducedArtifact


class PatternCliAdapter(BaseAdapter):
    """
    Pack:
      python -m pattern_engine.scripts.run_pattern_engine
        --config <config.yaml>
        --output-dir <dir>
        --parquet
        --schema
        --run-id INTEGRATION_PACK

    Output root under <output-dir>/pattern_engine_v0.1.0/
      matches/*.csv  -> exactly 1
      stats/*.csv    -> exactly 1

    C1-derived naming:
      pattern_matches.v0_1_0.json
      pattern_stats.v0_1_0.json
    """

    RUN_ID = "INTEGRATION_PACK"
    OUT_ROOT = "pattern_engine_v0.1.0"

    def adapter_id(self) -> str:
        return "pattern_engine_cli"

    def prepare_run_dir(self, run_paths: RunPaths, input_payload: Any) -> None:
        """
        Expect dict input_payload with:
          - bars_parquet_path: str
          - config_yaml_path: str

        We stage both inside run_dir to keep execution isolated/deterministic.
        """
        if not isinstance(input_payload, dict):
            raise ValueError("Pattern adapter expects dict input_payload")

        bars = input_payload.get("bars_parquet_path")
        cfg = input_payload.get("config_yaml_path")
        if not bars or not cfg:
            raise ValueError("Missing required keys: bars_parquet_path, config_yaml_path")

        self._copy_in_run_dir(run_paths, Path(bars), "input/bars_clean.parquet")
        self._copy_in_run_dir(run_paths, Path(cfg), "input/pattern_config.yaml")

    def build_command(self, run_paths: RunPaths, *, timeout_s: int, extra_args: list[str]) -> list[str]:
        cfg = (run_paths.run_dir / "input" / "pattern_config.yaml").resolve()
        out_dir = run_paths.output_dir.resolve()

        cmd = [
            "python",
            "-m",
            "pattern_engine.scripts.run_pattern_engine",
            "--config",
            str(cfg),
            "--output-dir",
            str(out_dir),
            "--parquet",
            "--schema",
            "--run-id",
            self.RUN_ID,
        ]
        cmd.extend(extra_args)
        return cmd

    def expected_outputs(self, run_paths: RunPaths) -> list[str | Path]:
        # Used only for reference; capture is enforced in override (exactly-1 per category).
        return [
            f"output/{self.OUT_ROOT}/matches/*.csv",
            f"output/{self.OUT_ROOT}/stats/*.csv",
        ]

    # --- capture: enforce exactly-1 and produce two official artifacts ---

    def _capture_and_normalize_outputs(self, run_paths: RunPaths) -> list[ProducedArtifact]:
        # Expand per-category to enforce exactly-1 deterministically.
        matches_glob = run_paths.run_dir / "output" / self.OUT_ROOT / "matches" / "*.csv"
        stats_glob = run_paths.run_dir / "output" / self.OUT_ROOT / "stats" / "*.csv"

        matches = sorted(matches_glob.parent.glob(matches_glob.name))
        stats = sorted(stats_glob.parent.glob(stats_glob.name))

        # Guardrail: outputs must remain inside run_dir
        matches = [self._assert_within_run_dir(run_paths, p) for p in matches]
        stats = [self._assert_within_run_dir(run_paths, p) for p in stats]

        if len(matches) != 1:
            raise ValueError(f"Expected exactly 1 matches CSV, got {len(matches)}: {matches}")
        if len(stats) != 1:
            raise ValueError(f"Expected exactly 1 stats CSV, got {len(stats)}: {stats}")

        from . import base_adapter as ba  # reuse strict CSV->JSON + deterministic dump

        produced: list[ProducedArtifact] = []

        # matches -> pattern_matches.v0_1_0.json
        rows_m = ba._load_csv_as_json_strict(matches[0])
        rows_m = ba._remove_runtime_fields(rows_m)
        s_m = ba._json_dumps_deterministic(rows_m)
        p_m = self._assert_within_run_dir(run_paths, run_paths.output_dir / "pattern_matches.v0_1_0.json")
        with p_m.open("w", encoding="utf-8", newline="\n") as f:
            f.write(s_m)
            f.write("\n")
        produced.append(ProducedArtifact(name=p_m.name, path=str(p_m)))

        # stats -> pattern_stats.v0_1_0.json
        rows_s = ba._load_csv_as_json_strict(stats[0])
        rows_s = ba._remove_runtime_fields(rows_s)
        s_s = ba._json_dumps_deterministic(rows_s)
        p_s = self._assert_within_run_dir(run_paths, run_paths.output_dir / "pattern_stats.v0_1_0.json")
        with p_s.open("w", encoding="utf-8", newline="\n") as f:
            f.write(s_s)
            f.write("\n")
        produced.append(ProducedArtifact(name=p_s.name, path=str(p_s)))

        # Final guardrail: produced paths must stay in run_dir
        for art in produced:
            self._assert_within_run_dir(run_paths, Path(art.path))

        return produced
