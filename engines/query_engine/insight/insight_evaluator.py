from __future__ import annotations

from typing import Any


def evaluate_insight(raw_insight: dict[str, Any]) -> tuple[str, list[str]]:
    flags: list[str] = []

    insight_type = raw_insight.get("type")
    rows_valid = raw_insight.get("rows_valid")
    metric_value = raw_insight.get("metric_value")

    if rows_valid is None or rows_valid <= 0:
        return "D", ["no_valid_rows"]

    if not _is_interpretable(insight_type, metric_value):
        return "D", ["non_interpretable_metric"]

    if rows_valid < 5:
        flags.append("low_sample_size")

    if _is_near_zero_signal(insight_type, metric_value):
        flags.append("weak_signal")

    classification = _classify(
        insight_type=insight_type,
        metric_value=metric_value,
        rows_valid=rows_valid,
        flags=flags,
    )

    return classification, flags


def _is_interpretable(insight_type: Any, metric_value: Any) -> bool:
    if insight_type in {
        "top_gap",
        "range_gap",
        "top_performer",
        "bottom_performer",
        "scalar",
        "distribution",
        "probability",
        "dominant_segment",
        "imbalanced_distribution",
    }:
        return isinstance(metric_value, (int, float))

    return metric_value is not None


def _is_near_zero_signal(insight_type: Any, metric_value: Any) -> bool:
    if not isinstance(metric_value, (int, float)):
        return True

    value = abs(float(metric_value))

    if insight_type in {"top_gap", "range_gap"}:
        return value <= 1e-9

    if insight_type in {"dominant_segment", "imbalanced_distribution", "probability"}:
        return value < 0.15

    if insight_type == "distribution":
        return value <= 0

    if insight_type in {"top_performer", "bottom_performer", "scalar"}:
        return value <= 0

    return value <= 0


def _classify(
    *,
    insight_type: Any,
    metric_value: Any,
    rows_valid: int,
    flags: list[str],
) -> str:
    if "low_sample_size" in flags and "weak_signal" in flags:
        return "C"

    if "low_sample_size" in flags:
        return "C"

    if "weak_signal" in flags:
        return "C"

    if _is_strong_signal(insight_type, metric_value, rows_valid):
        return "A"

    return "B"


def _is_strong_signal(insight_type: Any, metric_value: Any, rows_valid: int) -> bool:
    if not isinstance(metric_value, (int, float)):
        return False

    value = abs(float(metric_value))

    if insight_type == "dominant_segment":
        return value >= 0.60 and rows_valid >= 8

    if insight_type == "imbalanced_distribution":
        return value >= 0.45 and rows_valid >= 8

    if insight_type == "probability":
        return value >= 0.70 and rows_valid >= 8

    if insight_type in {"top_gap", "range_gap"}:
        return value > 0 and rows_valid >= 8

    if insight_type in {"top_performer", "bottom_performer"}:
        return value > 0 and rows_valid >= 8

    if insight_type in {"distribution", "scalar"}:
        return value > 0 and rows_valid >= 8

    return False