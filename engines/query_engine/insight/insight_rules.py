from __future__ import annotations

from typing import Any


def extract_base_insights(report: dict[str, Any]) -> list[dict[str, Any]]:
    metric = report["meta"]["metric"]

    if report["ranking"] is not None:
        return _extract_from_ranking(report)

    return _extract_from_data(report, metric)


def _extract_from_data(
    report: dict[str, Any],
    metric: str,
) -> list[dict[str, Any]]:
    rows = _normalize_rows_for_metric(report, metric)
    if rows is None:
        return []

    insights: list[dict[str, Any]] = []

    for row in rows:
        group_key = row.get("group_key", {})
        dimension = _extract_dimension(group_key)
        value = _extract_value(group_key)

        if metric in {
            "count",
            "mean",
            "median",
            "std",
            "success_rate",
            "true_breakout_rate",
            "non_failed_rate",
        }:
            insights.append(
                {
                    "type": "scalar",
                    "dimension": dimension,
                    "value": value,
                    "metric_value": row.get("result"),
                    "rows_valid": row.get("rows_valid"),
                }
            )
            continue

        if metric == "distribution":
            insights.append(
                {
                    "type": "distribution",
                    "dimension": dimension,
                    "value": value,
                    "metric_value": row.get("result"),
                    "rows_valid": row.get("rows_valid"),
                }
            )
            continue

        if metric == "probability":
            insights.append(
                {
                    "type": "probability",
                    "dimension": dimension,
                    "value": value,
                    "metric_value": row.get("result"),
                    "rows_valid": row.get("rows_valid"),
                    "condition_count": row.get("condition_count"),
                    "event_and_condition_count": row.get("event_and_condition_count"),
                }
            )
            continue

        insights.append(
            {
                "type": "unknown",
                "dimension": dimension,
                "value": value,
                "metric_value": row.get("result"),
                "rows_valid": row.get("rows_valid"),
            }
        )

    return insights


