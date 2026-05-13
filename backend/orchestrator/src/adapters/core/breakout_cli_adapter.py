from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_adapter import BaseAdapter, RunPaths


class BreakoutCliAdapter(BaseAdapter):
    def adapter_id(self) -> str:
        return "breakout_engine_cli"

    def prepare_run_dir(self, run_paths: RunPaths, input_payload: Any) -> None:
        if not isinstance(input_payload, dict):
            raise ValueError("Breakout adapter expects dict input_payload")

        bars_5m = input_payload.get("bars_5m_path")
        bars_1m = input_payload.get("bars_1m_path")
        cfg = input_payload.get("config_yaml_path")

        if not bars_5m or not bars_1m or not cfg:
            raise ValueError("Missing required keys: bars_5m_path, bars_1m_path, config_yaml_path")

        self._copy_in_run_dir(run_paths, Path(cfg), "config.yaml")
        self._copy_in_run_dir(run_paths, Path(bars_5m), "market_analysis_engine/data/raw/5m/MNQ_30D.txt")
        self._copy_in_run_dir(run_paths, Path(bars_1m), "market_analysis_engine/data/raw/1m/MNQ_30D.txt")

    def build_command(self, run_paths: RunPaths, *, timeout_s: int, extra_args: list[str]) -> list[str]:
        cmd = ["python", "scripts/run_detector_test.py"]
        cmd.extend(extra_args)
        return cmd

    def expected_outputs(self, run_paths: RunPaths) -> list[str | Path]:
        # filename non deterministico: si prende via glob (ordinato)
        return ["exports_production/breakouts_v*.csv"]

    def normalized_artifact_name(self, raw_output: Path) -> str:
        # Derivato 1:1 da outputs_schema C1: name="breakouts", version="v1"
        # => breakouts.v1.json
        return "breakouts.v1.json"
