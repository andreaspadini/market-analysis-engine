from __future__ import annotations

from typing import Final


SUPPORTED_METRICS: Final[set[str]] = {
    "count",
    "success_rate",
    "true_breakout_rate",
    "non_failed_rate",
    "mean",
    "median",
    "std",
    "distribution",
    "probability",
    "ranking",
}

SUPPORTED_RANKING_SCORE_METRICS: Final[set[str]] = {
    "count",
    "mean",
    "median",
    "std",
    "success_rate",
    "true_breakout_rate",
    "non_failed_rate",
}

SUPPORTED_SORT_DIRECTIONS: Final[set[str]] = {"asc", "desc"}

SUPPORTED_DISTRIBUTION_NORMALIZATIONS: Final[set[str]] = {
    "none",
    "share_of_valid_rows",
}

METRIC_ALIASES: Final[dict[str, str]] = {
    "count": "count",
    "success rate": "success_rate",
    "success_rate": "success_rate",
    "true breakout rate": "true_breakout_rate",
    "true_breakout_rate": "true_breakout_rate",
    "non failed rate": "non_failed_rate",
    "non_failed_rate": "non_failed_rate",
    "mean": "mean",
    "median": "median",
    "std": "std",
    "distribution": "distribution",
    "probability": "probability",
    "ranking": "ranking",
}

DIMENSION_ALIASES: Final[dict[str, str]] = {
    "session": "session_calc",
    "session_calc": "session_calc",
    "atr_bucket": "atr_bucket",
    "weekday": "weekday",
    "hour": "hour",
    "day_of_month": "day_of_month",
    "week_of_month": "week_of_month",
    "year": "year",
    "time_bucket": "time_bucket",
    "side": "side",
    "instrument": "instrument",
    "symbol": "symbol",
    "breakout_outcome": "breakout_outcome",
    "breakout_type": "breakout_type",
}

FIELD_ALIASES: Final[dict[str, str]] = {
    "session": "session_calc",
    "session_calc": "session_calc",
    "atr_bucket": "atr_bucket",
    "breakout_type": "breakout_type",
    "max_excursion": "max_excursion",
    "is_failed": "is_failed",
    "weekday": "weekday",
    "hour": "hour",
    "day_of_month": "day_of_month",
    "week_of_month": "week_of_month",
    "year": "year",
    "time_bucket": "time_bucket",
    "side": "side",
    "instrument": "instrument",
    "symbol": "symbol",
    "breakout_outcome": "breakout_outcome",
    "atr_before": "atr_before",
    "atr_after": "atr_after",
}

OPERATOR_ALIASES: Final[dict[str, str]] = {
    "=": "==",
    "==": "==",
    "!=": "!=",
    ">": ">",
    ">=": ">=",
    "<": "<",
    "<=": "<=",
    "in": "in",
}

DEFAULT_TRUE_BREAKOUT_TEMPLATE: Final[dict[str, object]] = {
    "target_field": "breakout_outcome",
    "success_condition": {
        "operator": "==",
        "value": "true_breakout",
    },
}

DEFAULT_NON_FAILED_TEMPLATE: Final[dict[str, object]] = {
    "target_field": "is_failed",
    "success_condition": {
        "operator": "==",
        "value": False,
    },
}

# Deprecated transitional alias.
# Kept only for backward compatibility with QRY-2 public callers.
DEFAULT_SUCCESS_TEMPLATE: Final[dict[str, object]] = DEFAULT_NON_FAILED_TEMPLATE
