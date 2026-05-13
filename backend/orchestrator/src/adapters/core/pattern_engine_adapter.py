from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml

from .base_adapter import BaseAdapter, RunPaths
from .core_types import CoreResult, ProducedArtifact


def _to_plain(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain(v) for v in obj]
    return obj


def _get_mode(input_payload: dict[str, Any]) -> str:
    config = _to_plain(input_payload.get("config", input_payload))
    if not isinstance(config, dict):
        raise ValueError("Pattern adapter config must be a dict/model")

    mode = config.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        raise ValueError("Pattern config requires explicit mode")

    return mode.strip()


class PatternEngineAdapter(BaseAdapter):
    """
    Pattern Engine Adapter.

    Canonical modes:
    - manual_template      → new P1 backend path
    - historical_reference → legacy reference-window engine
    """

    def adapter_id(self) -> str:
        return "pattern_engine"

    def build_command(
        self,
        run_paths: RunPaths,
        *,
        timeout_s: int,
        extra_args: list[str],
    ) -> list[str]:
        raise RuntimeError("PatternEngineAdapter runs in-process")

    def expected_outputs(self, run_paths: RunPaths) -> list[str | Path]:
        return []

    def prepare_run_dir(self, run_paths: RunPaths, input_payload: Any) -> Path:
        if not isinstance(input_payload, dict):
            raise ValueError("Pattern adapter expects dict input_payload")

        cfg = input_payload.get("config_yaml_path")
        if cfg:
            cfg_src = Path(str(cfg))
            if not cfg_src.exists():
                raise FileNotFoundError(f"config_yaml_path not found: {cfg_src}")
            return self._copy_in_run_dir(
                run_paths,
                cfg_src,
                "pattern_engine/config/config.yaml",
            )

        dataset = _to_plain(input_payload.get("dataset"))
        if not isinstance(dataset, dict):
            raise ValueError("Missing required key: dataset")

        config = _to_plain(input_payload.get("config"))
        if not isinstance(config, dict):
            raise ValueError("Missing required key: config")

        mode = config.get("mode")

        if mode == "manual_template":
            staged_cfg = (
                run_paths.run_dir
                / "pattern_engine"
                / "config"
                / "manual_template.yaml"
            )
            staged_cfg.parent.mkdir(parents=True, exist_ok=True)
            staged_cfg.write_text(
                yaml.safe_dump(
                    {
                        "dataset": dataset,
                        "config": config,
                    },
                    sort_keys=False,
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            return staged_cfg

        if mode == "historical_reference":
            runtime_cfg = dict(config)
            runtime_cfg.pop("mode", None)

            staged_cfg = (
                run_paths.run_dir
                / "pattern_engine"
                / "config"
                / "config.yaml"
            )
            staged_cfg.parent.mkdir(parents=True, exist_ok=True)
            staged_cfg.write_text(
                yaml.safe_dump(runtime_cfg, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            return staged_cfg

        raise ValueError(f"Unsupported pattern mode: {mode!r}")

    def run(
        self,
        input_payload: Any,
        *,
        timeout_s: Optional[int] = None,
        extra_args: Optional[list[str]] = None,
    ) -> CoreResult:
        run_paths = self._create_isolated_workdir()
        self._write_payload_snapshot(run_paths, _to_plain(input_payload))

        meta: dict[str, Any] = {
            "adapter_id": self.adapter_id(),
            "run_dir": str(run_paths.run_dir),
            "mode": "in_process",
        }

        try:
            if not isinstance(input_payload, dict):
                raise ValueError("Pattern adapter expects dict input_payload")

            pattern_mode = _get_mode(input_payload)
            meta["pattern_mode"] = pattern_mode

            cfg_path = self.prepare_run_dir(run_paths, input_payload)
        except Exception as e:
            meta["stage_exception"] = repr(e)
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

        try:
            export_parquet = bool(input_payload.get("export_parquet", False))
            export_schema_json = bool(input_payload.get("export_schema_json", False))
            run_id = input_payload.get("run_id")

            if not os.environ.get("PATTERN_ENGINE_RAW_ROOT"):
                market_data_root = os.environ.get("MARKET_DATA_ROOT")
                if market_data_root:
                    os.environ["PATTERN_ENGINE_RAW_ROOT"] = market_data_root

            if pattern_mode == "manual_template":
                from engines.pattern_engine.manual.run_manual_template_engine import (
                    run_manual_template_engine,
                )

                _artifacts = run_manual_template_engine(
                    config_path=cfg_path,
                    output_dir=run_paths.output_dir,
                    run_id=run_id,
                    engine_version="1.0",
                )
                meta["engine_call"] = "run_manual_template_engine"

            elif pattern_mode == "historical_reference":
                from engines.pattern_engine.run.run_engine import (
                    run_pattern_engine,
                )

                _artifacts = run_pattern_engine(
                    config_path=cfg_path,
                    output_dir=run_paths.output_dir,
                    export_parquet=export_parquet,
                    export_schema_json=export_schema_json,
                    run_id=run_id,
                )
                meta["engine_call"] = "run_pattern_engine"
                meta["export_parquet"] = export_parquet
                meta["export_schema_json"] = export_schema_json

            else:
                raise ValueError(f"Unsupported pattern mode: {pattern_mode!r}")

        except Exception as e:
            meta["exception"] = repr(e)
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

        try:
            produced = self._capture_all_outputs(run_paths)
            return CoreResult(True, produced, str(run_paths.logs_dir), meta)
        except Exception as e:
            meta["capture_exception"] = repr(e)
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

    def _capture_all_outputs(self, run_paths: RunPaths) -> list[ProducedArtifact]:
        outdir = run_paths.output_dir.resolve()
        if not outdir.exists():
            raise FileNotFoundError(f"output_dir missing: {outdir}")

        files = [p for p in outdir.rglob("*") if p.is_file()]
        if not files:
            raise FileNotFoundError(f"No output files produced under: {outdir}")

        files_sorted = sorted(
            files,
            key=lambda p: str(p.relative_to(run_paths.run_dir)).replace("\\", "/"),
        )

        produced: list[ProducedArtifact] = []
        for p in files_sorted:
            p2 = self._assert_within_run_dir(run_paths, p)
            produced.append(ProducedArtifact(name=p2.name, path=str(p2)))

        return produced