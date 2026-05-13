from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .errors import IntentValidationError
from .intent_mapper import map_intent
from .intent_parser import parse_intent
from .intent_validator import validate_intent
from .query_builder import build_query_spec


Predicate = dict[str, Any]


@dataclass(frozen=True)
class PublicIntentSpec:
    intent_id: str
    params_schema: dict[str, dict[str, Any]]
    raw_intent_builder: Callable[[dict[str, Any]], dict[str, Any]]
    deprecated: bool = False
    replacement_intent_id: str | None = None
    semantic_note: str | None = None


def list_public_intents() -> dict[str, PublicIntentSpec]:
    return dict(_PUBLIC_INTENT_REGISTRY)

def list_public_intent_catalog() -> list[dict[str, Any]]:
    return [
        {
            "intent_id": spec.intent_id,
            "params_schema": dict(spec.params_schema),
            "deprecated": spec.deprecated,
            "replacement_intent_id": spec.replacement_intent_id,
            "semantic_note": spec.semantic_note,
        }
        for spec in _PUBLIC_INTENT_REGISTRY.values()
    ]


def get_public_intent_spec(intent_id: str) -> PublicIntentSpec:
    try:
        return _PUBLIC_INTENT_REGISTRY[intent_id]
    except KeyError as exc:
        raise IntentValidationError(
            f"Unsupported public intent_id '{intent_id}'. "
            f"Allowed intent_ids: {sorted(_PUBLIC_INTENT_REGISTRY.keys())}"
        ) from exc


def validate_public_intent(intent_id: str, params: Mapping[str, Any] | None) -> None:
    spec = get_public_intent_spec(intent_id)
    params_dict = _normalize_params(params)
    _validate_params_against_schema(spec.params_schema, params_dict)


def build_query_spec_from_public_intent(
    intent_id: str,
    params: Mapping[str, Any] | None,
) -> dict[str, Any]:
    spec = get_public_intent_spec(intent_id)
    params_dict = _normalize_params(params)

    _validate_params_against_schema(spec.params_schema, params_dict)

    raw_intent = spec.raw_intent_builder(params_dict)
    parsed = parse_intent(raw_intent)
    validated = validate_intent(parsed)
    mapped = map_intent(validated)
    query_spec = build_query_spec(mapped)

    if spec.deprecated:
        query_spec.setdefault("metadata", {})
        query_spec["metadata"]["deprecated_intent_id"] = spec.intent_id
        query_spec["metadata"]["replacement_intent_id"] = spec.replacement_intent_id
        query_spec["metadata"]["semantic_note"] = spec.semantic_note

    return query_spec

def _normalize_params(params: Mapping[str, Any] | None) -> dict[str, Any]:
    if params is None:
        return {}

    if not isinstance(params, Mapping):
        raise IntentValidationError("Public intent params must be an object/dict.")

    return dict(params)


def _validate_params_against_schema(
    schema: Mapping[str, dict[str, Any]],
    params: Mapping[str, Any],
) -> None:
    extra = set(params.keys()) - set(schema.keys())
    if extra:
        raise IntentValidationError(
            f"Public intent params contain extra keys: {sorted(extra)}"
        )

    for name, rules in schema.items():
        required = bool(rules.get("required", False))
        if required and name not in params:
            raise IntentValidationError(
                f"Public intent params missing required key '{name}'"
            )

        if name not in params:
            continue

        value = params[name]
        expected_type = rules.get("type", "any")

        if expected_type == "string":
            if not isinstance(value, str):
                raise IntentValidationError(f"Public intent param '{name}' must be string")

        elif expected_type == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                raise IntentValidationError(f"Public intent param '{name}' must be int")
            if "min" in rules and value < int(rules["min"]):
                raise IntentValidationError(f"Public intent param '{name}' is below min")
            if "max" in rules and value > int(rules["max"]):
                raise IntentValidationError(f"Public intent param '{name}' is above max")

        elif expected_type == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise IntentValidationError(f"Public intent param '{name}' must be float")
            numeric_value = float(value)
            if "min" in rules and numeric_value < float(rules["min"]):
                raise IntentValidationError(f"Public intent param '{name}' is below min")
            if "max" in rules and numeric_value > float(rules["max"]):
                raise IntentValidationError(f"Public intent param '{name}' is above max")

        elif expected_type == "bool":
            if not isinstance(value, bool):
                raise IntentValidationError(f"Public intent param '{name}' must be bool")

        elif expected_type == "enum":
            allowed_values = list(rules.get("values", []))
            if value not in allowed_values:
                raise IntentValidationError(
                    f"Public intent param '{name}' must be one of {allowed_values}"
                )

        elif expected_type == "string_list":
            if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
                raise IntentValidationError(
                    f"Public intent param '{name}' must be a list of non-empty strings"
                )

        elif expected_type == "predicate_list":
            if not isinstance(value, list):
                raise IntentValidationError(
                    f"Public intent param '{name}' must be a list"
                )
            for predicate in value:
                _validate_predicate_object(predicate, param_name=name)

        elif expected_type == "predicate":
            _validate_predicate_object(value, param_name=name)

        elif expected_type == "condition":
            _validate_condition_object(value, param_name=name)

        elif expected_type == "any":
            pass

        else:
            raise IntentValidationError(
                f"Public intent param '{name}' has unsupported schema type '{expected_type}'"
            )


