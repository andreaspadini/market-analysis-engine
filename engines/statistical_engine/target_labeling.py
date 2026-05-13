from __future__ import annotations

import pandas as pd


def _get_runtime_config(config: dict | None) -> dict:
    if not isinstance(config, dict):
        return {}
    return config


def append_primary_target(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """
    Adds the primary ATR-based target column defined by:
        config["targets"]["primary"] = {
            "name": <str>,
            "atr_multiplier": <float>,
        }

    Rule:
        success = max_excursion >= atr_multiplier * atr_before
    """

    out = df.copy()

    runtime_cfg = _get_runtime_config(config)
    targets_cfg = runtime_cfg.get("targets", {})
    if not isinstance(targets_cfg, dict):
        return out

    primary_cfg = targets_cfg.get("primary", {})
    if not isinstance(primary_cfg, dict):
        return out

    target_name = primary_cfg.get("name")
    atr_multiplier = primary_cfg.get("atr_multiplier")

    if not isinstance(target_name, str) or not target_name.strip():
        return out

    if atr_multiplier is None:
        return out

    max_excursion = pd.to_numeric(out["max_excursion"], errors="coerce")
    atr_before = pd.to_numeric(out["atr_before"], errors="coerce")

    threshold = atr_before * float(atr_multiplier)
    success = max_excursion >= threshold
    success = success.where(atr_before > 0)

    out[target_name] = success

    return out

def append_secondary_target(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """
    Adds the secondary tick-based target column defined by:
        config["targets"]["secondary"] = {
            "name": <str>,
            "ticks": <int>,
        }

    Tick size source:
        config["tick_scan"]["tick_size"]

    Rule:
        success = max_excursion >= ticks * tick_size
    """

    out = df.copy()

    runtime_cfg = _get_runtime_config(config)

    targets_cfg = runtime_cfg.get("targets", {})
    if not isinstance(targets_cfg, dict):
        return out

    secondary_cfg = targets_cfg.get("secondary", {})
    if not isinstance(secondary_cfg, dict):
        return out

    tick_scan_cfg = runtime_cfg.get("tick_scan", {})
    if not isinstance(tick_scan_cfg, dict):
        return out

    target_name = secondary_cfg.get("name")
    ticks = secondary_cfg.get("ticks")
    tick_size = tick_scan_cfg.get("tick_size")

    if not isinstance(target_name, str) or not target_name.strip():
        return out

    if ticks is None or tick_size is None:
        return out

    max_excursion = pd.to_numeric(out["max_excursion"], errors="coerce")

    threshold = float(ticks) * float(tick_size)
    success = max_excursion >= threshold

    out[target_name] = success

    return out

def append_target_scan_atr(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """
    Materializes multiple ATR-based target columns from:
        config["target_scans"]["success_ATR_scan"]
    """

    out = df.copy()

    runtime_cfg = _get_runtime_config(config)

    scans_cfg = runtime_cfg.get("target_scans", {})
    if not isinstance(scans_cfg, dict):
        return out

    scan_cfg = scans_cfg.get("success_ATR_scan", {})
    if not isinstance(scan_cfg, dict):
        return out

    base_target = scan_cfg.get("base_target")
    x_scan = scan_cfg.get("x_scan", {})

    if not isinstance(base_target, str) or not base_target.strip():
        return out

    if not isinstance(x_scan, dict):
        return out

    start = x_scan.get("start")
    end = x_scan.get("end")
    step = x_scan.get("step")

    if start is None or end is None or step is None:
        return out

    max_excursion = pd.to_numeric(out["max_excursion"], errors="coerce")
    atr_before = pd.to_numeric(out["atr_before"], errors="coerce")

    x = float(start)
    while x <= float(end) + 1e-9:
        threshold = atr_before * x
        col_name = f"{base_target}_{str(x).replace('.', '_')}ATR"
        out[col_name] = max_excursion >= threshold
        x += float(step)

    return out


def append_target_scan_ticks(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """
    Materializes multiple tick-based target columns from:
        config["tick_scan"]["success_ticks"]["levels"]
    using:
        config["tick_scan"]["tick_size"]
    """

    out = df.copy()

    runtime_cfg = _get_runtime_config(config)

    tick_scan_cfg = runtime_cfg.get("tick_scan", {})
    if not isinstance(tick_scan_cfg, dict):
        return out

    tick_size = tick_scan_cfg.get("tick_size")
    success_ticks = tick_scan_cfg.get("success_ticks", {})
    if not isinstance(success_ticks, dict):
        return out

    levels = success_ticks.get("levels")
    if tick_size is None or not isinstance(levels, list):
        return out

    max_excursion = pd.to_numeric(out["max_excursion"], errors="coerce")

    for level in levels:
        threshold = float(level) * float(tick_size)
        col_name = f"t2_{int(level)}ticks"
        out[col_name] = max_excursion >= threshold

    return out


def append_clean_quant(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """
    Adds a quantitative clean-move flag using:
        config["clean_quant"] = {
            "base_target": <str>,
            "atr_multiplier": <float>,
            "clean_atr_threshold": <float>,
        }

    Output columns:
        - is_clean_quant
        - clean_quant_label

    Rule:
        is_clean_quant =
            (base_target == True)
            AND
            (max_excursion >= clean_atr_threshold * atr_before)
    """

    out = df.copy()

    runtime_cfg = _get_runtime_config(config)
    clean_cfg = runtime_cfg.get("clean_quant", {})
    if not isinstance(clean_cfg, dict):
        return out

    base_target = clean_cfg.get("base_target")
    clean_atr_threshold = clean_cfg.get("clean_atr_threshold")

    if not isinstance(base_target, str) or not base_target.strip():
        return out

    if clean_atr_threshold is None:
        return out

    if base_target not in out.columns:
        return out

    retracement_depth = pd.to_numeric(out["retracement_depth"], errors="coerce")
    max_excursion = pd.to_numeric(out["max_excursion"], errors="coerce")

    clean_ratio = retracement_depth / max_excursion
    clean_ratio = clean_ratio.where(max_excursion > 0)

    clean_move = clean_ratio <= float(clean_atr_threshold)

    base_series = out[base_target].astype("boolean")
    is_clean_quant = base_series & clean_move.astype("boolean")

    out["is_clean_quant"] = is_clean_quant
    out["clean_quant_label"] = is_clean_quant.map(
        {
            True: "clean",
            False: "not_clean",
        }
    )

    return out

def append_clean_tick_targets(df: pd.DataFrame, config: dict | None = None) -> pd.DataFrame:
    """
    Materializes clean tick-based targets using:
        - tick_scan.clean_ticks.levels
        - tick_scan.tick_size
        - clean_quant logic (retracement-based)

    Rule:
        success = max_excursion >= ticks * tick_size
        clean = retracement_depth <= threshold
    """

    out = df.copy()

    runtime_cfg = _get_runtime_config(config)

    tick_scan_cfg = runtime_cfg.get("tick_scan", {})
    clean_quant_cfg = runtime_cfg.get("clean_quant", {})

    if not isinstance(tick_scan_cfg, dict) or not isinstance(clean_quant_cfg, dict):
        return out

    tick_size = tick_scan_cfg.get("tick_size")
    clean_ticks_cfg = tick_scan_cfg.get("clean_ticks", {})

    if not isinstance(clean_ticks_cfg, dict):
        return out

    levels = clean_ticks_cfg.get("levels")
    if tick_size is None or not isinstance(levels, list):
        return out

    # dati base
    max_excursion = pd.to_numeric(out["max_excursion"], errors="coerce")
    retracement = pd.to_numeric(out["retracement_depth"], errors="coerce")
    atr_before = pd.to_numeric(out["atr_before"], errors="coerce")

    # clean threshold
    atr_multiplier = clean_quant_cfg.get("atr_multiplier")
    clean_threshold = clean_quant_cfg.get("clean_atr_threshold")

    if atr_multiplier is None or clean_threshold is None:
        return out

    # soglia clean (stessa logica clean_quant)
    clean_limit = atr_before * float(clean_threshold)

    for level in levels:
        threshold = float(level) * float(tick_size)

        success = max_excursion >= threshold
        clean = retracement <= clean_limit

        col_name = f"t2_clean_{int(level)}ticks"
        out[col_name] = success & clean

    return out

