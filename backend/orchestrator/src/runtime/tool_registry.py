from __future__ import annotations

import io
import json
from collections.abc import Callable, Mapping, Iterable
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import pandas as pd

from ..adapters.core.core_port import CorePort
from ..adapters.core.query_cli_adapter import QueryCliAdapter
from ..adapters.core.root_engine_adapter import RootEngineAdapter


class ToolNotRegisteredError(RuntimeError):
    """Raised when a tool_id is not registered in ToolRegistry (deterministic fail-fast)."""


def _root_json_bytes_to_canonical_csv_bytes(data: bytes) -> bytes:
    try:
        payload = json.loads(data.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Invalid root engine JSON artifact: {e}") from e

    if not isinstance(payload, dict):
        raise RuntimeError("Root engine artifact must be a JSON object")

    breakouts = payload.get("breakouts")
    if not isinstance(breakouts, list):
        raise RuntimeError("Root engine artifact missing 'breakouts' list")

    df = pd.DataFrame(breakouts)

    required_source_columns = [
        "breakout_id",
        "direction",
        "breakout_price",
        "balance_range_size",
        "initial_delta",
        "initial_volume",
        "atr_before",
        "follow_through",
        "is_failed",
    ]

    required_output_columns = [
        "schema_version",
        "breakout_id",
        "direction",
        "breakout_price",
        "balance_range_size",
        "initial_delta",
        "initial_volume",
        "atr_before",
        "follow_through",
        "is_failed",
    ]

    optional_passthrough = [
        "breakout_type",
        "delta_peak",
        "delta_mean_post_breakout",
        "pre_breakout_signal",
        "breakout_time",
        "instrument",
        "session_id",
        "timeframe",
        "version",
        "ml_distance_to_level",
        "ml_nearest_support",
        "ml_nearest_resistance",
        "ml_cluster_strength",
        "ml_density",
        "ml_alignment_score",
    ]

    df = df.copy()

    if df.empty:
        for col in required_output_columns:
            if col not in df.columns:
                df[col] = pd.Series(dtype="object")
        for col in optional_passthrough:
            if col not in df.columns:
                df[col] = pd.Series(dtype="object")
    else:
        missing = [c for c in required_source_columns if c not in df.columns]
        if missing:
            raise RuntimeError(
                f"Root engine breakout dataset missing required columns: {missing}"
            )

        for col in optional_passthrough:
            if col not in df.columns:
                df[col] = None

    df["schema_version"] = "1.1.0"

    ordered = list(required_output_columns)
    extras = sorted([c for c in df.columns if c not in ordered])
    df = df[ordered + extras]

    sort_keys = [c for c in ("breakout_time", "breakout_id") if c in df.columns]
    if sort_keys:
        df = df.sort_values(sort_keys, kind="mergesort").reset_index(drop=True)

    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n")
    return buf.getvalue().encode("utf-8")

def _root_input_bars_to_canonical_csv_bytes(bars: list[dict[str, object]]) -> bytes:
    df = pd.DataFrame(list(bars))

    required_output_columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    optional_passthrough = [
        "delta",
    ]

    if df.empty:
        for col in required_output_columns:
            if col not in df.columns:
                df[col] = pd.Series(dtype="object")
        for col in optional_passthrough:
            if col not in df.columns:
                df[col] = pd.Series(dtype="object")
    else:
        if "time" not in df.columns:
            raise RuntimeError("Root input dataset missing required column: time")

        rename_map = {
            "time": "timestamp",
        }
        df = df.rename(columns=rename_map)

        missing = [c for c in ("open", "high", "low", "close") if c not in df.columns]
        if missing:
            raise RuntimeError(
                f"Root input dataset missing required OHLC columns: {missing}"
            )

        if "volume" not in df.columns:
            df["volume"] = None

        for col in optional_passthrough:
            if col not in df.columns:
                df[col] = None

    ordered = list(required_output_columns)
    extras = sorted([c for c in df.columns if c not in ordered])
    df = df[ordered + extras]

    if "timestamp" in df.columns:
        df = df.sort_values(["timestamp"], kind="mergesort").reset_index(drop=True)

    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n")
    return buf.getvalue().encode("utf-8")


def _build_query_cli_core(*, tmp_root=None) -> CorePort:
    from ..adapters.core.core_port import CoreInvocation, CoreResult

    class _QueryCliCore(CorePort):
        def __init__(self) -> None:
            self._adapter = QueryCliAdapter(tmp_root=tmp_root)

        def invoke(self, invocation: CoreInvocation) -> CoreResult:
            tool = str(invocation.tool_id)
            if tool != "query_cli":
                raise RuntimeError(f"Unsupported tool_id (wired only query_cli): {tool}")

            input_payload = dict(invocation.inputs)
            res = self._adapter.run(input_payload)

            meta = getattr(res, "meta", None) or {}
            if meta.get("status") != "SUCCEEDED":
                raise RuntimeError(f"query_cli failed meta={meta}")

            produced = list(getattr(res, "produced_artifacts", []) or [])
            if len(produced) != 1:
                raise RuntimeError(f"Expected exactly 1 produced artifact, got {len(produced)}")

            artifact_obj = produced[0]
            payload_obj = {
                "artifact": {
                    "tool_id": getattr(artifact_obj, "tool_id", None),
                    "fingerprint": getattr(artifact_obj, "fingerprint", None),
                    "manifest_relpath": getattr(artifact_obj, "manifest_relpath", None),
                    "outputs_relpath": getattr(artifact_obj, "outputs_relpath", None),
                    "content_type": getattr(artifact_obj, "content_type", None),
                    "checksum": getattr(artifact_obj, "checksum", None),
                }
            }
            return CoreResult(payload=payload_obj, metrics=None)

    return _QueryCliCore()


def _build_root_engine_core(*, tmp_root=None) -> CorePort:
    from ..adapters.core.core_port import CoreInvocation, CoreResult
    from ..adapters.storage.ports import ArtifactPayload, OutputItem
    from engines.root_engine.dataset_loader import load_dataset

    class _RootEnginePayload(ArtifactPayload):
        def __init__(self, *, output_data: bytes, input_data: bytes) -> None:
            self._output_data = output_data
            self._input_data = input_data

        def iter_outputs(self) -> Iterable[OutputItem]:
            return iter(
                (
                    OutputItem(
                        logical_name="root_output_dataset",
                        filename="root_output_dataset.csv",
                        data=self._output_data,
                    ),
                    OutputItem(
                        logical_name="root_input_dataset",
                        filename="root_input_dataset.csv",
                        data=self._input_data,
                    ),
                )
            )

    class _RootEngineCore(CorePort):
        def __init__(self) -> None:
            self._adapter = RootEngineAdapter(tmp_root=tmp_root)

        def invoke(self, invocation: CoreInvocation) -> CoreResult:
            tool = str(invocation.tool_id)
            if tool != "root_engine":
                raise RuntimeError(f"Unsupported tool_id (wired only root_engine): {tool}")

            input_payload = dict(invocation.inputs or {})
            parameters = dict(invocation.parameters or {})

            config_payload = dict(parameters)
            dataset_in_inputs = input_payload.get("dataset")
            dataset_in_config = config_payload.get("dataset")

            if isinstance(dataset_in_inputs, dict) and "dataset" not in config_payload:
                config_payload["dataset"] = dict(dataset_in_inputs)
            elif isinstance(dataset_in_config, dict):
                config_payload["dataset"] = dict(dataset_in_config)

            input_payload["config"] = config_payload

            res = self._adapter.run(input_payload)

            meta = getattr(res, "execution_metadata", None) or getattr(res, "meta", None) or {}
            if not getattr(res, "success", False):
                raise RuntimeError(f"root_engine failed meta={meta}")

            produced = list(getattr(res, "produced_artifacts", []) or [])
            if len(produced) != 1:
                raise RuntimeError(f"Expected exactly 1 produced artifact, got {len(produced)}")

            artifact_obj = produced[0]
            artifact_path = Path(getattr(artifact_obj, "path", "")).resolve()
            if not artifact_path.exists():
                raise RuntimeError(f"Produced artifact path not found: {artifact_path}")

            raw_data = artifact_path.read_bytes()
            output_csv_data = _root_json_bytes_to_canonical_csv_bytes(raw_data)

            dataset_payload = input_payload.get("dataset")
            if not isinstance(dataset_payload, dict):
                dataset_payload = config_payload.get("dataset")

            if not isinstance(dataset_payload, dict):
                raise RuntimeError("Root engine input dataset is missing or invalid")

            bars = load_dataset(dataset_payload)
            input_csv_data = _root_input_bars_to_canonical_csv_bytes(bars)

            payload = _RootEnginePayload(
                output_data=output_csv_data,
                input_data=input_csv_data,
            )
            return CoreResult(payload=payload, metrics=None)

    return _RootEngineCore()


def _build_statistical_engine_core(*, tmp_root=None) -> CorePort:
    from ..adapters.core.core_port import CoreInvocation, CoreResult
    from ..adapters.core.statistical_engine_adapter import StatisticalEngineAdapter
    from ..adapters.storage.ports import ArtifactPayload, OutputItem

    class _StatisticalEnginePayload(ArtifactPayload):
        def __init__(
            self,
            *,
            parquet_data: bytes,
            bucketizers_data: bytes | None = None,
        ) -> None:
            self._parquet_data = parquet_data
            self._bucketizers_data = bucketizers_data

        def iter_outputs(self) -> Iterable[OutputItem]:
            outputs: list[OutputItem] = [
                OutputItem(
                    logical_name="statistical_dataset",
                    filename="statistical_dataset.parquet",
                    data=self._parquet_data,
                )
            ]

            if self._bucketizers_data is not None:
                outputs.append(
                    OutputItem(
                        logical_name="statistical_bucketizers_used",
                        filename="statistical_bucketizers_used.json",
                        data=self._bucketizers_data,
                    )
                )

            return iter(outputs)

    class _StatisticalEngineCore(CorePort):
        def __init__(self) -> None:
            self._adapter = StatisticalEngineAdapter(tmp_root=tmp_root)

        def invoke(self, invocation: CoreInvocation) -> CoreResult:
            tool = str(invocation.tool_id)
            if tool != "statistical_engine":
                raise RuntimeError(f"Unsupported tool_id (statistical_engine only): {tool}")

            input_payload = dict(invocation.inputs or {})
            input_payload.update(invocation.parameters or {})

            res = self._adapter.run(input_payload)

            meta = getattr(res, "execution_metadata", None) or getattr(res, "meta", None) or {}
            if not getattr(res, "success", False):
                raise RuntimeError(f"statistical_engine failed meta={meta}")

            produced = list(getattr(res, "produced_artifacts", []) or [])
            if len(produced) < 1:
                raise RuntimeError("Expected at least 1 produced artifact")

            parquet_path: Path | None = None
            bucketizers_path: Path | None = None

            for artifact_obj in produced:
                artifact_path = Path(getattr(artifact_obj, "path", "")).resolve()
                if not artifact_path.exists():
                    raise RuntimeError(f"Produced artifact path not found: {artifact_path}")

                if artifact_path.name == "statistical_dataset.parquet":
                    parquet_path = artifact_path
                elif artifact_path.name == "statistical_bucketizers_used.json":
                    bucketizers_path = artifact_path

            if parquet_path is None:
                raise RuntimeError("Missing required produced artifact: statistical_dataset.parquet")

            parquet_data = parquet_path.read_bytes()
            bucketizers_data = (
                bucketizers_path.read_bytes() if bucketizers_path is not None else None
            )

            payload = _StatisticalEnginePayload(
                parquet_data=parquet_data,
                bucketizers_data=bucketizers_data,
            )
            return CoreResult(payload=payload, metrics=None)

    return _StatisticalEngineCore()


def _build_pattern_engine_core(*, tmp_root=None) -> CorePort:
    from pathlib import Path
    from typing import Iterable

    from ..adapters.core.core_port import CoreInvocation, CoreResult
    from ..adapters.core.pattern_engine_adapter import PatternEngineAdapter
    from ..adapters.storage.ports import ArtifactPayload, OutputItem

    class _PatternEnginePayload(ArtifactPayload):
        def __init__(self, items: list[OutputItem]) -> None:
            self._items = tuple(items)

        def iter_outputs(self) -> Iterable[OutputItem]:
            return iter(self._items)

    class _PatternEngineCore(CorePort):
        def __init__(self) -> None:
            self._adapter = PatternEngineAdapter(tmp_root=tmp_root)

        def invoke(self, invocation: CoreInvocation) -> CoreResult:
            tool = str(invocation.tool_id)
            if tool != "pattern_engine":
                raise RuntimeError(f"Unsupported tool_id (pattern_engine only): {tool}")

            input_payload = {}
            input_payload.update(invocation.inputs or {})

            parameters = dict(invocation.parameters or {})

            if "config" not in parameters and parameters.get("mode") in {
                "manual_template",
                "historical_reference",
            }:
                input_payload["config"] = parameters
            else:
                input_payload.update(parameters)

            res = self._adapter.run(input_payload)

            meta = getattr(res, "execution_metadata", None) or getattr(res, "meta", None) or {}
            if not getattr(res, "success", False):
                raise RuntimeError(f"pattern_engine failed meta={meta}")

            produced = list(getattr(res, "produced_artifacts", []) or [])
            if not produced:
                raise RuntimeError("Expected at least 1 produced artifact")

            run_dir_raw = meta.get("run_dir")
            if not run_dir_raw:
                raise RuntimeError("Missing run_dir in pattern_engine execution metadata")

            run_dir = Path(str(run_dir_raw)).resolve()
            output_dir = (run_dir / "output").resolve()
            if not output_dir.exists():
                raise RuntimeError(f"Pattern output_dir missing: {output_dir}")

            items: list[OutputItem] = []
            for artifact in produced:
                artifact_path_raw = getattr(artifact, "path", None)
                if not artifact_path_raw:
                    raise RuntimeError(f"Produced artifact missing path: {artifact!r}")

                artifact_path = Path(str(artifact_path_raw)).resolve()
                if not artifact_path.exists():
                    raise RuntimeError(f"Produced artifact not found: {artifact_path}")

                try:
                    relpath = artifact_path.relative_to(output_dir).as_posix()
                except ValueError as exc:
                    raise RuntimeError(
                        f"Produced artifact outside pattern output_dir: {artifact_path}"
                    ) from exc

                items.append(
                    OutputItem(
                        logical_name=artifact_path.stem,
                        filename=relpath,
                        data=artifact_path.read_bytes(),
                    )
                )

            payload = _PatternEnginePayload(items=items)
            return CoreResult(payload=payload, metrics=None)

    return _PatternEngineCore()


def _build_query_engine_core(*, tmp_root=None) -> CorePort:
    from ..adapters.core.core_port import CoreInvocation, CoreResult
    from ..adapters.core.query_engine_adapter import QueryEngineAdapter
    from engines.query_engine.intent import build_query_spec_from_public_intent
    from ..adapters.storage.ports import ArtifactPayload, OutputItem

    class _QueryEnginePayload(ArtifactPayload):
        def __init__(self, *, report_data: bytes, insight_data: bytes) -> None:
            self._report_data = report_data
            self._insight_data = insight_data

        def iter_outputs(self) -> Iterable[OutputItem]:
            return iter(
                (
                    OutputItem(
                        logical_name="query_report",
                        filename="report.json",
                        data=self._report_data,
                    ),
                    OutputItem(
                        logical_name="query_insight",
                        filename="insight.json",
                        data=self._insight_data,
                    ),
                )
            )

    class _QueryEngineCore(CorePort):
        def __init__(self) -> None:
            self._adapter = QueryEngineAdapter(tmp_root=tmp_root)

        def invoke(self, invocation: CoreInvocation) -> CoreResult:
            tool = str(invocation.tool_id)
            if tool != "query_engine":
                raise RuntimeError(f"Unsupported tool_id (query_engine only): {tool}")

            input_payload = dict(invocation.inputs or {})
            query_payload = input_payload.get("query")
            if isinstance(query_payload, dict):
                intent_id = query_payload.get("intent_id")
                params = query_payload.get("params")

                if isinstance(intent_id, str) and isinstance(params, dict):
                    try:
                        input_payload["query"] = build_query_spec_from_public_intent(
                            intent_id,
                            params,
                        )
                    except Exception as exc:
                        raise RuntimeError(
                            f"Failed to normalize public query intent '{intent_id}': {exc}"
                        ) from exc
            input_payload.update(invocation.parameters or {})

            res = self._adapter.run(input_payload)

            meta = getattr(res, "execution_metadata", None) or getattr(res, "meta", None) or {}
            if not getattr(res, "success", False):
                raise RuntimeError(f"query_engine failed meta={meta}")

            produced = list(getattr(res, "produced_artifacts", []) or [])
            if len(produced) != 1:
                raise RuntimeError(f"Expected exactly 1 produced artifact, got {len(produced)}")

            from engines.query_engine.insight.insight_builder import build_insight

            artifact_obj = produced[0]
            artifact_path = Path(getattr(artifact_obj, "path", "")).resolve()
            if not artifact_path.exists():
                raise RuntimeError(f"Produced artifact path not found: {artifact_path}")

            report_obj = json.loads(artifact_path.read_text(encoding="utf-8"))
            insight_obj = build_insight(report_obj)

            report_data = (
                json.dumps(
                    report_obj,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")

            insight_data = (
                json.dumps(
                    insight_obj,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")

            payload = _QueryEnginePayload(
                report_data=report_data,
                insight_data=insight_data,
            )
            return CoreResult(payload=payload, metrics=None)

    return _QueryEngineCore()


_CANONICAL_TOOL_IDS = (
    "query_cli",
    "root_engine",
    "statistical_engine",
    "pattern_engine",
    "query_engine",
)

_REGISTRY: Mapping[str, Callable[..., CorePort]] = MappingProxyType(
    {
        "query_cli": _build_query_cli_core,
        "root_engine": _build_root_engine_core,
        "statistical_engine": _build_statistical_engine_core,
        "pattern_engine": _build_pattern_engine_core,
        "query_engine": _build_query_engine_core,
    }
)


@dataclass(frozen=True)
class ToolRegistry:
    """
    Deterministic tool_id -> CorePort factory resolver.
    """

    @classmethod
    def resolve(cls, tool_id: str, *, tmp_root=None) -> CorePort:
        factory = _REGISTRY.get(tool_id)
        if factory is None:
            raise ToolNotRegisteredError(f"Tool not registered: {tool_id}")
        return factory(tmp_root=tmp_root)

    @classmethod
    def registered_tool_ids(cls) -> tuple[str, ...]:
        return _CANONICAL_TOOL_IDS