def _validate_predicate_object(value: Any, *, param_name: str) -> None:
    if not isinstance(value, dict):
        raise IntentValidationError(
            f"Public intent param '{param_name}' must contain predicate objects"
        )

    field = value.get("field")
    operator = value.get("operator")

    if not isinstance(field, str) or not field.strip():
        raise IntentValidationError(
            f"Public intent predicate '{param_name}.field' must be non-empty string"
        )

    if not isinstance(operator, str) or not operator.strip():
        raise IntentValidationError(
            f"Public intent predicate '{param_name}.operator' must be non-empty string"
        )

    if "value" not in value:
        raise IntentValidationError(
            f"Public intent predicate '{param_name}.value' is required"
        )


def _validate_condition_object(value: Any, *, param_name: str) -> None:
    if not isinstance(value, dict):
        raise IntentValidationError(
            f"Public intent param '{param_name}' must be an object"
        )

    operator = value.get("operator")
    if not isinstance(operator, str) or not operator.strip():
        raise IntentValidationError(
            f"Public intent condition '{param_name}.operator' must be non-empty string"
        )

    if "value" not in value:
        raise IntentValidationError(
            f"Public intent condition '{param_name}.value' is required"
        )


def _build_success_by_weekday_report(_: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "success_rate",
        "filters": [],
        "group_by": ["weekday"],
        "target_field": "is_failed",
        "success_condition": {
            "operator": "==",
            "value": False,
        },
    }


def _build_success_rate(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "success_rate",
        "filters": list(params.get("filters", [])),
        "group_by": list(params.get("group_by", [])),
        "target_field": params.get("target_field", "is_failed"),
        "success_condition": dict(
            params.get(
                "success_condition",
                {
                    "operator": "==",
                    "value": False,
                },
            )
        ),
    }

def _build_true_breakout_rate(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "true_breakout_rate",
        "filters": list(params.get("filters", [])),
        "group_by": list(params.get("group_by", [])),
        "target_field": params.get("target_field", "breakout_outcome"),
        "success_condition": dict(
            params.get(
                "success_condition",
                {
                    "operator": "==",
                    "value": "true_breakout",
                },
            )
        ),
    }


def _build_non_failed_rate(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "non_failed_rate",
        "filters": list(params.get("filters", [])),
        "group_by": list(params.get("group_by", [])),
        "target_field": params.get("target_field", "is_failed"),
        "success_condition": dict(
            params.get(
                "success_condition",
                {
                    "operator": "==",
                    "value": False,
                },
            )
        ),
    }
def _build_count(params: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "metric": "count",
        "filters": list(params.get("filters", [])),
        "group_by": list(params.get("group_by", [])),
    }

    if "value_field" in params:
        payload["value_field"] = params["value_field"]

    return payload

def _build_aggregate(metric: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": metric,
        "filters": list(params.get("filters", [])),
        "group_by": list(params.get("group_by", [])),
        "value_field": params["value_field"],
    }


def _build_distribution(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "distribution",
        "filters": list(params.get("filters", [])),
        "group_by": list(params.get("group_by", [])),
        "value_field": params["value_field"],
        "normalization": params.get("normalization", "none"),
    }


def _build_probability(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "metric": "probability",
        "filters": list(params.get("filters", [])),
        "group_by": [],
        "event_predicate": dict(params["event_predicate"]),
        "condition_predicate": dict(params["condition_predicate"]),
    }


def _build_ranking(params: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "metric": "ranking",
        "filters": list(params.get("filters", [])),
        "group_by": list(params["group_by"]),
        "score_metric": params["score_metric"],
        "sort_direction": params["sort_direction"],
    }

    if "value_field" in params:
        payload["value_field"] = params["value_field"]

    if "target_field" in params:
        payload["target_field"] = params["target_field"]

    if "success_condition" in params:
        payload["success_condition"] = dict(params["success_condition"])

    return payload


