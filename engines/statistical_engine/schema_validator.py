from __future__ import annotations

from typing import Iterable


REQUIRED_SCHEMA_VERSION = "1.1.0"

ROOT_REQUIRED_COLUMNS = [
    "breakout_id",
    "parent_balance_id",
    "instrument",
    "symbol",
    "session_id",
    "timeframe",
    "breakout_time",
    "breakout_bar_index",
    "confirmation_time",
    "confirmation_bar_index",
    "computation_timestamp",
    "version",
    "direction",
    "breakout_type",
    "confirmation_status",
    "breakout_price",
    "confirmation_price",
    "boundary_price",
    "boundary_type",
    "balance_high",
    "balance_low",
    "balance_midpoint",
    "balance_range_size",
    "balance_vpoc",
    "balance_hvn",
    "balance_lvn",
    "balance_equilibrium_score",
    "balance_rotation_quality_score",
    "balance_structural_integrity_score",
    "initial_volume",
    "initial_volume_zscore",
    "initial_delta",
    "delta_peak",
    "delta_mean_post_breakout",
    "atr_before",
    "atr_after",
    "strength_components",
    "follow_through",
    "post_breakout_volume_profile",
    "bar_count_initial_move",
    "bars_observed",
    "is_failed",
    "is_retest_occurred",
    "config_snapshot",
    "tags",
    "notes",
    "early_time",
    "early_price",
    "early_bar_index",
    "early_timeframe",
    "minutes_of_anticipation",
    "rotation_context",
    "pre_breakout_signal",
    "global_rank",
    "session_rank",
    "ml_nearest_support",
    "ml_nearest_resistance",
    "ml_distance_to_level",
    "ml_cluster_strength",
    "ml_density",
    "ml_alignment_score",
    "schema_version",
]


def validate_root_dataset_columns(columns: Iterable[str]) -> None:
    cols = list(columns)
    missing = [col for col in ROOT_REQUIRED_COLUMNS if col not in cols]

    if missing:
        raise ValueError(
            f"Missing required root dataset columns: {missing}"
        )


def validate_root_dataset_schema_version(values: Iterable[object]) -> None:
    normalized = {str(v) for v in values if v is not None}

    if normalized != {REQUIRED_SCHEMA_VERSION}:
        raise ValueError(
            f"Invalid schema_version values: expected only '{REQUIRED_SCHEMA_VERSION}', got {sorted(normalized)}"
        )