from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

from .aggregation_contract import validate_query_against_contract


class QueryPlanningError(Exception):
    """Raised when query planning fails."""


@dataclass(frozen=True)
class ExecutionPlan:
    metric: str
    filters: list[dict[str, Any]]
    group_by: list[str]
    value_field: str | None = None
    target_field: str | None = None
    success_condition: dict[str, Any] | None = None
    event_predicate: dict[str, Any] | None = None
    condition_predicate: dict[str, Any] | None = None
    normalization: str | None = None
    score_metric: str | None = None
    sort_direction: str | None = None
    metadata: dict[str, Any] | None = None


def plan_query(
    query: Mapping[str, Any],
    df: pd.DataFrame,
) -> ExecutionPlan:
    """
    Validate and normalize query into deterministic execution plan.
    """

    if not isinstance(query, Mapping):
        raise QueryPlanningError("Query must be a mapping/object.")

    # 1. Validate against contract
    validate_query_against_contract(query, df)

    # 2. Extract fields with defaults
    metric = query["metric"]

    filters = _normalize_filters(query.get("filters", []))
    group_by = _normalize_group_by(query.get("group_by", []))

    value_field = query.get("value_field")
    target_field = query.get("target_field")

    success_condition = _normalize_optional_dict(query.get("success_condition"))
    event_predicate = _normalize_optional_dict(query.get("event_predicate"))
    condition_predicate = _normalize_optional_dict(query.get("condition_predicate"))

    normalization = query.get("normalization", "none") if metric == "distribution" else None

    score_metric = query.get("score_metric") if metric == "ranking" else None
    sort_direction = query.get("sort_direction") if metric == "ranking" else None
    metadata = _normalize_optional_dict(query.get("metadata"))

    # 3. Build immutable execution plan
    return ExecutionPlan(
        metric=metric,
        filters=filters,
        group_by=group_by,
        value_field=value_field,
        target_field=target_field,
        success_condition=success_condition,
        event_predicate=event_predicate,
        condition_predicate=condition_predicate,
        normalization=normalization,
        score_metric=score_metric,
        sort_direction=sort_direction,
        metadata=metadata,
    )


# -------------------------
# Normalization helpers
# -------------------------

def _normalize_filters(filters: Any) -> list[dict[str, Any]]:
    if filters is None:
        return []

    if not isinstance(filters, list):
        raise QueryPlanningError("filters must be a list.")

    normalized = []
    for predicate in filters:
        if not isinstance(predicate, Mapping):
            raise QueryPlanningError("Each filter must be an object.")
        normalized.append(dict(predicate))

    return normalized


def _normalize_group_by(group_by: Any) -> list[str]:
    if group_by is None:
        return []

    if not isinstance(group_by, list):
        raise QueryPlanningError("group_by must be a list.")

    normalized = []
    for field in group_by:
        if not isinstance(field, str) or not field:
            raise QueryPlanningError("group_by must contain non-empty strings.")
        normalized.append(field)

    return normalized


def _normalize_optional_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None

    if not isinstance(value, Mapping):
        raise QueryPlanningError("Expected object for predicate/condition.")

    return dict(value)