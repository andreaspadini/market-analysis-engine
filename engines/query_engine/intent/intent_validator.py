from __future__ import annotations

from .errors import IntentValidationError
from .intent_registry import (
    SUPPORTED_DISTRIBUTION_NORMALIZATIONS,
    SUPPORTED_METRICS,
    SUPPORTED_RANKING_SCORE_METRICS,
    SUPPORTED_SORT_DIRECTIONS,
)
from .types import ParsedIntent


def validate_intent(intent: ParsedIntent) -> ParsedIntent:
    """
    Validate intent-layer semantics before mapper canonicalization.

    This validator checks:
    - supported metric
    - required fields by metric
    - unsupported ambiguity
    - ranking constraints
    """
    if intent.metric not in SUPPORTED_METRICS:
        raise IntentValidationError(
            f"Unsupported intent metric '{intent.metric}'. Allowed metrics: {sorted(SUPPORTED_METRICS)}"
        )

    if intent.filters is None:
        raise IntentValidationError("filters cannot be None.")

    if intent.group_by is None:
        raise IntentValidationError("group_by cannot be None.")

    if intent.metric in {
        "success_rate",
        "true_breakout_rate",
        "non_failed_rate",
    }:
        _validate_success_rate(intent)

    elif intent.metric in {"mean", "median", "std"}:
        _validate_numeric_aggregate(intent)

    elif intent.metric == "count":
        _validate_count(intent)

    elif intent.metric == "distribution":
        _validate_distribution(intent)

    elif intent.metric == "probability":
        _validate_probability(intent)

    elif intent.metric == "ranking":
        _validate_ranking(intent)

    return intent


def _validate_success_rate(intent: ParsedIntent) -> None:
    if not intent.group_by:
        raise IntentValidationError("success_rate requires non-empty group_by in QRY-2 v1.")

    if intent.value_field is not None:
        raise IntentValidationError(
            f"{intent.metric} does not accept value_field."
        )

    if not intent.target_field:
        raise IntentValidationError(
            f"{intent.metric} requires target_field."
        )

    if not isinstance(intent.success_condition, dict):
        raise IntentValidationError(
            f"{intent.metric} requires success_condition object."
        )

    _validate_condition_shape(intent.success_condition)

    if intent.event_predicate is not None or intent.condition_predicate is not None:
        raise IntentValidationError("success_rate does not accept event_predicate/condition_predicate.")

    if intent.score_metric is not None or intent.sort_direction is not None:
        raise IntentValidationError("success_rate does not accept ranking fields.")


def _validate_numeric_aggregate(intent: ParsedIntent) -> None:
    if not intent.value_field:
        raise IntentValidationError(f"{intent.metric} requires value_field.")

    if not intent.group_by:
        raise IntentValidationError(f"{intent.metric} requires non-empty group_by in QRY-2 v1.")

    if intent.target_field is not None or intent.success_condition is not None:
        raise IntentValidationError(f"{intent.metric} does not accept success fields.")

    if intent.event_predicate is not None or intent.condition_predicate is not None:
        raise IntentValidationError(f"{intent.metric} does not accept probability predicates.")

    if intent.normalization is not None:
        raise IntentValidationError(f"{intent.metric} does not accept normalization.")

    if intent.score_metric is not None or intent.sort_direction is not None:
        raise IntentValidationError(f"{intent.metric} does not accept ranking fields.")


def _validate_count(intent: ParsedIntent) -> None:
    if intent.target_field is not None or intent.success_condition is not None:
        raise IntentValidationError("count does not accept success fields.")

    if intent.event_predicate is not None or intent.condition_predicate is not None:
        raise IntentValidationError("count does not accept probability predicates.")

    if intent.normalization is not None:
        raise IntentValidationError("count does not accept normalization.")

    if intent.score_metric is not None or intent.sort_direction is not None:
        raise IntentValidationError("count does not accept ranking fields.")


