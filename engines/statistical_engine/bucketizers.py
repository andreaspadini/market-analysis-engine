from __future__ import annotations

import pandas as pd


def _get_runtime_config(config: dict | None) -> dict:
    if not isinstance(config, dict):
        return {}
    return config


def _get_bucket_config(config: dict | None, bucket_name: str, default: dict) -> dict:
    runtime_cfg = _get_runtime_config(config)
    buckets_cfg = runtime_cfg.get("bucketizers", {})
    if not isinstance(buckets_cfg, dict):
        return default

    bucket_cfg = buckets_cfg.get(bucket_name, {})
    if not isinstance(bucket_cfg, dict):
        return default

    merged = default.copy()
    merged.update(bucket_cfg)
    return merged


def append_compression_bucket(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    out = df.copy()

    ratio = pd.to_numeric(out["range_atr_ratio"], errors="coerce")

    cfg = _get_bucket_config(
        config,
        "compression_bucket",
        {
            "ultra_compressed_max": 0.50,
            "compressed_max": 1.00,
            "balanced_max": 1.50,
            "expanded_max": 2.50,
        },
    )

    ultra_compressed_max = cfg["ultra_compressed_max"]
    compressed_max = cfg["compressed_max"]
    balanced_max = cfg["balanced_max"]
    expanded_max = cfg["expanded_max"]

    bucket = pd.Series(index=out.index, dtype="object")

    bucket.loc[(ratio >= 0.00) & (ratio < ultra_compressed_max)] = "ultra_compressed"
    bucket.loc[(ratio >= ultra_compressed_max) & (ratio < compressed_max)] = "compressed"
    bucket.loc[(ratio >= compressed_max) & (ratio < balanced_max)] = "balanced"
    bucket.loc[(ratio >= balanced_max) & (ratio < expanded_max)] = "expanded"
    bucket.loc[ratio >= expanded_max] = "ultra_expanded"

    out["compression_bucket"] = bucket

    return out


def append_delta_bucket(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    out = df.copy()

    delta = pd.to_numeric(out["abs_initial_delta"], errors="coerce")

    cfg = _get_bucket_config(
        config,
        "delta_bucket",
        {
            "delta_0_100_max": 100,
            "delta_100_300_max": 300,
            "delta_300_600_max": 600,
            "delta_600_1000_max": 1000,
        },
    )

    delta_0_100_max = cfg["delta_0_100_max"]
    delta_100_300_max = cfg["delta_100_300_max"]
    delta_300_600_max = cfg["delta_300_600_max"]
    delta_600_1000_max = cfg["delta_600_1000_max"]

    bucket = pd.Series(index=out.index, dtype="object")

    bucket.loc[(delta >= 0) & (delta < delta_0_100_max)] = "delta_0_100"
    bucket.loc[(delta >= delta_0_100_max) & (delta < delta_100_300_max)] = "delta_100_300"
    bucket.loc[(delta >= delta_100_300_max) & (delta < delta_300_600_max)] = "delta_300_600"
    bucket.loc[(delta >= delta_300_600_max) & (delta < delta_600_1000_max)] = "delta_600_1000"
    bucket.loc[delta >= delta_600_1000_max] = "delta_1000_plus"

    out["delta_bucket"] = bucket

    return out


def append_volume_bucket(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    out = df.copy()

    volume = pd.to_numeric(out["initial_volume_feature"], errors="coerce")

    bucket = pd.Series(index=out.index, dtype="object")

    cfg = (((config or {}).get("bucketizers") or {}).get("volume_bucket") or {})
   

    very_low_max = cfg.get("very_low_max", 50)
    low_max = cfg.get("low_max", 150)
    medium_max = cfg.get("medium_max", 400)
    high_max = cfg.get("high_max", 800)

    bucket.loc[volume < very_low_max] = "very_low"
    bucket.loc[(volume >= very_low_max) & (volume < low_max)] = "low"
    bucket.loc[(volume >= low_max) & (volume < medium_max)] = "medium"
    bucket.loc[(volume >= medium_max) & (volume < high_max)] = "high"
    bucket.loc[volume >= high_max] = "extreme"

    out["volume_bucket"] = bucket

    return out


def append_atr_bucket(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    out = df.copy()

    atr = pd.to_numeric(out["atr_before"], errors="coerce")

    cfg = _get_bucket_config(
        config,
        "atr_bucket",
        {
            "atr_0_0_5_max": 0.5,
            "atr_0_5_1_0_max": 1.0,
            "atr_1_0_1_5_max": 1.5,
            "atr_1_5_2_5_max": 2.5,
        },
    )

    atr_0_0_5_max = cfg["atr_0_0_5_max"]
    atr_0_5_1_0_max = cfg["atr_0_5_1_0_max"]
    atr_1_0_1_5_max = cfg["atr_1_0_1_5_max"]
    atr_1_5_2_5_max = cfg["atr_1_5_2_5_max"]

    bucket = pd.Series(index=out.index, dtype="object")

    bucket.loc[(atr > 0.0) & (atr < atr_0_0_5_max)] = "atr_0_0_5"
    bucket.loc[(atr >= atr_0_0_5_max) & (atr < atr_0_5_1_0_max)] = "atr_0_5_1_0"
    bucket.loc[(atr >= atr_0_5_1_0_max) & (atr < atr_1_0_1_5_max)] = "atr_1_0_1_5"
    bucket.loc[(atr >= atr_1_0_1_5_max) & (atr < atr_1_5_2_5_max)] = "atr_1_5_2_5"
    bucket.loc[atr >= atr_1_5_2_5_max] = "atr_2_5_plus"

    out["atr_bucket"] = bucket

    return out


def append_pre_bo_bucket(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    out = df.copy()

    score = pd.to_numeric(out["pre_total_score"], errors="coerce")

    cfg = _get_bucket_config(
        config,
        "pre_bo_bucket",
        {
            "pre_neg_max": 0.0,
            "pre_0_2_max": 2.0,
            "pre_2_4_max": 4.0,
            "pre_4_6_max": 6.0,
        },
    )

    pre_neg_max = cfg["pre_neg_max"]
    pre_0_2_max = cfg["pre_0_2_max"]
    pre_2_4_max = cfg["pre_2_4_max"]
    pre_4_6_max = cfg["pre_4_6_max"]

    bucket = pd.Series(index=out.index, dtype="object")

    bucket.loc[score < pre_neg_max] = "pre_neg"
    bucket.loc[(score >= pre_neg_max) & (score < pre_0_2_max)] = "pre_0_2"
    bucket.loc[(score >= pre_0_2_max) & (score < pre_2_4_max)] = "pre_2_4"
    bucket.loc[(score >= pre_2_4_max) & (score < pre_4_6_max)] = "pre_4_6"
    bucket.loc[score >= pre_4_6_max] = "pre_6_plus"

    out["pre_bo_bucket"] = bucket

    return out


def append_time_bucket_feature(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """
    time_bucket from decimal hour
    """

    out = df.copy()

    hour = pd.to_numeric(out["hour"], errors="coerce")

    cfg = _get_bucket_config(
        config,
        "time_bucket",
        {
            "tb_00_04_max": 4.0,
            "tb_04_08_max": 8.0,
            "tb_08_12_max": 12.0,
            "tb_12_16_max": 16.0,
            "tb_16_20_max": 20.0,
            "tb_20_24_max": 24.0,
        },
    )

    tb_00_04_max = cfg["tb_00_04_max"]
    tb_04_08_max = cfg["tb_04_08_max"]
    tb_08_12_max = cfg["tb_08_12_max"]
    tb_12_16_max = cfg["tb_12_16_max"]
    tb_16_20_max = cfg["tb_16_20_max"]
    tb_20_24_max = cfg["tb_20_24_max"]

    bucket = pd.Series(index=out.index, dtype="object")

    bucket.loc[(hour >= 0.0) & (hour < tb_00_04_max)] = "tb_00_04"
    bucket.loc[(hour >= tb_00_04_max) & (hour < tb_04_08_max)] = "tb_04_08"
    bucket.loc[(hour >= tb_04_08_max) & (hour < tb_08_12_max)] = "tb_08_12"
    bucket.loc[(hour >= tb_08_12_max) & (hour < tb_12_16_max)] = "tb_12_16"
    bucket.loc[(hour >= tb_12_16_max) & (hour < tb_16_20_max)] = "tb_16_20"
    bucket.loc[(hour >= tb_16_20_max) & (hour < tb_20_24_max)] = "tb_20_24"

    out["time_bucket"] = bucket

    return out