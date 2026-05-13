from __future__ import annotations

from typing import Any

import math
import pandas as pd


def _require_number(value: Any, name: str) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ValueError(f"{name} must be numeric") from exc

    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite")

    return out


def derive_candle_features(
    row: pd.Series,
    *,
    tick_size: float,
) -> dict[str, Any]:
    """
    Derive manual-template candle features from one OHLCV row.

    Output fields:
    - direction
    - body_ticks
    - upper_wick_ticks
    - lower_wick_ticks
    - volume
    - delta
    - close_position
    """

    tick = _require_number(tick_size, "tick_size")
    if tick <= 0:
        raise ValueError("tick_size must be > 0")

    open_ = _require_number(row.get("open"), "open")
    high = _require_number(row.get("high"), "high")
    low = _require_number(row.get("low"), "low")
    close = _require_number(row.get("close"), "close")

    if high < max(open_, close):
        raise ValueError("Invalid OHLC: high < max(open, close)")

    if low > min(open_, close):
        raise ValueError("Invalid OHLC: low > min(open, close)")

    if close > open_:
        direction = "bullish"
    elif close < open_:
        direction = "bearish"
    else:
        direction = "neutral"

    body = abs(close - open_)
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low

    body_ticks = max(0.0, body / tick)
    upper_wick_ticks = max(0.0, upper_wick / tick)
    lower_wick_ticks = max(0.0, lower_wick / tick)

    if "volume" not in row:
        raise ValueError("volume is required")

    volume = _require_number(row.get("volume"), "volume")
    if volume < 0:
        raise ValueError("volume must be >= 0")

    delta = None
    if "delta" in row and row.get("delta") is not None:
        delta = _require_number(row.get("delta"), "delta")

    candle_range = high - low

    if candle_range <= 0:
        close_position = "mid"
    else:
        near_high_threshold = high - (0.25 * candle_range)
        near_low_threshold = low + (0.25 * candle_range)

        if close >= near_high_threshold:
            close_position = "near_high"
        elif close <= near_low_threshold:
            close_position = "near_low"
        else:
            close_position = "mid"

    return {
        "direction": direction,
        "body_ticks": body_ticks,
        "upper_wick_ticks": upper_wick_ticks,
        "lower_wick_ticks": lower_wick_ticks,
        "volume": volume,
        "delta": delta,
        "close_position": close_position,
    }

def score_numeric_field(
    *,
    candidate_value: float | None,
    template_value: float | None,
    tolerance_pct: float,
) -> float:
    if template_value is None:
        return 1.0

    if candidate_value is None:
        return 0.0

    candidate = _require_number(candidate_value, "candidate_value")
    template = _require_number(template_value, "template_value")
    tolerance = _require_number(tolerance_pct, "tolerance_pct")

    if tolerance <= 0:
        raise ValueError("tolerance_pct must be > 0")

    # Negative values are valid for delta.
    # body/wick/volume validation belongs to the contract/model layer.

    if template == 0:
        return 1.0 if candidate == 0 else 0.0

    allowed = abs(template) * tolerance / 100.0
    if allowed <= 0:
        return 1.0 if candidate == template else 0.0

    distance = abs(candidate - template) / allowed
    return max(0.0, min(1.0, 1.0 - distance))


def score_direction(
    *,
    candidate_direction: str,
    template_direction: str,
) -> float:
    template = str(template_direction).strip().lower()
    candidate = str(candidate_direction).strip().lower()

    if template == "any":
        return 1.0

    return 1.0 if candidate == template else 0.0


def score_close_position(
    *,
    candidate_close_position: str | None,
    template_close_position: str | None,
) -> float:
    if template_close_position is None:
        return 1.0

    template = str(template_close_position).strip().lower()
    if template == "any":
        return 1.0

    candidate = str(candidate_close_position).strip().lower()
    return 1.0 if candidate == template else 0.0


def weighted_average(parts: list[tuple[float, float]]) -> float:
    total_weight = 0.0
    total_score = 0.0

    for score, weight in parts:
        s = _require_number(score, "score")
        w = _require_number(weight, "weight")

        if w <= 0:
            continue

        total_weight += w
        total_score += s * w

    if total_weight <= 0:
        return 0.0

    return max(0.0, min(1.0, total_score / total_weight))

def _model_or_dict_get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def score_single_candle(
    *,
    candidate_features: dict[str, Any],
    template_candle: Any,
    tolerance: Any,
) -> float:
    body_tol = _model_or_dict_get(tolerance, "body_ticks_pct")
    wick_tol = _model_or_dict_get(tolerance, "wick_ticks_pct")
    volume_tol = _model_or_dict_get(tolerance, "volume_pct")
    delta_tol = _model_or_dict_get(tolerance, "delta_pct")

    direction_score = score_direction(
        candidate_direction=str(candidate_features.get("direction")),
        template_direction=str(_model_or_dict_get(template_candle, "direction")),
    )

    body_score = score_numeric_field(
        candidate_value=candidate_features.get("body_ticks"),
        template_value=_model_or_dict_get(template_candle, "body_ticks"),
        tolerance_pct=body_tol,
    )

    upper_wick_score = score_numeric_field(
        candidate_value=candidate_features.get("upper_wick_ticks"),
        template_value=_model_or_dict_get(template_candle, "upper_wick_ticks"),
        tolerance_pct=wick_tol,
    )

    lower_wick_score = score_numeric_field(
        candidate_value=candidate_features.get("lower_wick_ticks"),
        template_value=_model_or_dict_get(template_candle, "lower_wick_ticks"),
        tolerance_pct=wick_tol,
    )

    volume_score = score_numeric_field(
        candidate_value=candidate_features.get("volume"),
        template_value=_model_or_dict_get(template_candle, "volume"),
        tolerance_pct=volume_tol,
    )

    delta_score = score_numeric_field(
        candidate_value=candidate_features.get("delta"),
        template_value=_model_or_dict_get(template_candle, "delta"),
        tolerance_pct=delta_tol,
    )

    close_position_score = score_close_position(
        candidate_close_position=candidate_features.get("close_position"),
        template_close_position=_model_or_dict_get(template_candle, "close_position"),
    )

    return weighted_average(
        [
            (direction_score, 1.0),
            (body_score, 1.0),
            (upper_wick_score, 1.0),
            (lower_wick_score, 1.0),
            (volume_score, 0.5),
            (delta_score, 0.5),
            (close_position_score, 0.75),
        ]
    )

