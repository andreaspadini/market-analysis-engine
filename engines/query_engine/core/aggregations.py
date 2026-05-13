from __future__ import annotations

from math import isnan
from typing import Any, Mapping

import pandas as pd


class AggregationExecutionError(Exception):
    """Raised when an aggregation cannot be executed."""


def agg_count(
    df: pd.DataFrame,
    *,
    value_field: str | None = None,
) -> dict[str, Any]:
    rows_total = int(len(df))

    if value_field is None:
        rows_valid = rows_total
        result = rows_total
    else:
        rows_valid = int(df[value_field].notna().sum())
        result = rows_valid

    return {
        "rows_total": rows_total,
        "rows_valid": rows_valid,
        "result": int(result),
    }


def agg_mean(
    df: pd.DataFrame,
    *,
    value_field: str,
) -> dict[str, Any]:
    series = df[value_field]
    valid = series[series.notna()]
    rows_total = int(len(df))
    rows_valid = int(len(valid))

    result = None if rows_valid == 0 else _to_python_float(valid.mean())

    return {
        "rows_total": rows_total,
        "rows_valid": rows_valid,
        "result": result,
    }


def agg_median(
    df: pd.DataFrame,
    *,
    value_field: str,
) -> dict[str, Any]:
    series = df[value_field]
    valid = series[series.notna()]
    rows_total = int(len(df))
    rows_valid = int(len(valid))

    result = None if rows_valid == 0 else _to_python_float(valid.median())

    return {
        "rows_total": rows_total,
        "rows_valid": rows_valid,
        "result": result,
    }


def agg_std(
    df: pd.DataFrame,
    *,
    value_field: str,
) -> dict[str, Any]:
    series = df[value_field]
    valid = series[series.notna()]
    rows_total = int(len(df))
    rows_valid = int(len(valid))

    result = None
    if rows_valid > 0:
        result = _to_python_float(valid.std(ddof=0))

    return {
        "rows_total": rows_total,
        "rows_valid": rows_valid,
        "result": result,
    }


def agg_success_rate(
    df: pd.DataFrame,
    *,
    target_field: str,
    success_condition: Mapping[str, Any],
) -> dict[str, Any]:
    rows_total = int(len(df))
    target = df[target_field]

    evaluable_mask = target.notna()
    rows_valid = int(evaluable_mask.sum())

    if rows_valid == 0:
        result = None
    else:
        success_mask = _evaluate_target_condition(
            target[evaluable_mask],
            success_condition,
        )
        denominator = int(len(success_mask))
        numerator = int(success_mask.sum())
        result = None if denominator == 0 else _to_python_float(numerator / denominator)

    return {
        "rows_total": rows_total,
        "rows_valid": rows_valid,
        "result": result,
    }


def agg_probability(
    df: pd.DataFrame,
    *,
    event_predicate: Mapping[str, Any],
    condition_predicate: Mapping[str, Any],
) -> dict[str, Any]:
    rows_total = int(len(df))

    condition_evaluable_mask = _predicate_evaluable_mask(df, condition_predicate)
    rows_valid = int(condition_evaluable_mask.sum())

    if rows_valid == 0:
        return {
            "rows_total": rows_total,
            "rows_valid": 0,
            "condition_count": 0,
            "event_and_condition_count": 0,
            "result": None,
        }

    condition_true_mask = _evaluate_simple_predicate(df, condition_predicate)

    event_evaluable_mask = _predicate_evaluable_mask(df, event_predicate)
    denominator_mask = condition_true_mask & event_evaluable_mask
    numerator_mask = denominator_mask & _evaluate_simple_predicate(df, event_predicate)

    condition_count = int(denominator_mask.sum())
    event_and_condition_count = int(numerator_mask.sum())

    result = None
    if condition_count > 0:
        result = _to_python_float(event_and_condition_count / condition_count)

    return {
        "rows_total": rows_total,
        "rows_valid": rows_valid,
        "condition_count": condition_count,
        "event_and_condition_count": event_and_condition_count,
        "result": result,
    }


def agg_distribution(
    df: pd.DataFrame,
    *,
    value_field: str,
    normalization: str = "none",
) -> dict[str, Any]:
    rows_total = int(len(df))
    valid = df[df[value_field].notna()]
    rows_valid = int(len(valid))

    if rows_valid == 0:
        result: dict[str, Any] = {}
    else:
        counts = (
            valid[value_field]
            .astype(str)
            .value_counts(dropna=False, sort=False)
            .sort_index()
        )

        if normalization == "none":
            result = {str(key): int(value) for key, value in counts.items()}
        elif normalization == "share_of_valid_rows":
            result = {
                str(key): _to_python_float(value / rows_valid)
                for key, value in counts.items()
            }
        else:
            raise AggregationExecutionError(
                f"Unsupported distribution normalization '{normalization}'."
            )

    return {
        "rows_total": rows_total,
        "rows_valid": rows_valid,
        "result": result,
    }


