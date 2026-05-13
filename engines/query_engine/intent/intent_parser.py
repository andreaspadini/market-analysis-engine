from __future__ import annotations

import re
from typing import Any

from .errors import IntentParseError
from .intent_registry import DEFAULT_SUCCESS_TEMPLATE
from .types import ParsedIntent


_SUCCESS_RATE_BY_RE = re.compile(
    r"^\s*success\s+rate\s+by\s+(?P<dimension>[A-Za-z_][A-Za-z0-9_]*)\s*$",
    re.IGNORECASE,
)

_MEAN_BY_RE = re.compile(
    r"^\s*mean\s*\(\s*(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*\)\s+by\s+(?P<dimension>[A-Za-z_][A-Za-z0-9_]*)\s*$",
    re.IGNORECASE,
)

_DISTRIBUTION_OF_RE = re.compile(
    r"^\s*distribution\s+of\s+(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*$",
    re.IGNORECASE,
)

_PROBABILITY_RE = re.compile(
    r"^\s*P\s*\(\s*(?P<event>.+?)\s*\|\s*(?P<condition>.+?)\s*\)\s*$",
    re.IGNORECASE,
)

_PREDICATE_RE = re.compile(
    r"^\s*(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<operator>==|!=|>=|<=|>|<|=|in)\s*(?P<value>.+?)\s*$",
    re.IGNORECASE,
)


def parse_intent(raw_intent: dict[str, Any]) -> ParsedIntent:
    """
    Parse structured or semi-structured intent input into ParsedIntent.

    Supported inputs:
    - structured JSON
    - semi-structured JSON with 'expression'
    """
    if not isinstance(raw_intent, dict):
        raise IntentParseError("Intent input must be a dict.")

    if "expression" in raw_intent:
        return _parse_expression_input(raw_intent)

    return _parse_structured_input(raw_intent)


def _parse_expression_input(raw_intent: dict[str, Any]) -> ParsedIntent:
    expression = raw_intent.get("expression")
    if not isinstance(expression, str) or not expression.strip():
        raise IntentParseError("expression must be a non-empty string.")

    expression = expression.strip()

    success_match = _SUCCESS_RATE_BY_RE.match(expression)
    if success_match:
        return ParsedIntent(
            metric="success_rate",
            filters=[],
            group_by=[success_match.group("dimension")],
            target_field=str(DEFAULT_SUCCESS_TEMPLATE["target_field"]),
            success_condition=dict(DEFAULT_SUCCESS_TEMPLATE["success_condition"]),  # type: ignore[arg-type]
        )

    mean_match = _MEAN_BY_RE.match(expression)
    if mean_match:
        return ParsedIntent(
            metric="mean",
            filters=[],
            group_by=[mean_match.group("dimension")],
            value_field=mean_match.group("field"),
        )

    distribution_match = _DISTRIBUTION_OF_RE.match(expression)
    if distribution_match:
        return ParsedIntent(
            metric="distribution",
            filters=[],
            group_by=[],
            value_field=distribution_match.group("field"),
            normalization="none",
        )

    probability_match = _PROBABILITY_RE.match(expression)
    if probability_match:
        event_predicate = _parse_predicate(probability_match.group("event"))
        condition_predicate = _parse_predicate(probability_match.group("condition"))

        return ParsedIntent(
            metric="probability",
            filters=[],
            group_by=[],
            event_predicate=event_predicate,
            condition_predicate=condition_predicate,
        )

    raise IntentParseError(f"Unsupported expression pattern: '{expression}'.")


def _parse_structured_input(raw_intent: dict[str, Any]) -> ParsedIntent:
    metric = raw_intent.get("metric")
    if not isinstance(metric, str) or not metric.strip():
        raise IntentParseError("Structured intent requires non-empty string metric.")

    filters = _parse_filters(raw_intent.get("filters", []))
    group_by = _parse_group_by(raw_intent.get("group_by", []))
    value_field = _parse_optional_str(raw_intent.get("value_field"))
    target_field = _parse_optional_str(raw_intent.get("target_field"))
    success_condition = _parse_optional_condition(raw_intent.get("success_condition"))
    event_predicate = _parse_optional_predicate(raw_intent.get("event_predicate"))
    condition_predicate = _parse_optional_predicate(raw_intent.get("condition_predicate"))
    normalization = _parse_optional_str(raw_intent.get("normalization"))
    score_metric = _parse_optional_str(raw_intent.get("score_metric"))
    sort_direction = _parse_optional_str(raw_intent.get("sort_direction"))

    return ParsedIntent(
        metric=metric.strip(),
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


def _parse_filters(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []

    if not isinstance(value, list):
        raise IntentParseError("filters must be a list.")

    parsed_filters: list[dict[str, Any]] = []
    for item in value:
        parsed_filters.append(_parse_predicate_object(item))

    return parsed_filters


def _parse_group_by(value: Any) -> list[str]:
    if value is None:
        return []

    if not isinstance(value, list):
        raise IntentParseError("group_by must be a list.")

    parsed_group_by: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise IntentParseError("group_by must contain only non-empty strings.")
        parsed_group_by.append(item.strip())

    return parsed_group_by


def _parse_optional_str(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str) or not value.strip():
        raise IntentParseError("Expected non-empty string or None.")

    return value.strip()


def _parse_optional_condition(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None

    if not isinstance(value, dict):
        raise IntentParseError("success_condition must be an object.")

    operator = value.get("operator")
    if not isinstance(operator, str) or not operator.strip():
        raise IntentParseError("success_condition.operator must be a non-empty string.")

    if "value" not in value:
        raise IntentParseError("success_condition.value is required.")

    return {
        "operator": operator.strip(),
        "value": value["value"],
    }


def _parse_optional_predicate(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    return _parse_predicate_object(value)


def _parse_predicate_object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IntentParseError("Predicate must be an object.")

    field = value.get("field")
    operator = value.get("operator")

    if not isinstance(field, str) or not field.strip():
        raise IntentParseError("Predicate field must be a non-empty string.")

    if not isinstance(operator, str) or not operator.strip():
        raise IntentParseError("Predicate operator must be a non-empty string.")

    if "value" not in value:
        raise IntentParseError("Predicate value is required.")

    return {
        "field": field.strip(),
        "operator": operator.strip(),
        "value": value["value"],
    }


def _parse_predicate(raw: str) -> dict[str, Any]:
    match = _PREDICATE_RE.match(raw.strip())
    if not match:
        raise IntentParseError(f"Invalid predicate expression: '{raw}'.")

    return {
        "field": match.group("field").strip(),
        "operator": match.group("operator").strip(),
        "value": _parse_scalar_value(match.group("value").strip()),
    }


def _parse_scalar_value(raw: str) -> Any:
    lowered = raw.lower()

    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None

    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]

    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw