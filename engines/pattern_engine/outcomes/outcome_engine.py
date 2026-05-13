"""Chapter 8 â€” Outcome / Post-Pattern Statistics.

Compute post-pattern outcome metrics (MFE/MAE) after a pattern is found.

Frozen spec (MVP):
- entry_price = close of the bar at match.end_ts
- future window = next H bars strictly after end_ts
- compute MFE/MAE in points/ticks for BOTH long and short, always
- ignore matches without enough future bars
- deterministic output, ML-ready

Implementation:
- Works with a tz-aware, sorted bars_df (Cap.4 contract).
- Uses PatternMatchModel + PatternStatsModel (Cap.3 schema).

The function is defensive about schema differences across pydantic v1/v2:
- It builds a payload dict and passes it to PatternStatsModel.
- If PatternStatsModel has fewer fields, unknown keys are filtered out.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import math

import numpy as np
import pandas as pd

from engines.pattern_engine.pattern_schema import PatternMatchModel, PatternStatsModel


@dataclass(frozen=True)
class _Summary:
    n_occurrences: int
    mean: float
    median: float
    q25: float
    q75: float
    q90: float
    min: float
    max: float


def _quantile(values: np.ndarray, q: float) -> float:
    # deterministic across numpy versions by using method arg when available
    if values.size == 0:
        return float("nan")
    try:
        return float(np.quantile(values, q, method="linear"))
    except TypeError:
        # numpy<1.22
        return float(np.quantile(values, q, interpolation="linear"))


def _summary(values: Sequence[float]) -> _Summary:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("No values to summarize")

    return _Summary(
        n_occurrences=int(arr.size),
        mean=float(arr.mean()),
        median=float(_quantile(arr, 0.50)),
        q25=float(_quantile(arr, 0.25)),
        q75=float(_quantile(arr, 0.75)),
        q90=float(_quantile(arr, 0.90)),
        min=float(arr.min()),
        max=float(arr.max()),
    )


def _hit_rates_ge(values: Sequence[float], levels: Sequence[float]) -> list[tuple[float, float]]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return [(float(l), float("nan")) for l in levels]
    out: list[tuple[float, float]] = []
    n = float(arr.size)
    for lvl in levels:
        p = float((arr >= float(lvl)).sum() / n)
        out.append((float(lvl), p))
    return out


def _hit_rates_le(values: Sequence[float], levels: Sequence[float]) -> list[tuple[float, float]]:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return [(float(l), float("nan")) for l in levels]
    out: list[tuple[float, float]] = []
    n = float(arr.size)
    for lvl in levels:
        p = float((arr <= float(lvl)).sum() / n)
        out.append((float(lvl), p))
    return out


def _get_model_fields(model_cls: type) -> set[str]:
    # pydantic v1: __fields__ ; pydantic v2: model_fields
    if hasattr(model_cls, "model_fields"):
        return set(getattr(model_cls, "model_fields").keys())
    if hasattr(model_cls, "__fields__"):
        return set(getattr(model_cls, "__fields__").keys())
    return set()


def _instantiate_stats_model(payload: Mapping[str, Any]) -> PatternStatsModel:
    # filter unknown top-level keys to reduce coupling to schema evolution
    allowed = _get_model_fields(PatternStatsModel)
    filtered = dict(payload) if not allowed else {k: v for k, v in payload.items() if k in allowed}

    # pydantic v2 uses model_validate, v1 uses constructor
    if hasattr(PatternStatsModel, "model_validate"):
        return PatternStatsModel.model_validate(filtered)  # type: ignore[attr-defined]
    return PatternStatsModel(**filtered)  # type: ignore[call-arg]


def _compute_atr_series(bars_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Simple ATR as rolling mean of True Range (deterministic).

    This is intentionally simple (not Wilder smoothing) to avoid hidden state.
    """
    high = bars_df["high"].astype(float)
    low = bars_df["low"].astype(float)
    close = bars_df["close"].astype(float)
    prev_close = close.shift(1)

    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return tr.rolling(window=period, min_periods=period).mean()


