from __future__ import annotations

from typing import Any, Mapping

from .errors import ReportValidationError


def validate_report(report: Mapping[str, Any]) -> None:
    """
    Validate final QRY-3 report structure.

    Raises:
        ReportValidationError if contract is violated.
    """
    if not isinstance(report, Mapping):
        raise ReportValidationError("Report must be an object.")

    _validate_top_level(report)

    metric = report["meta"]["metric"]
    data = report["data"]
    ranking = report["ranking"]

    if metric == "ranking":
        _validate_ranking_mode(data, ranking)
    else:
        _validate_data_mode(data, ranking)

    _validate_summary(report["summary"])


# -------------------------------------------------
# Top-level
# -------------------------------------------------

def _validate_top_level(report: Mapping[str, Any]) -> None:
    required_keys = ("meta", "summary", "data", "ranking")

    missing = [k for k in required_keys if k not in report]
    if missing:
        raise ReportValidationError(
            f"Missing top-level keys: {', '.join(missing)}"
        )

    if not isinstance(report["meta"], Mapping):
        raise ReportValidationError("'meta' must be an object.")

    if not isinstance(report["summary"], Mapping):
        raise ReportValidationError("'summary' must be an object.")


# -------------------------------------------------
# Data mode (non-ranking)
# -------------------------------------------------

def _validate_data_mode(data: Any, ranking: Any) -> None:
    if ranking is not None:
        raise ReportValidationError(
            "Non-ranking report must have 'ranking = null'."
        )

    if not isinstance(data, list):
        raise ReportValidationError("'data' must be a list for non-ranking metrics.")

    for row in data:
        _validate_data_row(row)


def _validate_data_row(row: Any) -> None:
    if not isinstance(row, Mapping):
        raise ReportValidationError("Each data row must be an object.")

    required = ("group_key", "rows_total", "rows_valid", "result")
    missing = [k for k in required if k not in row]
    if missing:
        raise ReportValidationError(
            f"Missing keys in data row: {', '.join(missing)}"
        )

    if not isinstance(row["group_key"], Mapping):
        raise ReportValidationError("'group_key' must be an object.")

    if not isinstance(row["rows_total"], int):
        raise ReportValidationError("'rows_total' must be int.")

    if not isinstance(row["rows_valid"], int):
        raise ReportValidationError("'rows_valid' must be int.")

    # optional fields (probability)
    if "condition_count" in row and not isinstance(row["condition_count"], int):
        raise ReportValidationError("'condition_count' must be int.")

    if (
        "event_and_condition_count" in row
        and not isinstance(row["event_and_condition_count"], int)
    ):
        raise ReportValidationError("'event_and_condition_count' must be int.")


# -------------------------------------------------
# Ranking mode
# -------------------------------------------------

def _validate_ranking_mode(data: Any, ranking: Any) -> None:
    if data is not None:
        raise ReportValidationError(
            "Ranking report must have 'data = null'."
        )

    if not isinstance(ranking, list):
        raise ReportValidationError("'ranking' must be a list.")

    for row in ranking:
        _validate_ranking_row(row)


def _validate_ranking_row(row: Any) -> None:
    if not isinstance(row, Mapping):
        raise ReportValidationError("Each ranking row must be an object.")

    required = ("rank", "group_key", "score", "rows_valid")
    missing = [k for k in required if k not in row]
    if missing:
        raise ReportValidationError(
            f"Missing keys in ranking row: {', '.join(missing)}"
        )

    if not isinstance(row["rank"], int):
        raise ReportValidationError("'rank' must be int.")

    if not isinstance(row["group_key"], Mapping):
        raise ReportValidationError("'group_key' must be an object.")

    if not isinstance(row["rows_valid"], int):
        raise ReportValidationError("'rows_valid' must be int.")


# -------------------------------------------------
# Summary
# -------------------------------------------------

def _validate_summary(summary: Mapping[str, Any]) -> None:
    required = ("rows_total", "rows_valid")

    missing = [k for k in required if k not in summary]
    if missing:
        raise ReportValidationError(
            f"Missing keys in summary: {', '.join(missing)}"
        )

    if not isinstance(summary["rows_total"], int):
        raise ReportValidationError("'summary.rows_total' must be int.")

    if summary["rows_valid"] is not None and not isinstance(
        summary["rows_valid"], int
    ):
        raise ReportValidationError(
            "'summary.rows_valid' must be int or null."
        )