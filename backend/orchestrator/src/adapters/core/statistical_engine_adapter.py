from __future__ import annotations
import json
import traceback
from pathlib import Path
from typing import Any, Optional

from .base_adapter import BaseAdapter, RunPaths
from .core_types import CoreResult, ProducedArtifact
from .root_to_statistical_adapter import adapt_root_to_statistical


class StatisticalEngineAdapter(BaseAdapter):
    """
    Statistical Engine Adapter (Phase 2)

    - tool_id MUST remain exactly: statistical_engine (freeze)
    - Executes in-process (no local engine bundle required)
    - Produces a parquet under run_paths.output_dir
    - Returns legacy CoreResult(success, produced_artifacts, logs_dir, meta),
      which is then bridged by runtime.tool_registry into runtime CoreResult(payload=...)
    """

    _OUTPUT_NAME = "statistical_dataset"
    _OUTPUT_VERSION = "v1_0_0"
    _PARQUET_NAME = "statistical_dataset.parquet"
    _BUCKETIZERS_JSON_NAME = "statistical_bucketizers_used.json"

    def adapter_id(self) -> str:
        return "statistical_engine"

    # BaseAdapter abstract methods; unused because this adapter runs in-process.
    def build_command(
        self,
        run_paths: RunPaths,
        *,
        timeout_s: int,
        extra_args: list[str],
    ) -> list[str]:
        raise RuntimeError("StatisticalEngineAdapter runs in-process (no subprocess command)")

    def expected_outputs(self, run_paths: RunPaths) -> list[str | Path]:
        return [
            run_paths.output_dir / self._PARQUET_NAME,
            run_paths.output_dir / self._BUCKETIZERS_JSON_NAME,
        ]

    def prepare_run_dir(self, run_paths: RunPaths, input_payload: Any) -> None:
        if not isinstance(input_payload, dict):
            raise ValueError("Statistical adapter expects dict input_payload")

        root_artifact_path = input_payload.get("root_artifact_path")
        if not root_artifact_path:
            raise ValueError("Missing required key: root_artifact_path")

        artifact_root = Path(root_artifact_path).resolve()
        root_dataset = artifact_root / "outputs" / "root_output_dataset.csv"

        if not artifact_root.exists():
            raise FileNotFoundError(f"root_artifact_path not found: {artifact_root}")

        if not root_dataset.exists():
            raise FileNotFoundError(f"Root dataset not found: {root_dataset}")

        self._copy_in_run_dir(
            run_paths,
            root_dataset,
            "statistical_engine/input/root/root_output_dataset.csv",
        )

    def normalized_artifact_name(self, raw_output: Path) -> str:
        return raw_output.name

    # ------------------------------------------------------------------
    # In-process run (bypass subprocess)
    # ------------------------------------------------------------------

    def run(
        self,
        input_payload: Any,
        *,
        timeout_s: Optional[int] = None,
        extra_args: Optional[list[str]] = None,
    ) -> CoreResult:
        run_paths = self._create_isolated_workdir()
        self._write_payload_snapshot(run_paths, input_payload)

        meta: dict[str, Any] = {
            "adapter_id": self.adapter_id(),
            "run_dir": str(run_paths.run_dir),
            "logs_dir": str(run_paths.logs_dir),
            "mode": "in_process",
        }

        try:
            self.prepare_run_dir(run_paths, input_payload)
        except Exception as e:
            meta["stage_exception"] = repr(e)
            meta["traceback"] = traceback.format_exc()
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

        try:
            from engines.statistical_engine.statistical_pipeline import (
                run_statistical_pipeline,
            )

            raw_root_dataset_path = (
                run_paths.run_dir / "statistical_engine/input/root/root_output_dataset.csv"
            ).resolve()

            adapted_root_dataset_path = (
                run_paths.run_dir / "statistical_engine/input/root/root_dataset_adapted.csv"
            ).resolve()

            adapt_root_to_statistical(
                root_dataset_path=raw_root_dataset_path,
                adapted_dataset_path=adapted_root_dataset_path,
            )

            parquet_out = (run_paths.output_dir / self._PARQUET_NAME).resolve()

            statistical_config = {}
            if isinstance(input_payload, dict):
                statistical_config = input_payload.get("config", {}) or {}


            run_statistical_pipeline(
                root_dataset_path=adapted_root_dataset_path,
                output_parquet_path=parquet_out,
                config=input_payload.get("config", {}),
            )

            if not parquet_out.exists():
                raise FileNotFoundError(
                    f"Pipeline completed but expected parquet was not created: {parquet_out}"
                )
            
            bucketizers_out = (
                run_paths.output_dir / self._BUCKETIZERS_JSON_NAME
            ).resolve()

            bucketizers_payload = {}
            if isinstance(statistical_config, dict):
                bucketizers_payload = statistical_config.get("bucketizers", {}) or {}

            bucketizers_out.write_text(
                json.dumps(
                    {
                        "bucketizers": bucketizers_payload,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            meta["engine_call"] = "run_statistical_pipeline"
            meta["config_passed_to_pipeline"] = bool(statistical_config)
            meta["raw_root_dataset_relpath"] = str(
                raw_root_dataset_path.relative_to(run_paths.run_dir)
            )
            meta["adapted_root_dataset_relpath"] = str(
                adapted_root_dataset_path.relative_to(run_paths.run_dir)
            )
            meta["parquet_relpath"] = str(parquet_out.relative_to(run_paths.run_dir))
            meta["parquet_bytes"] = parquet_out.stat().st_size
            meta["bucketizers_json_relpath"] = str(
                bucketizers_out.relative_to(run_paths.run_dir)
            )
            meta["bucketizers_json_bytes"] = bucketizers_out.stat().st_size
            meta["bucketizers_present"] = bool(bucketizers_payload)
        except Exception as e:
            meta["exception"] = repr(e)
            meta["traceback"] = traceback.format_exc()
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

        try:
            produced = self._capture_and_normalize_outputs(run_paths)
            meta["produced_artifacts_count"] = len(produced)
            if produced:
                meta["produced_artifact_path"] = produced[0].path
            return CoreResult(True, produced, str(run_paths.logs_dir), meta)
        except Exception as e:
            meta["capture_exception"] = repr(e)
            meta["traceback"] = traceback.format_exc()
            return CoreResult(False, [], str(run_paths.logs_dir), meta)


    @staticmethod
    def _as_list(v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [str(x) for x in v]
        return [str(v)]