def score_pattern_window(
    *,
    window_df: pd.DataFrame,
    template_candles: list[Any],
    tolerance: Any,
    tick_size: float,
) -> float:
    if len(window_df) != len(template_candles):
        raise ValueError(
            f"window length mismatch: window_df={len(window_df)} template={len(template_candles)}"
        )

    if len(template_candles) <= 0:
        raise ValueError("template_candles must contain at least one candle")

    scores: list[float] = []

    sorted_template = sorted(
        template_candles,
        key=lambda c: int(_model_or_dict_get(c, "index")),
    )

    for i, template_candle in enumerate(sorted_template):
        row = window_df.iloc[i]
        features = derive_candle_features(row, tick_size=tick_size)
        score = score_single_candle(
            candidate_features=features,
            template_candle=template_candle,
            tolerance=tolerance,
        )
        scores.append(score)

    return max(0.0, min(1.0, sum(scores) / len(scores)))

def _get_timestamp_from_row(row: pd.Series) -> Any:
    if "timestamp" in row:
        return row.get("timestamp")
    if "ts" in row:
        return row.get("ts")
    return row.name

def _timeframe_to_timedelta(timeframe: str) -> pd.Timedelta:
    tf = str(timeframe).strip().lower()
    if len(tf) < 2:
        raise ValueError(f"Invalid timeframe: {timeframe!r}")

    unit = tf[-1]
    value = int(tf[:-1])

    if value <= 0:
        raise ValueError(f"Invalid timeframe: {timeframe!r}")

    if unit == "s":
        return pd.Timedelta(seconds=value)
    if unit == "m":
        return pd.Timedelta(minutes=value)
    if unit == "h":
        return pd.Timedelta(hours=value)
    if unit == "d":
        return pd.Timedelta(days=value)

    raise ValueError(f"Unsupported timeframe: {timeframe!r}")

def find_manual_template_matches(
    *,
    pattern_id: str,
    instrument: str,
    timeframe: str,
    bars_df: pd.DataFrame,
    template_candles: list[Any],
    tolerance: Any,
    tick_size: float,
    min_similarity: float = 0.0,
    engine_version: str = "1.0",
    run_id: str = "manual_template_run",
) -> list[Any]:
    from engines.pattern_engine.pattern_schema import PatternMatchModel

    if not isinstance(bars_df, pd.DataFrame):
        raise TypeError("bars_df must be a pandas DataFrame")

    if len(template_candles) <= 0:
        raise ValueError("template_candles must contain at least one candle")

    length_bars = len(template_candles)

    if len(bars_df) < length_bars:
        return []

    min_score = _require_number(min_similarity, "min_similarity")
    if min_score < 0 or min_score > 1:
        raise ValueError("min_similarity must be in [0, 1]")

    matches: list[PatternMatchModel] = []

    ordered_df = bars_df.copy()
    if "timestamp" in ordered_df.columns:
        ordered_df["timestamp"] = pd.to_datetime(ordered_df["timestamp"], utc=True)
        ordered_df = ordered_df.sort_values("timestamp").reset_index(drop=True)

    for start_idx in range(0, len(ordered_df) - length_bars + 1):
        end_idx = start_idx + length_bars - 1
        window_df = ordered_df.iloc[start_idx : end_idx + 1]

        similarity_score = score_pattern_window(
            window_df=window_df,
            template_candles=template_candles,
            tolerance=tolerance,
            tick_size=tick_size,
        )

        if similarity_score < min_score:
            continue

        start_ts = pd.Timestamp(_get_timestamp_from_row(window_df.iloc[0]))
        end_ts = pd.Timestamp(_get_timestamp_from_row(window_df.iloc[-1]))

        if start_ts.tzinfo is None:
            start_ts = start_ts.tz_localize("UTC")
        if end_ts.tzinfo is None:
            end_ts = end_ts.tz_localize("UTC")

        if not start_ts < end_ts:
            end_ts = start_ts + _timeframe_to_timedelta(timeframe)

        matches.append(
            PatternMatchModel(
                pattern_id=pattern_id,
                instrument=instrument,
                timeframe=timeframe,
                start_ts=start_ts.to_pydatetime(),
                end_ts=end_ts.to_pydatetime(),
                start_bar_index=start_idx,
                similarity_score=float(similarity_score),
                distance_components=None,
                feature_summary=None,
                engine_version=engine_version,
                run_id=run_id,
            )
        )

    return sorted(
        matches,
        key=lambda m: (-float(m.similarity_score), m.start_ts),
    )