def agg_ranking(
    df: pd.DataFrame,
    *,
    group_by: list[str],
    score_metric: str,
    sort_direction: str,
    value_field: str | None = None,
    target_field: str | None = None,
    success_condition: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if len(group_by) != 1:
        raise AggregationExecutionError("ranking requires exactly one group_by field.")

    group_field = group_by[0]
    rows_total = int(len(df))

    if rows_total == 0:
        return {
            "rows_total": 0,
            "result": [],
        }

    grouped_rows: list[dict[str, Any]] = []

    for group_value, group_df in df.groupby(group_field, dropna=False, sort=True):
        if pd.isna(group_value):
            group_key_value = None
        else:
            group_key_value = _to_group_key_value(group_value)

        score_payload = _compute_scalar_metric_for_ranking(
            group_df,
            score_metric=score_metric,
            value_field=value_field,
            target_field=target_field,
            success_condition=success_condition,
        )

        score = score_payload["result"]
        if score is None:
            continue

        grouped_rows.append(
            {
                "group_key": {group_field: group_key_value},
                "score": score,
                "rows_valid": int(score_payload["rows_valid"]),
            }
        )

    reverse = sort_direction == "desc"
    grouped_rows.sort(
        key=lambda item: (_sort_score_key(item["score"], reverse), _stable_group_key_repr(item["group_key"])),
        reverse=False,
    )

    for index, item in enumerate(grouped_rows, start=1):
        item["rank"] = index

    return {
        "rows_total": rows_total,
        "result": grouped_rows,
    }


def dispatch_aggregation(
    metric: str,
    df: pd.DataFrame,
    query: Mapping[str, Any],
) -> dict[str, Any]:
    if metric == "count":
        return agg_count(df, value_field=query.get("value_field"))

    if metric == "mean":
        return agg_mean(df, value_field=query["value_field"])

    if metric == "median":
        return agg_median(df, value_field=query["value_field"])

    if metric == "std":
        return agg_std(df, value_field=query["value_field"])

    if metric in {"success_rate", "true_breakout_rate", "non_failed_rate"}:
        return agg_success_rate(
            df,
            target_field=query["target_field"],
            success_condition=query["success_condition"],
        )

    if metric == "probability":
        return agg_probability(
            df,
            event_predicate=query["event_predicate"],
            condition_predicate=query["condition_predicate"],
        )

    if metric == "distribution":
        return agg_distribution(
            df,
            value_field=query["value_field"],
            normalization=query.get("normalization", "none"),
        )

    if metric == "ranking":
        return agg_ranking(
            df,
            group_by=query["group_by"],
            score_metric=query["score_metric"],
            sort_direction=query["sort_direction"],
            value_field=query.get("value_field"),
            target_field=query.get("target_field"),
            success_condition=query.get("success_condition"),
        )

    raise AggregationExecutionError(f"Unsupported metric '{metric}'.")


def _compute_scalar_metric_for_ranking(
    df: pd.DataFrame,
    *,
    score_metric: str,
    value_field: str | None,
    target_field: str | None,
    success_condition: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if score_metric == "count":
        return agg_count(df, value_field=value_field)

    if score_metric == "mean":
        if value_field is None:
            raise AggregationExecutionError("ranking.mean requires value_field.")
        return agg_mean(df, value_field=value_field)

    if score_metric == "median":
        if value_field is None:
            raise AggregationExecutionError("ranking.median requires value_field.")
        return agg_median(df, value_field=value_field)

    if score_metric == "std":
        if value_field is None:
            raise AggregationExecutionError("ranking.std requires value_field.")
        return agg_std(df, value_field=value_field)

    if score_metric in {"success_rate", "true_breakout_rate", "non_failed_rate"}:
        if target_field is None or success_condition is None:
            raise AggregationExecutionError(
                f"ranking.{score_metric} requires target_field and success_condition."
            )
        return agg_success_rate(
            df,
            target_field=target_field,
            success_condition=success_condition,
        )

    raise AggregationExecutionError(
        f"Unsupported ranking score_metric '{score_metric}'."
    )


def _evaluate_target_condition(
    series: pd.Series,
    condition: Mapping[str, Any],
) -> pd.Series:
    operator = condition["operator"]
    value = condition["value"]

    if operator == "==":
        return series == value
    if operator == "!=":
        return series != value
    if operator == ">":
        return series > value
    if operator == ">=":
        return series >= value
    if operator == "<":
        return series < value
    if operator == "<=":
        return series <= value
    if operator == "in":
        return series.isin(value)

    raise AggregationExecutionError(f"Unsupported target condition operator '{operator}'.")


def _evaluate_simple_predicate(
    df: pd.DataFrame,
    predicate: Mapping[str, Any],
) -> pd.Series:
    field = predicate["field"]
    operator = predicate["operator"]
    value = predicate["value"]
    series = df[field]

    if operator == "==":
        return series.notna() & (series == value)
    if operator == "!=":
        return series.notna() & (series != value)
    if operator == ">":
        return series.notna() & (series > value)
    if operator == ">=":
        return series.notna() & (series >= value)
    if operator == "<":
        return series.notna() & (series < value)
    if operator == "<=":
        return series.notna() & (series <= value)
    if operator == "in":
        return series.notna() & series.isin(value)

    raise AggregationExecutionError(f"Unsupported predicate operator '{operator}'.")


def _predicate_evaluable_mask(
    df: pd.DataFrame,
    predicate: Mapping[str, Any],
) -> pd.Series:
    field = predicate["field"]
    return df[field].notna()


def _to_python_float(value: Any) -> float | None:
    if value is None:
        return None

    converted = float(value)
    if isnan(converted):
        return None
    return converted


def _to_group_key_value(value: Any) -> Any:
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    return str(value)


def _stable_group_key_repr(group_key: Mapping[str, Any]) -> str:
    items = sorted(group_key.items(), key=lambda item: item[0])
    return "|".join(f"{key}={value}" for key, value in items)


def _sort_score_key(score: float, reverse: bool) -> float:
    return -score if reverse else score