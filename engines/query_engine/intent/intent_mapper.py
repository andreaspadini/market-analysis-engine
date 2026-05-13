from __future__ import annotations

from typing import Any

from .errors import IntentMappingError
from .intent_registry import (
    DEFAULT_NON_FAILED_TEMPLATE,
    DEFAULT_SUCCESS_TEMPLATE,
    DEFAULT_TRUE_BREAKOUT_TEMPLATE,
    DIMENSION_ALIASES,
    FIELD_ALIASES,
    OPERATOR_ALIASES,
)
from .types import MappedIntent, ParsedIntent


_RATE_METRICS = {"success_rate", "true_breakout_rate", "non_failed_rate"}


def map_intent(intent: ParsedIntent) -> MappedIntent:
    """
    Map a validated ParsedIntent into canonical query-engine fields.

    This is the ONLY layer allowed to canonicalize aliases such as:
    - session -> session_calc
    - = -> ==
    """
    metric = intent.metric

    filters = [_map_predicate(predicate) for predicate in intent.filters]
    group_by = [_map_dimension(field) for field in intent.group_by]
    value_field = _map_optional_field(intent.value_field)
    target_field = _map_optional_field(intent.target_field)
    success_condition = _map_optional_condition(intent.success_condition)
    event_predicate = _map_optional_predicate(intent.event_predicate)
    condition_predicate = _map_optional_predicate(intent.condition_predicate)
    normalization = intent.normalization
    score_metric = intent.score_metric
    sort_direction = intent.sort_direction

    if metric in _RATE_METRICS:
        target_field, success_condition = _resolve_success_template(
            metric=metric,
            target_field=target_field,
            success_condition=success_condition,
        )

    return MappedIntent(
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
    )


def _resolve_success_template(
    *,
    metric: str,
    target_field: str | None,
    success_condition: dict[str, Any] | None,
) -> tuple[str, dict[str, Any]]:
    if target_field is None and success_condition is None:
        template = _default_success_template_for_metric(metric)
        return (
            str(template["target_field"]),
            dict(template["success_condition"]),  # type: ignore[arg-type]
        )

    if target_field is None or success_condition is None:
        raise IntentMappingError(
            f"{metric} mapping requires both target_field and success_condition."
        )

    return target_field, success_condition


def _default_success_template_for_metric(metric: str) -> dict[str, object]:
    if metric == "true_breakout_rate":
        return dict(DEFAULT_TRUE_BREAKOUT_TEMPLATE)
    if metric == "non_failed_rate":
        return dict(DEFAULT_NON_FAILED_TEMPLATE)
    return dict(DEFAULT_SUCCESS_TEMPLATE)


def _map_dimension(field: str) -> str:
    canonical = DIMENSION_ALIASES.get(field)
    if canonical is None:
        raise IntentMappingError(f"Unsupported dimension alias '{field}'.")
    return canonical


def _map_optional_field(field: str | None) -> str | None:
    if field is None:
        return None
    return _map_field(field)


def _map_field(field: str) -> str:
    canonical = FIELD_ALIASES.get(field)
    if canonical is None:
        raise IntentMappingError(f"Unsupported field alias '{field}'.")
    return canonical


def _map_optional_condition(condition: dict[str, Any] | None) -> dict[str, Any] | None:
    if condition is None:
        return None

    return {
        "operator": _map_operator(condition["operator"]),
        "value": condition["value"],
    }


def _map_optional_predicate(predicate: dict[str, Any] | None) -> dict[str, Any] | None:
    if predicate is None:
        return None
    return _map_predicate(predicate)


def _map_predicate(predicate: dict[str, Any]) -> dict[str, Any]:
    return {
        "field": _map_field(str(predicate["field"])),
        "operator": _map_operator(str(predicate["operator"])),
        "value": predicate["value"],
    }


def _map_operator(operator: str) -> str:
    canonical = OPERATOR_ALIASES.get(operator)
    if canonical is None:
        raise IntentMappingError(f"Unsupported operator alias '{operator}'.")
    return canonical
