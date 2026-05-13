from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from .dataset_loader import validate_columns_exist, validate_numeric_column


class AggregationContractError(Exception):
    """Raised when a query spec violates the aggregation contract."""
    pass


_ALLOWED_METRICS = {
    "count",
    "mean",
    "median",
    "std",
    "success_rate",
    "true_breakout_rate",
    "non_failed_rate",
    "probability",
    "distribution",
    "ranking",
}

_ALLOWED_PREDICATE_OPERATORS = {"==", "!=", ">", ">=", "<", "<=", "in"}
_ALLOWED_SORT_DIRECTIONS = {"asc", "desc"}
_ALLOWED_DISTRIBUTION_NORMALIZATION = {"none", "share_of_valid_rows"}
_ALLOWED_RANKING_SCORE_METRICS = {
    "count",
    "mean",
    "median",
    "std",
    "success_rate",
    "true_breakout_rate",
    "non_failed_rate",
}


@dataclass(frozen=True)
class MetricSpec:
    name: str
    requires_value_field: bool = False
    requires_numeric_value_field: bool = False
    requires_target_field: bool = False
    requires_success_condition: bool = False
    requires_event_predicate: bool = False
    requires_condition_predicate: bool = False
    requires_group_by: bool = False
    requires_single_group_by: bool = False
    allows_distribution_normalization: bool = False
    requires_score_metric: bool = False
    requires_sort_direction: bool = False


METRIC_REGISTRY: Mapping[str, MetricSpec] = {
    "count": MetricSpec(
        name="count",
        requires_value_field=False,
    ),
    "mean": MetricSpec(
        name="mean",
        requires_value_field=True,
        requires_numeric_value_field=True,
    ),
    "median": MetricSpec(
        name="median",
        requires_value_field=True,
        requires_numeric_value_field=True,
    ),
    "std": MetricSpec(
        name="std",
        requires_value_field=True,
        requires_numeric_value_field=True,
    ),
    "success_rate": MetricSpec(
        name="success_rate",
        requires_target_field=True,
        requires_success_condition=True,
    ),
    "true_breakout_rate": MetricSpec(
        name="true_breakout_rate",
        requires_target_field=True,
        requires_success_condition=True,
    ),
    "non_failed_rate": MetricSpec(
        name="non_failed_rate",
        requires_target_field=True,
        requires_success_condition=True,
    ),
    "probability": MetricSpec(
        name="probability",
        requires_event_predicate=True,
        requires_condition_predicate=True,
    ),
    "distribution": MetricSpec(
        name="distribution",
        requires_value_field=True,
        allows_distribution_normalization=True,
    ),
    "ranking": MetricSpec(
        name="ranking",
        requires_group_by=True,
        requires_single_group_by=True,
        requires_score_metric=True,
        requires_sort_direction=True,
    ),
}


def get_metric_spec(metric_name: str) -> MetricSpec:
    try:
        return METRIC_REGISTRY[metric_name]
    except KeyError as exc:
        raise AggregationContractError(
            f"Unsupported metric '{metric_name}'. Allowed metrics: {sorted(_ALLOWED_METRICS)}"
        ) from exc