_PUBLIC_INTENT_REGISTRY: dict[str, PublicIntentSpec] = {
    "success_by_weekday_report": PublicIntentSpec(
        intent_id="success_by_weekday_report",
        params_schema={},
        raw_intent_builder=_build_success_by_weekday_report,
    ),
    "success_rate": PublicIntentSpec(
        intent_id="success_rate",
        params_schema={
            "group_by": {"type": "string_list", "required": True},
            "filters": {"type": "predicate_list", "required": False},
            "target_field": {"type": "string", "required": False},
            "success_condition": {"type": "condition", "required": False},
        },
        raw_intent_builder=_build_success_rate,
        deprecated=True,
        replacement_intent_id="true_breakout_rate",
        semantic_note=(
            "Deprecated compatibility alias. Historically mapped to "
            "is_failed == False. Use true_breakout_rate for canonical "
            "breakout success semantics or non_failed_rate for legacy "
            "non-failed semantics."
        ),
    ),
    "true_breakout_rate": PublicIntentSpec(
        intent_id="true_breakout_rate",
        params_schema={
            "group_by": {"type": "string_list", "required": True},
            "filters": {"type": "predicate_list", "required": False},
            "target_field": {"type": "string", "required": False},
            "success_condition": {"type": "condition", "required": False},
        },
        raw_intent_builder=_build_true_breakout_rate,
    ),

    "non_failed_rate": PublicIntentSpec(
        intent_id="non_failed_rate",
        params_schema={
            "group_by": {"type": "string_list", "required": True},
            "filters": {"type": "predicate_list", "required": False},
            "target_field": {"type": "string", "required": False},
            "success_condition": {"type": "condition", "required": False},
        },
        raw_intent_builder=_build_non_failed_rate,
    ),

    "count": PublicIntentSpec(
        intent_id="count",
        params_schema={
            "value_field": {"type": "string", "required": False},
            "group_by": {"type": "string_list", "required": False},
            "filters": {"type": "predicate_list", "required": False},
        },
        raw_intent_builder=_build_count,
    ),
    "mean": PublicIntentSpec(
        intent_id="mean",
        params_schema={
            "value_field": {"type": "string", "required": True},
            "group_by": {"type": "string_list", "required": True},
            "filters": {"type": "predicate_list", "required": False},
        },
        raw_intent_builder=lambda params: _build_aggregate("mean", params),
    ),
    "median": PublicIntentSpec(
        intent_id="median",
        params_schema={
            "value_field": {"type": "string", "required": True},
            "group_by": {"type": "string_list", "required": True},
            "filters": {"type": "predicate_list", "required": False},
        },
        raw_intent_builder=lambda params: _build_aggregate("median", params),
    ),
    "std": PublicIntentSpec(
        intent_id="std",
        params_schema={
            "value_field": {"type": "string", "required": True},
            "group_by": {"type": "string_list", "required": True},
            "filters": {"type": "predicate_list", "required": False},
        },
        raw_intent_builder=lambda params: _build_aggregate("std", params),
    ),
    "distribution": PublicIntentSpec(
        intent_id="distribution",
        params_schema={
            "value_field": {"type": "string", "required": True},
            "group_by": {"type": "string_list", "required": False},
            "filters": {"type": "predicate_list", "required": False},
            "normalization": {
                "type": "enum",
                "required": False,
                "values": ["none", "share_of_valid_rows"],
            },
        },
        raw_intent_builder=_build_distribution,
    ),
    "probability": PublicIntentSpec(
        intent_id="probability",
        params_schema={
            "filters": {"type": "predicate_list", "required": False},
            "event_predicate": {"type": "predicate", "required": True},
            "condition_predicate": {"type": "predicate", "required": True},
        },
        raw_intent_builder=_build_probability,
    ),
        "ranking": PublicIntentSpec(
            intent_id="ranking",
            params_schema={
                "group_by": {"type": "string_list", "required": True},
                "filters": {"type": "predicate_list", "required": False},
                "score_metric": {
                    "type": "enum",
                    "required": True,
                    "values": [
                        "count",
                        "mean",
                        "median",
                        "std",
                        "success_rate",
                        "true_breakout_rate",
                        "non_failed_rate",
                    ],
                },
                "sort_direction": {
                    "type": "enum",
                    "required": True,
                    "values": ["asc", "desc"],
                },
                "value_field": {"type": "string", "required": False},
                "target_field": {"type": "string", "required": False},
                "success_condition": {"type": "condition", "required": False},
            },
            raw_intent_builder=_build_ranking,
        ),
}