from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .base_adapter import BaseAdapter, RunPaths
from .core_types import CoreResult, ProducedArtifact


class QueryEngineAdapter(BaseAdapter):
    """
    Query Engine Adapter (QRY-4)

    - tool_id MUST remain exactly: query_engine
    - Executes in-process
    - Consumes ONLY statistical runtime artifact resolved by O5.x
    - Supports:
        * query spec direct
        * intent payload -> QRY-2 -> query spec
    - Produces canonical report.json
    """

    _REPORT_NAME = "report.json"

    def adapter_id(self) -> str:
        return "query_engine"

    # BaseAdapter abstract methods (unused because we override run()).
    def build_command(self, run_paths: RunPaths, *, timeout_s: int, extra_args: list[str]) -> list[str]:
        raise RuntimeError("QueryEngineAdapter runs in-process (no subprocess command)")

    def expected_outputs(self, run_paths: RunPaths) -> list[str | Path]:
        return [run_paths.output_dir / self._REPORT_NAME]

    def prepare_run_dir(self, run_paths: RunPaths, input_payload: Any) -> Path:
        if not isinstance(input_payload, dict):
            raise ValueError("Query engine adapter expects dict input_payload")

        statistical_artifact_path = input_payload.get("statistical_artifact_path")
        if not statistical_artifact_path:
            raise ValueError("Missing required key: statistical_artifact_path")

        artifact_root = Path(str(statistical_artifact_path)).resolve()
        outputs_dir = artifact_root / "outputs"

        if not artifact_root.exists():
            raise FileNotFoundError(f"statistical_artifact_path not found: {artifact_root}")

        candidate_paths = [
            outputs_dir / "statistical_dataset.parquet",
            outputs_dir / "statistical_dataset_v1_1_2.parquet",
        ]

        dataset_path = next((p for p in candidate_paths if p.exists()), None)
        if dataset_path is None:
            raise FileNotFoundError(
                "Statistical dataset not found. Expected one of: "
                + ", ".join(str(p) for p in candidate_paths)
            )

        staged_dataset = self._copy_in_run_dir(
            run_paths,
            dataset_path,
            "query_engine/input/statistical/statistical_dataset.parquet",
        )
        return staged_dataset

    def run(self, input_payload: Any, *, timeout_s: Optional[int] = None, extra_args: Optional[list[str]] = None) -> CoreResult:
        run_paths = self._create_isolated_workdir()
        self._write_payload_snapshot(run_paths, input_payload)

        meta: dict[str, Any] = {
            "adapter_id": self.adapter_id(),
            "run_dir": str(run_paths.run_dir),
            "mode": "in_process",
        }

        try:
            staged_dataset = self.prepare_run_dir(run_paths, input_payload)
        except Exception as e:
            meta["stage_exception"] = repr(e)
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

        try:
            query_payload = self._extract_query_payload(input_payload)
            query_kind = self._classify_query_payload(query_payload)

            report = run_query_engine(
                dataset_path=staged_dataset,
                query_payload=query_payload,
            )

            out_path = (run_paths.output_dir / self._REPORT_NAME).resolve()
            out_path.write_text(
                json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n",
                encoding="utf-8",
            )

            meta["query_kind"] = query_kind
            meta["dataset_relpath"] = str(staged_dataset.relative_to(run_paths.run_dir))
            meta["report_relpath"] = str(out_path.relative_to(run_paths.run_dir))
        except Exception as e:
            meta["exception"] = repr(e)
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

        try:
            produced = self._capture_outputs(run_paths)
            return CoreResult(True, produced, str(run_paths.logs_dir), meta)
        except Exception as e:
            meta["capture_exception"] = repr(e)
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

    def _capture_outputs(self, run_paths: RunPaths) -> list[ProducedArtifact]:
        report_path = (run_paths.output_dir / self._REPORT_NAME).resolve()
        if not report_path.exists():
            raise FileNotFoundError(f"Expected report missing: {report_path}")
        return [ProducedArtifact(name=report_path.name, path=str(report_path))]

    def _extract_query_payload(self, input_payload: dict[str, Any]) -> dict[str, Any]:
        raw = input_payload.get("query")
        if not isinstance(raw, dict):
            raise ValueError("Missing or invalid 'query': expected object")
        return dict(raw)

    def _classify_query_payload(self, query_payload: dict[str, Any]) -> str:
        if self._looks_like_query_spec(query_payload):
            return "query_spec"

        if self._looks_like_intent(query_payload):
            return "intent"

        raise ValueError("Unsupported query payload: not recognizable as intent or query spec")

    def _looks_like_query_spec(self, obj: dict[str, Any]) -> bool:
        metric = obj.get("metric")
        filters = obj.get("filters", [])
        group_by = obj.get("group_by", [])

        return (
            isinstance(metric, str)
            and metric != ""
            and isinstance(filters, list)
            and isinstance(group_by, list)
        )

    def _looks_like_intent(self, obj: dict[str, Any]) -> bool:
        if "expression" in obj:
            return isinstance(obj.get("expression"), str) and bool(obj.get("expression"))

        # structured intent is accepted only when it does NOT already qualify as query spec
        if self._looks_like_query_spec(obj):
            return False

        metric = obj.get("metric")
        filters = obj.get("filters", [])
        group_by = obj.get("group_by", [])

        optional_keys = {
            "value_field",
            "target_field",
            "success_condition",
            "event_predicate",
            "condition_predicate",
            "normalization",
            "score_metric",
            "sort_direction",
        }

        keys = set(obj.keys())
        allowed_intent_keys = {"metric", "filters", "group_by"} | optional_keys

        return (
            isinstance(metric, str)
            and metric != ""
            and isinstance(filters, list)
            and isinstance(group_by, list)
            and keys.issubset(allowed_intent_keys)
        )

def run_query_engine(*, dataset_path: Path, query_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Runtime entry point for QRY-4.

    dataset_path:
        path to statistical_dataset.parquet

    query_payload:
        either intent payload or direct query spec
    """
    from engines.query_engine.core.dataset_loader import load_statistical_dataset
    from engines.query_engine.core.query_executor import execute_query
    from engines.query_engine.core.query_planner import plan_query
    from engines.query_engine.intent import (
        build_query_spec,
        map_intent,
        parse_intent,
        validate_intent,
    )
    from engines.query_engine.report import build_report

    df = load_statistical_dataset(str(dataset_path))

    is_spec = (
        isinstance(query_payload.get("metric"), str)
        and isinstance(query_payload.get("filters", []), list)
        and isinstance(query_payload.get("group_by", []), list)
    )

    query_spec: dict[str, Any]
    if is_spec:
        query_spec = dict(query_payload)
    else:
        parsed = parse_intent(dict(query_payload))
        validated = validate_intent(parsed)
        mapped = map_intent(validated)
        query_spec = build_query_spec(mapped)

    plan = plan_query(query_spec, df)
    query_result = execute_query(df, plan)
    report = build_report(plan, query_result)
    return report