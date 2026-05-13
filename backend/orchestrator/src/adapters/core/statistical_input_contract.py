from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STATISTICAL_INPUT_SCHEMA_VERSION = "1.1.0"


class StatisticalInputContractError(ValueError):
    """Errore strict sul contract StatisticalInputDataset."""


REQUIRED_COLUMNS_ORDERED: list[str] = [
    "schema_version",
    "breakout_id",
    "direction",
    "breakout_price",
    "balance_range_size",
    "initial_delta",
    "initial_volume",
    "atr_before",
    "follow_through",
    "is_failed",
    "max_excursion",
    "retracement_depth",
    "time_to_retest_boundary",
]


REQUIRED_NON_NULL_COLUMNS: list[str] = [
    "schema_version",
    "breakout_id",
    "direction",
    "breakout_price",
    "balance_range_size",
    "initial_delta",
    "initial_volume",
    "atr_before",
    "follow_through",
    "is_failed",
]


STRING_COLUMNS: list[str] = [
    "schema_version",
    "breakout_id",
    "direction",
]

NUMERIC_COLUMNS: list[str] = [
    "breakout_price",
    "balance_range_size",
    "initial_delta",
    "initial_volume",
    "atr_before",
    "max_excursion",
    "retracement_depth",
    "time_to_retest_boundary",
]

BOOLEAN_COLUMNS: list[str] = [
    "is_failed",
]


OPTIONAL_PASSTHROUGH_COLUMNS: list[str] = [
    "breakout_type",
    "delta_peak",
    "delta_mean_post_breakout",
    "pre_breakout_signal",
    "breakout_time",
    "instrument",
    "session_id",
    "timeframe",
    "version",
    "ml_distance_to_level",
    "ml_nearest_support",
    "ml_nearest_resistance",
    "ml_cluster_strength",
    "ml_density",
    "ml_alignment_score",
]


def ordered_output_columns(actual_columns: list[str]) -> list[str]:
    extras = sorted(
        [
            c
            for c in actual_columns
            if c not in REQUIRED_COLUMNS_ORDERED
        ]
    )
    ordered = list(REQUIRED_COLUMNS_ORDERED)
    ordered.extend(extras)
    return ordered


def validate_schema_version_values(values: list[Any]) -> None:
    unique_values = {v for v in values if v is not None}
    if unique_values != {STATISTICAL_INPUT_SCHEMA_VERSION}:
        raise StatisticalInputContractError(
            "Invalid schema_version values. "
            f"Expected only {STATISTICAL_INPUT_SCHEMA_VERSION!r}, got {sorted(unique_values)!r}"
        )