def _extract_from_ranking(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = report["ranking"]
    if rows is None or len(rows) == 0:
        return []

    insights: list[dict[str, Any]] = []

    top = rows[0]
    top_group_key = top.get("group_key", {})

    insights.append(
        {
            "type": "top_performer",
            "dimension": _extract_dimension(top_group_key),
            "value": _extract_value(top_group_key),
            "metric_value": top.get("score"),
            "rows_valid": top.get("rows_valid"),
        }
    )

    if len(rows) > 1:
        bottom = rows[-1]
        bottom_group_key = bottom.get("group_key", {})

        insights.append(
            {
                "type": "bottom_performer",
                "dimension": _extract_dimension(bottom_group_key),
                "value": _extract_value(bottom_group_key),
                "metric_value": bottom.get("score"),
                "rows_valid": bottom.get("rows_valid"),
            }
        )

    return insights


def _normalize_rows_for_metric(
    report: dict[str, Any],
    metric: str,
) -> list[dict[str, Any]] | None:
    rows = report.get("data")
    if rows is None:
        return None

    if metric != "distribution":
        return rows

    return _expand_distribution_rows(report)


def _expand_distribution_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("data")
    if rows is None:
        return []

    value_field = report.get("meta", {}).get("value_field") or "value"
    expanded: list[dict[str, Any]] = []

    for row in rows:
        group_key = row.get("group_key", {}) or {}
        result = row.get("result")

        # Compatibilità con eventuale forma già "esplosa"
        if isinstance(result, (int, float)):
            expanded.append(row)
            continue

        if not isinstance(result, dict):
            continue

        for category, count in result.items():
            synthetic_group_key = dict(group_key)
            synthetic_group_key[value_field] = category

            expanded.append(
                {
                    "group_key": synthetic_group_key,
                    "rows_total": row.get("rows_total"),
                    "rows_valid": row.get("rows_valid"),
                    "result": count,
                }
            )

    return expanded


def _extract_dimension(group_key: dict[str, Any]) -> str | None:
    if not group_key:
        return None

    keys = list(group_key.keys())
    if len(keys) == 1:
        return keys[0]

    return "|".join(keys)


def _extract_value(group_key: dict[str, Any]) -> Any:
    if not group_key:
        return None

    values = list(group_key.values())
    if len(values) == 1:
        return values[0]

    return dict(group_key)

def _has_parent_groups(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        group_key = row.get("group_key", {}) or {}
        if len(group_key) > 1:
            return True
    return False


def extract_advanced_insights(report: dict[str, Any]) -> list[dict[str, Any]]:
    metric = report["meta"]["metric"]
    rows = _normalize_rows_for_metric(report, metric)

    if not rows or len(rows) < 2:
        return []

    valid_rows = [
        r for r in rows
        if isinstance(r.get("result"), (int, float))
    ]

    if len(valid_rows) < 2:
        return []

    insights: list[dict[str, Any]] = []

    # -------------------------
    # TOP / BOTTOM (grouped)
    # -------------------------
    top = max(valid_rows, key=lambda r: r["result"])
    bottom = min(valid_rows, key=lambda r: r["result"])

    def _build(row: dict[str, Any], insight_type: str) -> dict[str, Any]:
        group_key = row.get("group_key", {})
        return {
            "type": insight_type,
            "dimension": _extract_dimension(group_key),
            "value": _extract_value(group_key),
            "metric_value": row.get("result"),
            "rows_valid": row.get("rows_valid"),
        }

    insights.append(_build(top, "top_performer"))
    insights.append(_build(bottom, "bottom_performer"))

    # -------------------------
    # RANGE GAP
    # -------------------------
    values = [r["result"] for r in valid_rows]
    max_val = max(values)
    min_val = min(values)

    insights.append(
        {
            "type": "range_gap",
            "dimension": None,
            "value": None,
            "metric_value": max_val - min_val,
            "rows_valid": report["summary"]["rows_valid"],
        }
    )

    # -------------------------
    # TOP GAP
    # -------------------------
    sorted_rows = sorted(valid_rows, key=lambda r: r["result"], reverse=True)

    if len(sorted_rows) >= 2:
        gap = sorted_rows[0]["result"] - sorted_rows[1]["result"]

        top_rows_valid = sorted_rows[0].get("rows_valid")
        second_rows_valid = sorted_rows[1].get("rows_valid")

        if top_rows_valid is not None and second_rows_valid is not None:
            gap_rows_valid = min(top_rows_valid, second_rows_valid)
        else:
            gap_rows_valid = report["summary"]["rows_valid"]

        insights.append(
            {
                "type": "top_gap",
                "dimension": None,
                "value": None,
                "metric_value": gap,
                "rows_valid": gap_rows_valid,
            }
        )

    # -------------------------
    # DISTRIBUTION / DOMINANCE
    # -------------------------
    if metric in {
        "distribution",
        "success_rate",
        "true_breakout_rate",
        "non_failed_rate",
    }:
        if metric == "distribution" and _has_parent_groups(valid_rows):
            insights.extend(_extract_grouped_distribution_dominance(valid_rows))
        else:
            total = sum(values)

            if total > 0:
                dominant_row = max(valid_rows, key=lambda r: r["result"])
                dominant_group_key = dominant_row.get("group_key", {})
                max_share = dominant_row["result"] / total

                if max_share >= 0.6:
                    insights.append(
                        {
                            "type": "dominant_segment",
                            "dimension": _extract_dimension(dominant_group_key),
                            "value": _extract_value(dominant_group_key),
                            "metric_value": max_share,
                            "rows_valid": dominant_row.get("rows_valid"),
                        }
                    )
                elif max_share >= 0.45:
                    insights.append(
                        {
                            "type": "imbalanced_distribution",
                            "dimension": _extract_dimension(dominant_group_key),
                            "value": _extract_value(dominant_group_key),
                            "metric_value": max_share,
                            "rows_valid": dominant_row.get("rows_valid"),
                        }
                    )



    return insights

def _extract_grouped_distribution_dominance(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[tuple[str, Any], ...], list[dict[str, Any]]] = {}

    for row in rows:
        group_key = row.get("group_key", {}) or {}
        parent_key = _parent_group_key(group_key)

        if not parent_key:
            continue

        grouped.setdefault(parent_key, []).append(row)

    insights: list[dict[str, Any]] = []

    for parent_key, group_rows in grouped.items():
        values = [
            r["result"]
            for r in group_rows
            if isinstance(r.get("result"), (int, float))
        ]
        if not values:
            continue

        total = sum(values)
        if total <= 0:
            continue

        dominant_row = max(group_rows, key=lambda r: r["result"])
        max_share = dominant_row["result"] / total
        dominant_group_key = dominant_row.get("group_key", {})

        if max_share >= 0.6:
            insights.append(
                {
                    "type": "dominant_segment",
                    "dimension": _extract_dimension(dominant_group_key),
                    "value": _extract_value(dominant_group_key),
                    "metric_value": max_share,
                    "rows_valid": dominant_row.get("rows_valid"),
                }
            )
        elif max_share >= 0.45:
            insights.append(
                {
                    "type": "imbalanced_distribution",
                    "dimension": _extract_dimension(dominant_group_key),
                    "value": _extract_value(dominant_group_key),
                    "metric_value": max_share,
                    "rows_valid": dominant_row.get("rows_valid"),
                }
            )

    return insights


def _parent_group_key(group_key: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    if not group_key or len(group_key) <= 1:
        return tuple()

    items = list(group_key.items())
    return tuple(items[:-1])

