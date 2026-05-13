from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from .aggregations import dispatch_aggregation
from .query_planner import ExecutionPlan


class QueryExecutionError(Exception):
    """Raised when query execution fails."""


def execute_query(
    df: pd.DataFrame,
    plan: ExecutionPlan,
) -> dict[str, Any]:
    """
    Execute query plan against dataset.
    """

    filtered_df = _apply_filters(df, plan.filters)
    query_dict = _plan_to_query_dict(plan)

    # ranking is a special metric:
    # it requires group_by as input semantics, but returns top-level result
    if plan.metric == "ranking":
        payload = dispatch_aggregation(plan.metric, filtered_df, query_dict)
        return {
            "metric": plan.metric,
            "group_by": plan.group_by,
            "filters": plan.filters,
            **payload,
        }

    if not plan.group_by:
        payload = dispatch_aggregation(plan.metric, filtered_df, query_dict)
        return {
            "metric": plan.metric,
            "group_by": [],
            "filters": plan.filters,
            **payload,
        }

    groups_output = []

    grouped = filtered_df.groupby(plan.group_by, dropna=False, sort=True)

    for group_keys, group_df in grouped:
        group_key = _build_group_key(plan.group_by, group_keys)

        payload = dispatch_aggregation(
            plan.metric,
            group_df,
            query_dict,
        )

        groups_output.append(
            {
                "group_key": group_key,
                **payload,
            }
        )

    return {
        "metric": plan.metric,
        "group_by": plan.group_by,
        "filters": plan.filters,
        "groups": groups_output,
    }


def _apply_filters(
    df: pd.DataFrame,
    filters: list[dict[str, Any]],
) -> pd.DataFrame:
    if not filters:
        return df

    mask = pd.Series(True, index=df.index)

    for predicate in filters:
        predicate_mask = _evaluate_filter_predicate(df, predicate)
        mask = mask & predicate_mask

    return df[mask]


def _evaluate_filter_predicate(
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

    raise QueryExecutionError(f"Unsupported filter operator '{operator}'.")


def _build_group_key(
    group_by: list[str],
    group_keys: Any,
) -> dict[str, Any]:
    if not isinstance(group_keys, tuple):
        group_keys = (group_keys,)

    result = {}
    for field, value in zip(group_by, group_keys):
        result[field] = _normalize_group_value(value)

    return result


def _normalize_group_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _plan_to_query_dict(plan: ExecutionPlan) -> dict[str, Any]:
    return {
        "metric": plan.metric,
        "value_field": plan.value_field,
        "target_field": plan.target_field,
        "success_condition": plan.success_condition,
        "event_predicate": plan.event_predicate,
        "condition_predicate": plan.condition_predicate,
        "normalization": plan.normalization,
        "score_metric": plan.score_metric,
        "sort_direction": plan.sort_direction,
        "group_by": plan.group_by,
    }