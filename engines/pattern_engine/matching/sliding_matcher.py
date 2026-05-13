from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

import pandas as pd

from engines.pattern_engine.pattern_schema import PatternDefinitionModel, PatternMatchModel


# ----------------------------
# Internal: dependency resolver
# ----------------------------

def _resolve_extract_features() -> Callable[..., Any]:
    """
    Resolve Cap.5 feature extractor without creating hard circular deps.
    Tries a few canonical import paths; adjust if your Cap.5 module name differs.
    """
    candidates = [
        ("market_analysis_engine.pattern_engine.features.feature_extractor", "extract_features"),
        ("market_analysis_engine.pattern_engine.features.extractor", "extract_features"),
        ("market_analysis_engine.pattern_engine.feature_extraction", "extract_features"),
        ("market_analysis_engine.pattern_engine.features", "extract_features"),
    ]
    last_err: Optional[Exception] = None
    for mod, fn in candidates:
        try:
            m = __import__(mod, fromlist=[fn])
            f = getattr(m, fn)
            if callable(f):
                return f
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise ImportError(
        "Cap.5 extract_features not found. Tried: "
        + ", ".join([f"{m}.{f}" for m, f in candidates])
    ) from last_err


def _resolve_compute_similarity() -> Callable[..., Any]:
    """
    Resolve Cap.6 similarity engine without creating hard circular deps.
    Tries a few canonical import paths; adjust if your Cap.6 module name differs.
    """
    candidates = [
        ("market_analysis_engine.pattern_engine.similarity.similarity_engine", "compute_similarity"),
        ("market_analysis_engine.pattern_engine.similarity.engine", "compute_similarity"),
        ("market_analysis_engine.pattern_engine.similarity", "compute_similarity"),
        ("market_analysis_engine.pattern_engine.similarity_engine", "compute_similarity"),
    ]
    last_err: Optional[Exception] = None
    for mod, fn in candidates:
        try:
            m = __import__(mod, fromlist=[fn])
            f = getattr(m, fn)
            if callable(f):
                return f
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise ImportError(
        "Cap.6 compute_similarity not found. Tried: "
        + ", ".join([f"{m}.{f}" for m, f in candidates])
    ) from last_err


# Cached callables (lazy init at first call)
_EXTRACT_FEATURES: Optional[Callable[..., Any]] = None
_COMPUTE_SIMILARITY: Optional[Callable[..., Any]] = None


def _get_ts_series(bars_df: pd.DataFrame) -> pd.Series:
    """
    bars_df is assumed tz-aware and ordered (Cap.4).

    Supports either:
      - DatetimeIndex
      - a 'ts' column
      - a 'timestamp' column (common in user scripts)
    """
    if isinstance(bars_df.index, pd.DatetimeIndex):
        return pd.Series(bars_df.index, index=bars_df.index)

    if "ts" in bars_df.columns:
        return pd.to_datetime(bars_df["ts"], utc=True)

    # extra tolerance for ad-hoc scripts (no mutation)
    if "timestamp" in bars_df.columns:
        return pd.to_datetime(bars_df["timestamp"], utc=True)

    raise ValueError("bars_df must have a DatetimeIndex or a 'ts'/'timestamp' column.")


