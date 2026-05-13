from __future__ import annotations

from typing import Any

from .errors import QueryBuildError
from .types import MappedIntent


def build_query_spec(intent: MappedIntent) -> dict[str, Any]:
    """
    Build canonical query spec compatible with query_engine.core.plan_query.

    Canonical top-level field order:
    1. metric
    2. filters
    3. group_by
    4. value_field
    5. target_field
    6. success_condition
    7. event_predicate
    8. condition_predicate
    9. normalization
    10. score_metric
    11. sort_direction
    """
    if not intent.metric:
        raise QueryBuildError("Mapped intent must contain metric.")

    query: dict[str, Any] = {
        "metric": intent.metric,
        "filters": list(intent.filters),
        "group_by": list(intent.group_by),
    }

    if intent.value_field is not None:
        query["value_field"] = intent.value_field

    if intent.target_field is not None:
        query["target_field"] = intent.target_field

    if intent.success_condition is not None:
        query["success_condition"] = _build_condition(intent.success_condition)

    if intent.event_predicate is not None:
        query["event_predicate"] = _build_predicate(intent.event_predicate)

    if intent.condition_predicate is not None:
        query["condition_predicate"] = _build_predicate(intent.condition_predicate)

    if intent.normalization is not None:
        query["normalization"] = intent.normalization

    if intent.score_metric is not None:
        query["score_metric"] = intent.score_metric

    if intent.sort_direction is not None:
        query["sort_direction"] = intent.sort_direction

    return query


def _build_predicate(predicate: dict[str, Any]) -> dict[str, Any]:
    if "field" not in predicate or "operator" not in predicate or "value" not in predicate:
        raise QueryBuildError("Predicate must contain field, operator, value.")

    return {
        "field": predicate["field"],
        "operator": predicate["operator"],
        "value": predicate["value"],
    }


def _build_condition(condition: dict[str, Any]) -> dict[str, Any]:
    if "operator" not in condition or "value" not in condition:
        raise QueryBuildError("success_condition must contain operator and value.")

    return {
        "operator": condition["operator"],
        "value": condition["value"],
    }