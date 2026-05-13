from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Any, List

from .base_adapter import BaseAdapter, RunPaths
from .core_types import ProducedArtifact


class RootEngineAdapter(BaseAdapter):
    """
    Root Engine Adapter

    Contract:
      - Expects dict input_payload
      - Writes payload_snapshot.json (BaseAdapter behavior)
      - Invokes:
            python -m engines.root_engine
                --input <payload_snapshot.json>
                --output <run_dir/output>

      - Expects exactly one file:
            output/root_engine_result.json

    No CSV normalization.
    No globbing.
    Artifact already JSON deterministic.

    O7.10 note:
      - If payload.config.engine.data_path is provided and valid, propagate it
        to MARKET_DATA_ROOT for the subprocess execution context.
      - Otherwise fallback to existing process environment.
    """

    _OUTPUT_FILENAME = "root_engine_result.json"

    def adapter_id(self) -> str:
        return "root_engine_cli"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_project_root() -> Path:
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "engines").is_dir() and (parent / "backend").is_dir():
                return parent
        raise RuntimeError("Cannot resolve project root for RootEngineAdapter")
    @staticmethod
    def _resolve_market_data_root_from_payload(input_payload: dict[str, Any]) -> str | None:
        config = input_payload.get("config")
        if not isinstance(config, dict):
            return None

        engine = config.get("engine")
        if not isinstance(engine, dict):
            return None

        raw = engine.get("data_path")
        if not isinstance(raw, str):
            return None

        value = raw.strip()
        if not value:
            return None

        # Common placeholder values used in configs/examples should not be treated as real paths.
        if value.lower() in {"x", "<path>", "path/to/data", "todo"}:
            return None

        return value

    # ------------------------------------------------------------------
    # Stage input
    # ------------------------------------------------------------------

    def prepare_run_dir(self, run_paths: RunPaths, input_payload: Any) -> None:
        if not isinstance(input_payload, dict):
            raise ValueError("RootEngineAdapter expects dict input_payload")

        market_data_root = self._resolve_market_data_root_from_payload(input_payload)

        if market_data_root is not None:
            candidate = Path(market_data_root)
            if not candidate.exists():
                raise ValueError(
                    f"RootEngineAdapter config.engine.data_path does not exist: {candidate}"
                )
            if not candidate.is_dir():
                raise ValueError(
                    f"RootEngineAdapter config.engine.data_path is not a directory: {candidate}"
                )

            # Ensure subprocess inherits a valid MARKET_DATA_ROOT even if the
            # backend process was started without that environment variable.
            os.environ["MARKET_DATA_ROOT"] = str(candidate.resolve())

        # BaseAdapter will snapshot payload into:
        # run_paths.input_dir / payload_snapshot.json
        # No additional staging required.
        project_root = self._find_project_root()
        existing_pythonpath = os.environ.get("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = (
            str(project_root)
            if not existing_pythonpath
            else str(project_root) + os.pathsep + existing_pythonpath
        )

        return

    # ------------------------------------------------------------------
    # Build subprocess command
    # ------------------------------------------------------------------

    def build_command(
        self,
        run_paths: RunPaths,
        *,
        timeout_s: int,
        extra_args: List[str],
    ) -> List[str]:
        input_json = (run_paths.input_dir / "payload_snapshot.json").resolve()
        output_dir = run_paths.output_dir.resolve()

        cmd = [
            sys.executable,
            "-m",
            "engines.root_engine",
            "--input",
            str(input_json),
            "--output",
            str(output_dir),
        ]

        cmd.extend(extra_args)
        return cmd

    # ------------------------------------------------------------------
    # Expected outputs
    # ------------------------------------------------------------------

    def expected_outputs(self, run_paths: RunPaths) -> List[str | Path]:
        return [self._OUTPUT_FILENAME]

    # ------------------------------------------------------------------
    # Normalized artifact name (C1-style)
    # ------------------------------------------------------------------

    def normalized_artifact_name(self, raw_output: Path) -> str:
        # Logical name derived from tool identity
        # Could evolve to root_output.v1.json if versioning needed
        return "root_engine.v1.json"

    # ------------------------------------------------------------------
    # Capture outputs
    # ------------------------------------------------------------------

    def _capture_and_normalize_outputs(
        self,
        run_paths: RunPaths,
    ) -> List[ProducedArtifact]:
        output_path = run_paths.output_dir / self._OUTPUT_FILENAME

        if not output_path.exists():
            raise FileNotFoundError(
                f"Root engine output not found: {output_path}"
            )

        # Ensure file is valid strict JSON (no NaN/Infinity)
        with output_path.open("r", encoding="utf-8") as f:
            try:
                obj = json.load(f)
            except Exception as e:
                raise ValueError(f"Invalid JSON produced by root engine: {e}")

        # Re-dump deterministically to enforce canonical form
        normalized_str = json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

        normalized_path = run_paths.output_dir / self.normalized_artifact_name(output_path)

        with normalized_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(normalized_str)
            f.write("\n")

        return [
            ProducedArtifact(
                name=normalized_path.name,
                path=str(normalized_path),
            )
        ]