def _validate_distribution(intent: ParsedIntent) -> None:
    if not intent.value_field:
        raise IntentValidationError("distribution requires value_field.")

    if intent.target_field is not None or intent.success_condition is not None:
        raise IntentValidationError("distribution does not accept success fields.")

    if intent.event_predicate is not None or intent.condition_predicate is not None:
        raise IntentValidationError("distribution does not accept probability predicates.")

    if intent.score_metric is not None or intent.sort_direction is not None:
        raise IntentValidationError("distribution does not accept ranking fields.")

    normalization = intent.normalization or "none"
    if normalization not in SUPPORTED_DISTRIBUTION_NORMALIZATIONS:
        raise IntentValidationError(
            "distribution.normalization must be one of "
            f"{sorted(SUPPORTED_DISTRIBUTION_NORMALIZATIONS)}."
        )


def _validate_probability(intent: ParsedIntent) -> None:
    if intent.group_by:
        raise IntentValidationError("probability does not accept group_by in QRY-2 v1.")

    if intent.value_field is not None:
        raise IntentValidationError("probability does not accept value_field.")

    if intent.target_field is not None or intent.success_condition is not None:
        raise IntentValidationError("probability does not accept success fields.")

    if not isinstance(intent.event_predicate, dict):
        raise IntentValidationError("probability requires event_predicate.")

    if not isinstance(intent.condition_predicate, dict):
        raise IntentValidationError("probability requires condition_predicate.")

    _validate_predicate_shape(intent.event_predicate)
    _validate_predicate_shape(intent.condition_predicate)

    if intent.normalization is not None:
        raise IntentValidationError("probability does not accept normalization.")

    if intent.score_metric is not None or intent.sort_direction is not None:
        raise IntentValidationError("probability does not accept ranking fields.")


def _validate_ranking(intent: ParsedIntent) -> None:
    if len(intent.group_by) != 1:
        raise IntentValidationError("ranking requires exactly one group_by field.")

    if not intent.score_metric:
        raise IntentValidationError("ranking requires score_metric.")

    if intent.score_metric not in SUPPORTED_RANKING_SCORE_METRICS:
        raise IntentValidationError(
            "ranking.score_metric must be one of "
            f"{sorted(SUPPORTED_RANKING_SCORE_METRICS)}."
        )

    if not intent.sort_direction:
        raise IntentValidationError("ranking requires sort_direction.")

    if intent.sort_direction not in SUPPORTED_SORT_DIRECTIONS:
        raise IntentValidationError(
            "ranking.sort_direction must be one of "
            f"{sorted(SUPPORTED_SORT_DIRECTIONS)}."
        )

    if intent.normalization is not None:
        raise IntentValidationError("ranking does not accept normalization.")

    if intent.event_predicate is not None or intent.condition_predicate is not None:
        raise IntentValidationError("ranking does not accept probability predicates.")

    if intent.score_metric in {"mean", "median", "std"} and not intent.value_field:
        raise IntentValidationError(f"ranking.{intent.score_metric} requires value_field.")

    if intent.score_metric == "success_rate":
        if not intent.target_field:
            raise IntentValidationError("ranking.success_rate requires target_field.")
        if not isinstance(intent.success_condition, dict):
            raise IntentValidationError("ranking.success_rate requires success_condition.")
        _validate_condition_shape(intent.success_condition)


def _validate_predicate_shape(predicate: dict[str, object]) -> None:
    field = predicate.get("field")
    operator = predicate.get("operator")

    if not isinstance(field, str) or not field:
        raise IntentValidationError("Predicate field must be non-empty string.")

    if not isinstance(operator, str) or not operator:
        raise IntentValidationError("Predicate operator must be non-empty string.")

    if "value" not in predicate:
        raise IntentValidationError("Predicate value is required.")


def _validate_condition_shape(condition: dict[str, object]) -> None:
    operator = condition.get("operator")

    if not isinstance(operator, str) or not operator:
        raise IntentValidationError("success_condition.operator must be non-empty string.")

    if "value" not in condition:
        raise IntentValidationError("success_condition.value is required.")