def _slice_reference_window(
    *,
    pattern_def: PatternDefinitionModel,
    bars_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Materialize reference window df in a purely orchestrative way.

    Supported reference_window shapes (best-effort):
      - contains 'bars_df' already (DataFrame)
      - contains 'bars' (list of dicts) -> DataFrame
      - contains 'start_ts' and 'end_ts' -> slice from bars_df by timestamps (inclusive)
      - contains 'start_ts' and 'length_bars' -> slice by positional length from start_ts

    NOTE: reference_window may be a dict OR a Pydantic model (Cap.3).
    """
    rw = getattr(pattern_def, "reference_window", None)
    if rw is None:
        raise ValueError("pattern_def.reference_window is required.")

    # Normalize rw -> dict (handles Pydantic models)
    if isinstance(rw, dict):
        rw_dict = rw
    else:
        if hasattr(rw, "model_dump") and callable(getattr(rw, "model_dump")):
            rw_dict = rw.model_dump()
        elif hasattr(rw, "dict") and callable(getattr(rw, "dict")):
            rw_dict = rw.dict()
        else:
            keys = (
                "bars_df",
                "bars",
                "start_ts",
                "end_ts",
                "instrument",
                "timeframe",
                "length_bars",
            )
            rw_dict = {k: getattr(rw, k) for k in keys if hasattr(rw, k)}

    # Case 1: reference_window already carries a DataFrame
    maybe_df = rw_dict.get("bars_df")
    if isinstance(maybe_df, pd.DataFrame):
        df = maybe_df
        if len(df) != pattern_def.length_bars:
            raise ValueError(
                f"reference window length mismatch: expected {pattern_def.length_bars}, got {len(df)}"
            )
        return df.copy(deep=True)

    # Case 1b: bars list -> DataFrame
    if isinstance(rw_dict.get("bars"), list):
        df = pd.DataFrame(rw_dict["bars"])
        if len(df) != pattern_def.length_bars:
            raise ValueError(
                f"reference window length mismatch: expected {pattern_def.length_bars}, got {len(df)}"
            )
        return df.copy(deep=True)

    # Case 2: timestamps -> slice from bars_df (inclusive)
    if ("start_ts" in rw_dict) and ("end_ts" in rw_dict):
        start_ts = pd.Timestamp(rw_dict["start_ts"])
        end_ts = pd.Timestamp(rw_dict["end_ts"])

        if isinstance(bars_df.index, pd.DatetimeIndex):
            df_ref = bars_df.loc[start_ts:end_ts]
        else:
            ts = pd.to_datetime(bars_df["ts"])
            df_ref = bars_df.loc[(ts >= start_ts) & (ts <= end_ts)]

        if len(df_ref) != pattern_def.length_bars:
            raise ValueError(
                f"reference window slice length mismatch: expected {pattern_def.length_bars}, got {len(df_ref)}"
            )
        return df_ref.copy(deep=True)

    # Case 2b: (start_ts + length_bars) -> slice from bars_df by position
    # Matches your Cap.3 ReferenceWindowModel dump: {start_ts, length_bars, ...} (no end_ts)
    if ("start_ts" in rw_dict) and ("length_bars" in rw_dict):
        start_ts = pd.Timestamp(rw_dict["start_ts"])
        L = int(rw_dict["length_bars"])

        if L <= 0:
            raise ValueError("reference_window.length_bars must be > 0")

        if isinstance(bars_df.index, pd.DatetimeIndex):
            if start_ts not in bars_df.index:
                raise ValueError("reference window start_ts not found in bars_df index")

            start_pos = bars_df.index.get_loc(start_ts)

            # get_loc can return slice/array if index has duplicates; choose first deterministically
            if isinstance(start_pos, slice):
                start_pos = start_pos.start
            elif not isinstance(start_pos, int):
                start_pos = int(start_pos[0])

            end_pos = start_pos + L - 1
            if end_pos >= len(bars_df):
                raise ValueError("reference window exceeds available bars_df length")

            df_ref = bars_df.iloc[start_pos : end_pos + 1]
        else:
            # Support both 'ts' (Cap.4 canonical) and 'timestamp' (common in ad-hoc scripts)
            ts_col = None
            if "ts" in bars_df.columns:
                ts_col = "ts"
            elif "timestamp" in bars_df.columns:
                ts_col = "timestamp"
            else:
                raise ValueError("bars_df must have a DatetimeIndex or a 'ts'/'timestamp' column")

            ts = pd.to_datetime(bars_df[ts_col], utc=True)

            matches = ts[ts == start_ts]
            if matches.empty:
                raise ValueError(f"reference window start_ts not found in bars_df['{ts_col}']")

            start_pos = int(matches.index[0])
            end_pos = start_pos + L - 1
            if end_pos >= len(bars_df):
                raise ValueError("reference window exceeds available bars_df length")

            df_ref = bars_df.iloc[start_pos : end_pos + 1]


        if len(df_ref) != pattern_def.length_bars:
            raise ValueError(
                f"reference window slice length mismatch: expected {pattern_def.length_bars}, got {len(df_ref)}"
            )

        return df_ref.copy(deep=True)

    raise ValueError(
        "Unable to materialize reference window. "
        "Expected reference_window to contain bars_df, bars, (start_ts,end_ts), or (start_ts,length_bars)."
    )


@dataclass(frozen=True)
class _SimilarityResult:
    score: float
    distance_components: Optional[dict[str, float]] = None


def _call_similarity(
    compute_similarity: Callable[..., Any],
    *,
    ref_features: Any,
    win_features: Any,
    pattern_def: PatternDefinitionModel,
) -> _SimilarityResult:
    """
    Calls Cap.6 compute_similarity in a signature-tolerant way (orchestrative).
    We pass common knobs if present on pattern_def; compute_similarity may ignore extras.
    """
    kwargs: dict[str, Any] = {}

    # Normalize common fields (Cap.6 expects dict-like .get())
    if hasattr(pattern_def, "feature_set"):
        kwargs["feature_set"] = _as_dict(getattr(pattern_def, "feature_set"))

    if hasattr(pattern_def, "weights"):
        kwargs["weights"] = _as_dict(getattr(pattern_def, "weights"))

    if hasattr(pattern_def, "metric"):
        kwargs["metric"] = getattr(pattern_def, "metric")

    # Cap.6 required kw-only: distance_caps
    if hasattr(pattern_def, "distance_caps"):
        kwargs["distance_caps"] = _as_dict(getattr(pattern_def, "distance_caps"))
    elif hasattr(pattern_def, "cap"):
        kwargs["distance_caps"] = _as_dict(getattr(pattern_def, "cap"))
    else:
        kwargs["distance_caps"] = {}  # safe default dict

    # Some designs nest similarity params (also normalize if present)
    sim_cfg = getattr(pattern_def, "similarity", None)
    if sim_cfg is not None:
        sim_cfg_dict = _as_dict(sim_cfg)
        if isinstance(sim_cfg_dict, dict):
            # allow nested config to override
            kwargs.update(sim_cfg_dict)
            # ensure dict-like for these keys if provided via similarity config
            if "feature_set" in kwargs:
                kwargs["feature_set"] = _as_dict(kwargs["feature_set"])
            if "weights" in kwargs:
                kwargs["weights"] = _as_dict(kwargs["weights"])
            if "distance_caps" in kwargs:
                kwargs["distance_caps"] = _as_dict(kwargs["distance_caps"])

    out = compute_similarity(ref_features, win_features, **kwargs)


    # Accept either:
    #  - float score
    #  - (score, components)
    #  - dict with 'score' and optional 'distance_components'
    if isinstance(out, (int, float)):
        return _SimilarityResult(score=float(out), distance_components=None)

    if isinstance(out, tuple) and len(out) == 2:
        score, comps = out
        return _SimilarityResult(score=float(score), distance_components=comps)

    if isinstance(out, dict) and "score" in out:
        return _SimilarityResult(
            score=float(out["score"]),
            distance_components=out.get("distance_components"),
        )

    raise TypeError(
        "compute_similarity returned an unsupported type. "
        "Expected float | (float, dict) | {'score': float, ...}"
    )

def _as_dict(maybe_model: Any) -> Any:
    """Convert Pydantic models to plain dict when needed; otherwise return as-is."""
    if maybe_model is None:
        return None
    if isinstance(maybe_model, dict):
        return maybe_model
    if hasattr(maybe_model, "model_dump") and callable(getattr(maybe_model, "model_dump")):
        return maybe_model.model_dump()
    if hasattr(maybe_model, "dict") and callable(getattr(maybe_model, "dict")):
        return maybe_model.dict()
    return maybe_model


# ----------------------------
# Public API (Cap.7 contract)
# ----------------------------

def find_pattern_matches(
    *,
    pattern_def: PatternDefinitionModel,
    bars_df: pd.DataFrame,
    tolerance: float,
) -> list[PatternMatchModel]:
    """
    Cap.7 Sliding Window & Matching Engine (orchestrator only).

    - Deterministic sliding windows (overlapping allowed)
    - No side effects, no bars_df mutation
    - Uses Cap.5 extract_features and Cap.6 compute_similarity
    - Emits PatternMatchModel for windows with score >= tolerance
    """
    if not (0.0 < float(tolerance) <= 1.0):
        raise ValueError("tolerance must be in (0, 1].")

    if len(bars_df) < pattern_def.length_bars:
        return []
    
    feature_set_dict = _as_dict(pattern_def.feature_set)
    normalization_mode = pattern_def.normalization_mode


    global _EXTRACT_FEATURES, _COMPUTE_SIMILARITY  # noqa: PLW0603
    if _EXTRACT_FEATURES is None:
        _EXTRACT_FEATURES = _resolve_extract_features()
    if _COMPUTE_SIMILARITY is None:
        _COMPUTE_SIMILARITY = _resolve_compute_similarity()

    extract_features = _EXTRACT_FEATURES
    compute_similarity = _COMPUTE_SIMILARITY

    # Reference window -> reference features
    df_ref = _slice_reference_window(pattern_def=pattern_def, bars_df=bars_df).copy(deep=True)

    # Cap.5 extractor signature tolerance
    ref_features = extract_features(
        df_ref,
        feature_set=feature_set_dict,
        normalization_mode=normalization_mode,
    )



    matches: list[PatternMatchModel] = []
    L = int(pattern_def.length_bars)

    ts_series = _get_ts_series(bars_df)

    # Sliding windows (deterministic, overlapping allowed)
    for i in range(0, len(bars_df) - L + 1):
        df_win = bars_df.iloc[i : i + L].copy(deep=True)

        start_ts = pd.Timestamp(ts_series.iloc[i])
        end_ts = pd.Timestamp(ts_series.iloc[i + L - 1])

        # Temporal coherence gate
        if not (start_ts < end_ts):
            continue

        win_features = extract_features(
            df_win,
            feature_set=feature_set_dict,
            normalization_mode=normalization_mode,
        )



        sim = _call_similarity(
            compute_similarity,
            ref_features=ref_features,
            win_features=win_features,
            pattern_def=pattern_def,
        )

        score = float(sim.score)

        # Boundaries gate (clamp for tiny numeric drift)
        if score < 0.0:
            score = 0.0
        elif score > 1.0:
            score = 1.0

        if score >= float(tolerance):
            matches.append(
                PatternMatchModel(
                    pattern_id=pattern_def.pattern_id,
                    instrument=pattern_def.instrument,
                    timeframe=pattern_def.timeframe,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    similarity_score=score,
                    distance_components=sim.distance_components,
                    # Cap.3 required fields
                    engine_version=pattern_def.engine_version,
                    run_id=getattr(pattern_def, "run_id", "local_test_run"),
                )
            )

    return matches
