from __future__ import annotations

from typing import Any


class InsightValidationError(Exception):
    """Raised when an insight report is invalid."""


def validate_insight_report(report: dict[str, Any]) -> None:
    if not isinstance(report, dict):
        raise InsightValidationError("Insight report must be a dict.")

    required_top_level = {"meta", "summary", "insights"}
    missing = required_top_level - set(report.keys())
    if missing:
        joined = ", ".join(sorted(missing))
        raise InsightValidationError(f"Missing top-level keys: {joined}.")

    meta = report["meta"]
    summary = report["summary"]
    insights = report["insights"]

    if not isinstance(meta, dict):
        raise InsightValidationError("'meta' must be an object/dict.")

    if not isinstance(summary, dict):
        raise InsightValidationError("'summary' must be an object/dict.")

    if not isinstance(insights, list):
        raise InsightValidationError("'insights' must be a list.")

    _validate_meta(meta)
    _validate_summary(summary)

    for index, item in enumerate(insights):
        _validate_insight_item(item, index=index)


def _validate_meta(meta: dict[str, Any]) -> None:
    required = {"source_metric", "derived_metric", "group_by", "filters"}
    missing = required - set(meta.keys())
    if missing:
        joined = ", ".join(sorted(missing))
        raise InsightValidationError(f"Missing meta keys: {joined}.")

    if not isinstance(meta["source_metric"], str):
        raise InsightValidationError("'meta.source_metric' must be a string.")

    if meta["derived_metric"] is not None and not isinstance(meta["derived_metric"], str):
        raise InsightValidationError("'meta.derived_metric' must be a string or null.")

    if not isinstance(meta["group_by"], list):
        raise InsightValidationError("'meta.group_by' must be a list.")

    if not isinstance(meta["filters"], list):
        raise InsightValidationError("'meta.filters' must be a list.")


def _validate_summary(summary: dict[str, Any]) -> None:
    required = {"rows_total", "rows_valid"}
    missing = required - set(summary.keys())
    if missing:
        joined = ", ".join(sorted(missing))
        raise InsightValidationError(f"Missing summary keys: {joined}.")

    if not isinstance(summary["rows_total"], int):
        raise InsightValidationError("'summary.rows_total' must be an int.")

    if summary["rows_valid"] is not None and not isinstance(summary["rows_valid"], int):
        raise InsightValidationError("'summary.rows_valid' must be an int or null.")


def _validate_insight_item(item: Any, *, index: int) -> None:
    if not isinstance(item, dict):
        raise InsightValidationError(f"'insights[{index}]' must be an object/dict.")

    required = {
        "type",
        "dimension",
        "value",
        "metric_value",
        "support",
        "classification",
        "flags",
    }
    missing = required - set(item.keys())
    if missing:
        joined = ", ".join(sorted(missing))
        raise InsightValidationError(
            f"Missing keys in insights[{index}]: {joined}."
        )

    if not isinstance(item["type"], str):
        raise InsightValidationError(f"'insights[{index}].type' must be a string.")

    if item["dimension"] is not None and not isinstance(item["dimension"], str):
        raise InsightValidationError(
            f"'insights[{index}].dimension' must be a string or null."
        )

    if not isinstance(item["support"], dict):
        raise InsightValidationError(
            f"'insights[{index}].support' must be an object/dict."
        )

    _validate_support(item["support"], index=index)

    if not isinstance(item["classification"], str):
        raise InsightValidationError(
            f"'insights[{index}].classification' must be a string."
        )

    if item["classification"] not in {"A", "B", "C", "D"}:
        raise InsightValidationError(
            f"'insights[{index}].classification' must be one of A/B/C/D."
        )

    if not isinstance(item["flags"], list):
        raise InsightValidationError(
            f"'insights[{index}].flags' must be a list."
        )

    for flag in item["flags"]:
        if not isinstance(flag, str):
            raise InsightValidationError(
                f"All flags in 'insights[{index}].flags' must be strings."
            )


def _validate_support(support: dict[str, Any], *, index: int) -> None:
    required = {"rows_valid"}
    missing = required - set(support.keys())
    if missing:
        joined = ", ".join(sorted(missing))
        raise InsightValidationError(
            f"Missing support keys in insights[{index}].support: {joined}."
        )

    if support["rows_valid"] is not None and not isinstance(support["rows_valid"], int):
        raise InsightValidationError(
            f"'insights[{index}].support.rows_valid' must be an int or null."
        )