def compute_outcome_stats(
    *,
    matches: list[PatternMatchModel],
    bars_df: pd.DataFrame,
    horizon_bars: int,
    targets_ticks: list[int],
    compute_atr_multiples: bool = False,
) -> PatternStatsModel:
    """Compute post-pattern outcome statistics.

    Args:
        matches: validated matches (Cap.7 output)
        bars_df: sorted, tz-aware bars DataFrame. Index must be timestamps.
        horizon_bars: H, number of bars to look ahead
        targets_ticks: list of integer threshold levels (same unit as bars prices)
        compute_atr_multiples: if True, compute ATR multiples where ATR is available

    Returns:
        PatternStatsModel

    Raises:
        ValueError: if no match has enough future bars to compute outcomes
    """
    if horizon_bars <= 0:
        raise ValueError("horizon_bars must be > 0")

    if bars_df is None or len(bars_df) == 0:
        raise ValueError("bars_df is empty")

    # Ensure index is monotonic increasing for searchsorted
    if not bars_df.index.is_monotonic_increasing:
        bars_df = bars_df.sort_index()

    # Basic column contract
    for col in ("high", "low", "close"):
        if col not in bars_df.columns:
            raise ValueError(f"bars_df missing required column '{col}'")

    # ATR (optional)
    atr_series: pd.Series | None = None
    if compute_atr_multiples:
        atr_series = _compute_atr_series(bars_df)

    idx = bars_df.index
    highs = bars_df["high"].astype(float).to_numpy()
    lows = bars_df["low"].astype(float).to_numpy()
    closes = bars_df["close"].astype(float).to_numpy()

    long_mfe: list[float] = []
    long_mae: list[float] = []
    short_mfe: list[float] = []
    short_mae: list[float] = []

    long_mfe_atr: list[float] = []
    long_mae_atr: list[float] = []
    short_mfe_atr: list[float] = []
    short_mae_atr: list[float] = []

    valid_matches: list[PatternMatchModel] = []

    # Helper to get timestamp from match with minimal assumptions
    def _end_ts(m: PatternMatchModel):
        if hasattr(m, "end_ts"):
            return getattr(m, "end_ts")
        if hasattr(m, "pattern") and hasattr(getattr(m, "pattern"), "end_ts"):
            return getattr(getattr(m, "pattern"), "end_ts")
        raise AttributeError("PatternMatchModel does not expose end_ts")

    for m in matches:
        ts = _end_ts(m)
        # Find exact position for entry bar (must exist)
        try:
            pos = idx.get_loc(ts)
            # get_loc can return slice if duplicate indices
            if isinstance(pos, slice):
                pos = pos.stop - 1
            elif isinstance(pos, np.ndarray):
                pos = int(pos[-1])
            else:
                pos = int(pos)
        except KeyError:
            # fallback: use searchsorted, but require exact match for entry bar
            pos = int(idx.searchsorted(ts, side="left"))
            if pos >= len(idx) or idx[pos] != ts:
                continue

        entry = float(closes[pos])
        start = pos + 1
        end = start + horizon_bars
        if end > len(idx):
            continue  # insufficient future bars

        future_high = float(np.max(highs[start:end]))
        future_low = float(np.min(lows[start:end]))

        lmfe = max(0.0, future_high - entry)
        lmae = max(0.0, entry - future_low)
        smfe = max(0.0, entry - future_low)
        smae = max(0.0, future_high - entry)

        long_mfe.append(lmfe)
        long_mae.append(lmae)
        short_mfe.append(smfe)
        short_mae.append(smae)

        if atr_series is not None:
            atr_val = float(atr_series.iloc[pos])
            if math.isfinite(atr_val) and atr_val > 0.0:
                long_mfe_atr.append(lmfe / atr_val)
                long_mae_atr.append(lmae / atr_val)
                short_mfe_atr.append(smfe / atr_val)
                short_mae_atr.append(smae / atr_val)

        valid_matches.append(m)

    if len(valid_matches) == 0:
        raise ValueError("No matches with sufficient future bars")

    # Summaries
    s_long_mfe = _summary(long_mfe)
    s_long_mae = _summary(long_mae)
    s_short_mfe = _summary(short_mfe)
    s_short_mae = _summary(short_mae)

    meta_match = None
    for _m in matches:
        if getattr(_m, 'pattern_id', None) and getattr(_m, 'instrument', None) and getattr(_m, 'timeframe', None):
            meta_match = _m
            break
    if meta_match is None and matches:
        meta_match = matches[0]

    payload: Dict[str, Any] = {
        # Required by PatternStatsModel in this repo
        "pattern_id": getattr(meta_match, "pattern_id", None) if meta_match is not None else None,
        "instrument": getattr(meta_match, "instrument", None) if meta_match is not None else None,
        "timeframe": getattr(meta_match, "timeframe", None) if meta_match is not None else None,        "n_occurrences": len(valid_matches),
        "horizon_bars": int(horizon_bars),
        # metric summaries
        "long_mfe": s_long_mfe.__dict__,
        "long_mae": s_long_mae.__dict__,
        "short_mfe": s_short_mfe.__dict__,
        "short_mae": s_short_mae.__dict__,
        # hit rates
        "hit_rates": {
            "long_mfe_ge": _hit_rates_ge(long_mfe, targets_ticks),
            "short_mfe_ge": _hit_rates_ge(short_mfe, targets_ticks),
            "long_mae_le": _hit_rates_le(long_mae, targets_ticks),
            "short_mae_le": _hit_rates_le(short_mae, targets_ticks),
        },
    }

    # Optional schema-derived metadata: pattern_id/instrument/timeframe if present
    if valid_matches:
        m0 = valid_matches[0]
        for attr in ("pattern_id", "instrument", "timeframe"):
            if hasattr(m0, attr):
                payload[attr] = getattr(m0, attr)

        # Some schemas may nest definition/pattern info
        if "pattern_id" not in payload and hasattr(m0, "pattern") and hasattr(getattr(m0, "pattern"), "pattern_id"):
            payload["pattern_id"] = getattr(getattr(m0, "pattern"), "pattern_id")

    # ATR multiples (include only if requested and at least one valid ATR value existed)
    if compute_atr_multiples and atr_series is not None and len(long_mfe_atr) > 0:
        payload["long_mfe_atr"] = _summary(long_mfe_atr).__dict__
        payload["long_mae_atr"] = _summary(long_mae_atr).__dict__
        payload["short_mfe_atr"] = _summary(short_mfe_atr).__dict__
        payload["short_mae_atr"] = _summary(short_mae_atr).__dict__

    stats = _instantiate_stats_model(payload)

    # Extra safety (gate-style assertions): keep deterministic + bounded
    # Probabilities in [0,1] if present in produced model
    try:
        hr = getattr(stats, "hit_rates")
        # hr could be dict-like or model
        hr_dict: Mapping[str, Any]
        if isinstance(hr, Mapping):
            hr_dict = hr
        else:
            hr_dict = hr.__dict__  # type: ignore[assignment]
        for k in ("long_mfe_ge", "short_mfe_ge", "long_mae_le", "short_mae_le"):
            if k not in hr_dict:
                continue
            for lvl, p in hr_dict[k]:
                if not (0.0 <= float(p) <= 1.0):
                    raise ValueError(f"Hit-rate probability out of bounds for {k}: {p}")
    except Exception:
        # don't fail if schema doesn't expose hit_rates in that way
        pass

    return stats