def validate_query_against_contract(query: Mapping[str, Any], df: Any) -> None:
    if not isinstance(query, Mapping):
        raise AggregationContractError("Query must be a mapping/object.")

    metric = query.get("metric")
    if metric not in _ALLOWED_METRICS:
        raise AggregationContractError(
            f"Unsupported metric '{metric}'. Allowed metrics: {sorted(_ALLOWED_METRICS)}"
        )

    spec = get_metric_spec(metric)

    filters = query.get("filters", [])
    _validate_filters(filters, df)

    group_by = query.get("group_by", [])
    _validate_group_by(group_by, df)

    if spec.requires_group_by and not group_by:
        raise AggregationContractError(f"Metric '{metric}' requires non-empty group_by.")

    if spec.requires_single_group_by and len(group_by) != 1:
        raise AggregationContractError(
            f"Metric '{metric}' requires exactly one group_by field."
        )

    value_field = query.get("value_field")
    if spec.requires_value_field and not value_field:
        raise AggregationContractError(f"Metric '{metric}' requires value_field.")

    if value_field is not None:
        validate_columns_exist(df, [value_field])

    if spec.requires_numeric_value_field and value_field is not None:
        validate_numeric_column(df, value_field)

    target_field = query.get("target_field")
    if spec.requires_target_field and not target_field:
        raise AggregationContractError(f"Metric '{metric}' requires target_field.")

    if target_field is not None:
        validate_columns_exist(df, [target_field])

    if spec.requires_success_condition:
        success_condition = query.get("success_condition")
        if not isinstance(success_condition, Mapping):
            raise AggregationContractError(
                f"Metric '{metric}' requires success_condition object."
            )
        _validate_simple_predicate_shape(success_condition, require_field=False)

    if spec.requires_event_predicate:
        event_predicate = query.get("event_predicate")
        if not isinstance(event_predicate, Mapping):
            raise AggregationContractError(
                f"Metric '{metric}' requires event_predicate object."
            )
        _validate_simple_predicate_shape(event_predicate, require_field=True)
        _validate_predicate_against_df(event_predicate, df)

    if spec.requires_condition_predicate:
        condition_predicate = query.get("condition_predicate")
        if not isinstance(condition_predicate, Mapping):
            raise AggregationContractError(
                f"Metric '{metric}' requires condition_predicate object."
            )
        _validate_simple_predicate_shape(condition_predicate, require_field=True)
        _validate_predicate_against_df(condition_predicate, df)

    if metric == "distribution":
        normalization = query.get("normalization", "none")
        if normalization not in _ALLOWED_DISTRIBUTION_NORMALIZATION:
            raise AggregationContractError(
                "distribution.normalization must be one of "
                f"{sorted(_ALLOWED_DISTRIBUTION_NORMALIZATION)}."
            )

    if metric == "ranking":
        score_metric = query.get("score_metric")
        sort_direction = query.get("sort_direction")

        if score_metric not in _ALLOWED_RANKING_SCORE_METRICS:
            raise AggregationContractError(
                "ranking.score_metric must be one of "
                f"{sorted(_ALLOWED_RANKING_SCORE_METRICS)}."
            )

        if sort_direction not in _ALLOWED_SORT_DIRECTIONS:
            raise AggregationContractError(
                "ranking.sort_direction must be one of "
                f"{sorted(_ALLOWED_SORT_DIRECTIONS)}."
            )

        ranking_query = dict(query)
        ranking_query["metric"] = score_metric
        ranking_query.pop("score_metric", None)
        ranking_query.pop("sort_direction", None)
        validate_query_against_contract(ranking_query, df)


def _validate_group_by(group_by: Any, df: Any) -> None:
    if group_by is None:
        return

    if not isinstance(group_by, list):
        raise AggregationContractError("group_by must be a list.")

    if not all(isinstance(field, str) and field for field in group_by):
        raise AggregationContractError("group_by must contain only non-empty strings.")

    if group_by:
        validate_columns_exist(df, group_by)


def _validate_filters(filters: Any, df: Any) -> None:
    if filters is None:
        return

    if not isinstance(filters, list):
        raise AggregationContractError("filters must be a list.")

    for predicate in filters:
        if not isinstance(predicate, Mapping):
            raise AggregationContractError("Each filter must be an object.")
        _validate_simple_predicate_shape(predicate, require_field=True)
        _validate_predicate_against_df(predicate, df)


def _validate_simple_predicate_shape(
    predicate: Mapping[str, Any],
    *,
    require_field: bool,
) -> None:
    if require_field:
        field = predicate.get("field")
        if not isinstance(field, str) or not field:
            raise AggregationContractError("Predicate field must be a non-empty string.")

    operator = predicate.get("operator")
    if operator not in _ALLOWED_PREDICATE_OPERATORS:
        raise AggregationContractError(
            f"Predicate operator '{operator}' is not allowed. "
            f"Allowed operators: {sorted(_ALLOWED_PREDICATE_OPERATORS)}"
        )

    if "value" not in predicate:
        raise AggregationContractError("Predicate must include value.")

    value = predicate["value"]
    if operator == "in":
        if not isinstance(value, list) or len(value) == 0:
            raise AggregationContractError(
                "Predicate operator 'in' requires a non-empty list value."
            )
    else:
        if isinstance(value, list):
            raise AggregationContractError(
                f"Predicate operator '{operator}' requires scalar value, not list."
            )


def _validate_predicate_against_df(predicate: Mapping[str, Any], df: Any) -> None:
    field = predicate["field"]
    operator = predicate["operator"]

    validate_columns_exist(df, [field])

    if operator in {">", ">=", "<", "<="}:
        validate_numeric_column(df, field)