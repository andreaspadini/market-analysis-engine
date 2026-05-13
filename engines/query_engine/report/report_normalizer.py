from __future__ import annotations

from typing import Any, Mapping

from engines.query_engine.core.query_planner import ExecutionPlan

from .errors import ReportNormalizationError
from .report_types import ReportRankingRow, ReportRow


def normalize_query_result(
    plan: ExecutionPlan,
    query_result: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Normalize QRY-1 output into canonical QRY-3 internal shape.

    Returned shape:
    {
        "summary": {
            "rows_total": int,
            "rows_valid": int | None,
        },
        "data": list[ReportRow] | None,
        "ranking": list[ReportRankingRow] | None,
    }
    """
    if not isinstance(query_result, Mapping):
        raise ReportNormalizationError("query_result must be a mapping/object.")

    if plan.metric == "ranking":
        ranking_rows = _normalize_ranking_result(query_result)
        summary = _build_ranking_summary(query_result)

        return {
            "summary": summary,
            "data": None,
            "ranking": ranking_rows,
        }

    if plan.group_by:
        data_rows = _normalize_grouped_result(query_result)
    else:
        data_rows = _normalize_scalar_result(query_result)

    data_rows = _sort_data_rows_by_group_key(data_rows)
    summary = _build_data_summary(data_rows)

    return {
        "summary": summary,
        "data": data_rows,
        "ranking": None,
    }


def _normalize_scalar_result(
    query_result: Mapping[str, Any],
) -> list[ReportRow]:
    _require_keys(
        query_result,
        required_keys=("rows_total", "rows_valid", "result"),
        context="scalar query result",
    )

    row = _build_report_row(
        source=query_result,
        group_key={},
    )

    return [row]


def _normalize_grouped_result(
    query_result: Mapping[str, Any],
) -> list[ReportRow]:
    _require_keys(
        query_result,
        required_keys=("groups",),
        context="grouped query result",
    )

    groups = query_result["groups"]
    if not isinstance(groups, list):
        raise ReportNormalizationError("'groups' must be a list.")

    rows: list[ReportRow] = []

    for group_payload in groups:
        if not isinstance(group_payload, Mapping):
            raise ReportNormalizationError("Each grouped payload must be an object.")

        _require_keys(
            group_payload,
            required_keys=("group_key", "rows_total", "rows_valid", "result"),
            context="group row",
        )

        group_key = group_payload["group_key"]
        if not isinstance(group_key, Mapping):
            raise ReportNormalizationError("'group_key' must be an object.")

        row = _build_report_row(
            source=group_payload,
            group_key=dict(group_key),
        )
        rows.append(row)

    return rows


def _normalize_ranking_result(
    query_result: Mapping[str, Any],
) -> list[ReportRankingRow]:
    _require_keys(
        query_result,
        required_keys=("rows_total", "result"),
        context="ranking query result",
    )

    ranking_payload = query_result["result"]
    if not isinstance(ranking_payload, list):
        raise ReportNormalizationError("Ranking 'result' must be a list.")

    rows: list[ReportRankingRow] = []

    for item in ranking_payload:
        if not isinstance(item, Mapping):
            raise ReportNormalizationError("Each ranking row must be an object.")

        _require_keys(
            item,
            required_keys=("rank", "group_key", "score", "rows_valid"),
            context="ranking row",
        )

        group_key = item["group_key"]
        if not isinstance(group_key, Mapping):
            raise ReportNormalizationError("Ranking 'group_key' must be an object.")

        rows.append(
            ReportRankingRow(
                rank=_require_int(item["rank"], "ranking.rank"),
                group_key=dict(group_key),
                score=item["score"],
                rows_valid=_require_int(item["rows_valid"], "ranking.rows_valid"),
            )
        )

    return rows


def _build_report_row(
    source: Mapping[str, Any],
    group_key: dict[str, Any],
) -> ReportRow:
    condition_count = source.get("condition_count")
    event_and_condition_count = source.get("event_and_condition_count")

    return ReportRow(
        group_key=group_key,
        rows_total=_require_int(source["rows_total"], "rows_total"),
        rows_valid=_require_int(source["rows_valid"], "rows_valid"),
        result=source["result"],
        condition_count=(
            None
            if condition_count is None
            else _require_int(condition_count, "condition_count")
        ),
        event_and_condition_count=(
            None
            if event_and_condition_count is None
            else _require_int(event_and_condition_count, "event_and_condition_count")
        ),
    )


def _build_data_summary(
    data_rows: list[ReportRow],
) -> dict[str, int]:
    rows_total = sum(row.rows_total for row in data_rows)
    rows_valid = sum(row.rows_valid for row in data_rows)

    return {
        "rows_total": rows_total,
        "rows_valid": rows_valid,
    }


def _build_ranking_summary(
    query_result: Mapping[str, Any],
) -> dict[str, int | None]:
    rows_total = _require_int(query_result["rows_total"], "rows_total")

    return {
        "rows_total": rows_total,
        "rows_valid": None,
    }


def _sort_data_rows_by_group_key(
    rows: list[ReportRow],
) -> list[ReportRow]:
    return sorted(
        rows,
        key=lambda row: _stable_group_key_repr(row.group_key),
    )


def _stable_group_key_repr(
    group_key: Mapping[str, Any],
) -> str:
    items = sorted(group_key.items(), key=lambda item: item[0])
    return "|".join(f"{key}={value}" for key, value in items)


def _require_keys(
    payload: Mapping[str, Any],
    *,
    required_keys: tuple[str, ...],
    context: str,
) -> None:
    missing = [key for key in required_keys if key not in payload]
    if missing:
        joined = ", ".join(missing)
        raise ReportNormalizationError(
            f"Missing required keys in {context}: {joined}."
        )


def _require_int(
    value: Any,
    field_name: str,
) -> int:
    if not isinstance(value, int):
        raise ReportNormalizationError(f"'{field_name}' must be an integer.")
    return value