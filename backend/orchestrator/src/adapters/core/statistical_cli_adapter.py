from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_adapter import BaseAdapter, RunPaths
from .core_types import ProducedArtifact


class StatisticalCliAdapter(BaseAdapter):
    """
    C2 directive:
    - BaseAdapter invariato
    - naming from outputs_schema only: <name>.<version>.json
    - glob policy: exactly 1 match where contract expects single file
    """

    _OUTPUT_NAME = "levels"
    _OUTPUT_VERSION = "v0_3_0"

    def adapter_id(self) -> str:
        return "statistical_engine_cli"

    def prepare_run_dir(self, run_paths: RunPaths, input_payload: Any) -> None:
        if not isinstance(input_payload, dict):
            raise ValueError("Statistical adapter expects dict input_payload")

        cfg = input_payload.get("config_yaml_path")
        if not cfg:
            raise ValueError("Missing required key: config_yaml_path")

        breakouts = self._as_list(input_payload.get("breakouts_csv_paths"))
        levels = self._as_list(input_payload.get("levels_csv_paths"))

        # Determinism guardrail (exactly 1 each)
        if len(breakouts) != 1:
            raise ValueError(f"breakouts_csv_paths must contain exactly 1 file, got {len(breakouts)}")
        if len(levels) != 1:
            raise ValueError(f"levels_csv_paths must contain exactly 1 file, got {len(levels)}")

        self._copy_in_run_dir(run_paths, Path(cfg), "statistical_engine/v0.3.0_levels/config/config_levels.yaml")
        self._copy_in_run_dir(
            run_paths,
            Path(breakouts[0]),
            "statistical_engine/v0.3.0_levels/input/breakouts/breakouts.csv",
        )
        self._copy_in_run_dir(
            run_paths,
            Path(levels[0]),
            "statistical_engine/v0.3.0_levels/input/levels/levels.csv",
        )

    def build_command(self, run_paths: RunPaths, *, timeout_s: int, extra_args: list[str]) -> list[str]:
        cmd = ["python", "statistical_engine/v0.3.0_levels/build_df_master.py"]
        cmd.extend(extra_args)
        return cmd

    def expected_outputs(self, run_paths: RunPaths) -> list[str | Path]:
        return [
            "statistical_engine/v0.3.0_levels/df_masters/df_master_breakouts_levels_v0.3.0.parquet",
            "statistical_engine/v0.3.0_levels/output/df_master_summary.txt",
        ]

    def normalized_artifact_name(self, raw_output: Path) -> str:
        return f"{self._OUTPUT_NAME}.{self._OUTPUT_VERSION}.json"

    # --- adapter-local runtime cleanup (per directive) ---

    def _remove_runtime_fields_statistical(self, obj: Any) -> Any:
        """
        Keep BaseAdapter blacklist behavior, plus Statistical-specific variants like:
        - computation_timestamp_x
        """
        from .base_adapter import RUNTIME_FIELDS_BLACKLIST  # same module scope, allowed

        if isinstance(obj, dict):
            out: dict[str, Any] = {}
            for k, v in obj.items():
                if k in RUNTIME_FIELDS_BLACKLIST:
                    continue
                # Statistical-specific runtime variants
                if k.startswith("computation_timestamp"):
                    continue
                if k.endswith("_timestamp"):
                    continue
                out[k] = self._remove_runtime_fields_statistical(v)
            return out
        if isinstance(obj, list):
            return [self._remove_runtime_fields_statistical(x) for x in obj]
        return obj

    # ---- parquet loader (adapter-local, as before) ----

    def _load_df_master_records(self, parquet_path: Path) -> list[dict[str, Any]]:
        try:
            import pandas as pd  # type: ignore
        except Exception as e:
            raise RuntimeError(f"pandas not available for parquet load: {e!r}")

        try:
            df = pd.read_parquet(parquet_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read parquet (missing pyarrow/fastparquet?): {e!r}")

        sort_cols = [c for c in ["breakout_time", "breakout_id", "parent_balance_id"] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols, kind="mergesort")
        else:
            cols = list(df.columns)
            if cols:
                df = df.sort_values(cols, kind="mergesort")

        df = df.where(df.notna(), None)

        for c in df.columns:
            if str(df[c].dtype).startswith("datetime"):
                df[c] = df[c].apply(lambda x: x.isoformat() if x is not None else None)

        return df.to_dict(orient="records")

    # ---- override capture: parquet -> JSON artifact ----

    def _capture_and_normalize_outputs(self, run_paths: RunPaths) -> list[ProducedArtifact]:
        expected = self._expand_expected(run_paths, self.expected_outputs(run_paths))
        if len(expected) != 2:
            raise ValueError(f"Expected exactly 2 outputs (parquet + summary), got {len(expected)}")

        parquet = next((p for p in expected if p.suffix.lower() == ".parquet"), None)
        summary = next((p for p in expected if p.name.endswith(".txt")), None)
        if parquet is None or summary is None:
            raise ValueError(f"Missing parquet or summary in expected outputs: {expected}")

        if not parquet.exists():
            raise FileNotFoundError(f"Expected parquet missing: {parquet}")
        if not summary.exists():
            raise FileNotFoundError(f"Expected summary missing: {summary}")

        records = self._load_df_master_records(parquet)
        records = self._remove_runtime_fields_statistical(records)

        def _sanitize(x):
            import math
            try:
                import numpy as np  # type: ignore
            except Exception:
                np = None

            if x is None:
                return None
            if isinstance(x, float):
                if math.isnan(x) or math.isinf(x):
                    return None
                return x
            if np is not None and isinstance(x, (np.floating,)):
                xx = float(x)
                if math.isnan(xx) or math.isinf(xx):
                    return None
                return xx
            if np is not None and isinstance(x, (np.integer,)):
                return int(x)
            if isinstance(x, dict):
                return {k: _sanitize(v) for k, v in x.items()}
            if isinstance(x, list):
                return [_sanitize(v) for v in x]
            return x

        records = _sanitize(records)

        # deterministic JSON (same settings as BaseAdapter)
        import json
        s = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

        normalized_path = self._assert_within_run_dir(run_paths, run_paths.output_dir / self.normalized_artifact_name(parquet))
        with normalized_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(s)
            f.write("\n")

        return [ProducedArtifact(name=normalized_path.name, path=str(normalized_path))]

    @staticmethod
    def _as_list(v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [str(x) for x in v]
        return [str(v)]
