from __future__ import annotations

from pathlib import Path

from .dataset_loader import load_root_dataset
from .feature_extractors import (
    append_side_feature,
    append_range_atr_ratio_feature,
    append_balance_pressure_feature,
    append_breakout_location_ratio_feature,
    append_abs_initial_delta_feature,
    append_initial_volume_feature,
    append_volume_atr_ratio_feature,
    append_volume_range_ratio_feature,
    append_max_excursion_feature,
    append_breakout_efficiency_feature,
    append_pre_total_score_feature,
    append_hour_feature,
    append_session_calc_feature,
    append_weekday_feature,
    append_day_of_month_feature,
    append_week_of_month_feature,
    append_year_feature,
    append_ml_distance_atr_feature,
)
from .bucketizers import (
    append_compression_bucket,
    append_delta_bucket,
    append_volume_bucket,
    append_atr_bucket,
    append_pre_bo_bucket,
    append_time_bucket_feature,
)
from .schema_validator import (
    validate_root_dataset_columns,
    validate_root_dataset_schema_version,
)
from .outcome_labeling import (
    append_breakout_outcome,
)
from .target_labeling import (
    append_primary_target,
    append_secondary_target,
    append_clean_quant,
    append_target_scan_atr,
    append_target_scan_ticks,
    append_clean_tick_targets,
)

def run_statistical_pipeline(
    *,
    root_dataset_path: Path,
    output_parquet_path: Path,
    config: dict | None = None,
) -> Path:

    root_dataset_path = Path(root_dataset_path).resolve()
    output_parquet_path = Path(output_parquet_path).resolve()

    config = config or {}

    df = load_root_dataset(root_dataset_path)

    validate_root_dataset_columns(df.columns)
    validate_root_dataset_schema_version(df["schema_version"].dropna().unique())

    df = append_breakout_outcome(df)

    df = append_side_feature(df)
    df = append_range_atr_ratio_feature(df)
    df = append_balance_pressure_feature(df)
    df = append_breakout_location_ratio_feature(df)

    df = append_compression_bucket(df, config=config)

    df = append_abs_initial_delta_feature(df)
    df = append_delta_bucket(df, config=config)

    df = append_initial_volume_feature(df)
    df = append_volume_bucket(df, config=config)
    df = append_volume_atr_ratio_feature(df)
    df = append_volume_range_ratio_feature(df)

    df = append_atr_bucket(df, config=config)

    df = append_max_excursion_feature(df)

    df = append_primary_target(df, config=config)
    df = append_secondary_target(df, config=config)
    df = append_target_scan_atr(df, config=config)
    df = append_target_scan_ticks(df, config=config)
    df = append_clean_tick_targets(df, config=config)
    df = append_clean_quant(df, config=config)

    df = append_breakout_efficiency_feature(df)
    df = append_pre_total_score_feature(df)
    df = append_pre_bo_bucket(df, config=config)
    df = append_ml_distance_atr_feature(df)

    df = append_hour_feature(df)
    df = append_session_calc_feature(df)
    df = append_time_bucket_feature(df, config=config)
    df = append_weekday_feature(df)
    df = append_day_of_month_feature(df)
    df = append_week_of_month_feature(df)
    df = append_year_feature(df)

    output_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet_path, index=False)

    return output_parquet_path
