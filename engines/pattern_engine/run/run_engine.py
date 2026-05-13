from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING
import pandas as pd

import yaml

from engines.pattern_engine.bar_loader import NoDataError, load_bars
from engines.pattern_engine.matching.sliding_matcher import find_pattern_matches
from engines.pattern_engine.outcomes.outcome_engine import compute_outcome_stats
from engines.pattern_engine.pattern_config import PatternConfig
from engines.pattern_engine.pattern_schema import (
    PatternDefinitionModel,
    PatternMatchModel,
    PatternStatsModel,
)

# Cap.9: export_run_level puÃ² stare in pattern_engine.export o pattern_engine.export.run_level
try:
    from engines.pattern_engine.export import export_run_level  # type: ignore
except Exception:  # pragma: no cover
    from engines.pattern_engine.export.run_level import export_run_level  # type: ignore

if TYPE_CHECKING:
    try:
        from engines.pattern_engine.export.run_level import ExportArtifacts  # type: ignore
    except Exception:  # pragma: no cover
        from engines.pattern_engine.export import ExportArtifacts  # type: ignore
else:
    ExportArtifacts = Any


def _load_yaml_dict(config_path: Path) -> dict[str, Any]:
    raw = config_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid YAML root object in config: expected mapping, got {type(data).__name__}"
        )
    return data


def _validate_config(config_snapshot: dict[str, Any]) -> PatternConfig:
    """
    CompatibilitÃ  Pydantic v2/v1:
      - v2: PatternConfig.model_validate(...)
      - v1: PatternConfig.parse_obj(...)
    """
    if hasattr(PatternConfig, "model_validate"):
        return PatternConfig.model_validate(config_snapshot)  # type: ignore[attr-defined]
    return PatternConfig.parse_obj(config_snapshot)  # type: ignore[attr-defined]


def _default_run_id_utc() -> str:
    """
    Policy run_id ordinabile e filesystem-safe:
    timestamp UTC: YYYYMMDDTHHMMSSZ (es: 20260210T152012Z)
    """
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _validate_artifacts_paths(artifacts: Any) -> None:
    """
    Gate deterministico: se ExportArtifacts contiene path, devono esistere.
    Se sono file, devono essere non vuoti.
    """
    d = getattr(artifacts, "__dict__", None)
    if not isinstance(d, dict):
        return

    for k, v in d.items():
        if isinstance(v, (str, Path)):
            p = Path(v)
            if not p.exists():
                raise RuntimeError(f"ExportArtifacts.{k} does not exist: {p}")
            if p.is_file() and p.stat().st_size == 0:
                raise RuntimeError(f"ExportArtifacts.{k} is empty: {p}")


def _make_deterministic_pattern_id(
    *,
    instrument: str,
    timeframe: str,
    start_ts: Any,
    length_bars: int,
    feature_set_payload: dict[str, Any],
    normalization_mode: str,
) -> str:
    payload = {
        "instrument": instrument,
        "timeframe": timeframe,
        "start_ts": str(start_ts),
        "length_bars": int(length_bars),
        "feature_set": feature_set_payload,
        "normalization_mode": normalization_mode,
    }
    s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "pat_" + hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _model_to_payload(obj: Any) -> dict[str, Any]:
    """
    Converte Pydantic v2/v1 (o oggetto semplice) in dict.
    """
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # pydantic v2
    if hasattr(obj, "dict"):
        return obj.dict()  # pydantic v1
    # fallback best-effort
    out: dict[str, Any] = {}
    for k in ("instrument", "timeframe", "start_ts", "length_bars", "price", "volume", "delta"):
        if hasattr(obj, k):
            out[k] = getattr(obj, k)
    return out


def _coerce_ref_start_ts_to_bars(bars_df, start_ts):
    """
    Il matcher richiede che reference_window.start_ts sia presente esattamente in bars_df['timestamp'].
    Qui rendiamo deterministico l'allineamento:
      - normalizza a Timestamp tz-aware (UTC)
      - se non c'Ã¨ exact match, snappa al primo bar >= start_ts
    """
    import pandas as pd

    ts_dt = pd.to_datetime(bars_df["timestamp"])

    st = pd.Timestamp(start_ts)
    if st.tz is None:
        st = st.tz_localize("UTC")

    if (ts_dt == st).any():
        return st.to_pydatetime()

    ts_sorted = ts_dt.sort_values()
    pos = ts_sorted.searchsorted(st)
    if int(pos) >= len(ts_sorted):
        raise ValueError("reference window start_ts is after last available bar")
    return ts_sorted.iloc[int(pos)].to_pydatetime()


def run_pattern_engine(
    *,
    config_path: str | Path,
    output_dir: str | Path | None = None,  # override runtime (GUI)
    export_parquet: bool = False,
    export_schema_json: bool = False,
    run_id: str | None = None,
) -> ExportArtifacts:
    """
    Runner / orchestrazione finale (GUI-ready).
    Sequenza vincolante:
      1) load PatternConfig + snapshot dict
      2) engine_version dal config
      3) run_id (default UTC timestamp)
      4) load bars (include_delta da cfg.pattern.feature_set.delta)
      5) build PatternDefinitionModel (Cap.3 schema reale)
      6) matcher (Cap.7) -> matches
      7) outcome (Cap.8) -> stats
      8) export_run_level (Cap.9) con output_dir override + config_snapshot
      9) return ExportArtifacts
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    # 1) snapshot + validate (NON modificare il dict: PatternConfig forbids extra keys)
    config_snapshot = _load_yaml_dict(config_path)
    cfg = _validate_config(config_snapshot)

    # 2) engine_version
    engine_version = str(cfg.pattern_engine.version)

    # 3) run_id
    run_id_final = run_id or _default_run_id_utc()

    # 4) bars: instrument/timeframe/range + include_delta
    instrument = str(cfg.pattern.reference_window.instrument)
    timeframe = str(cfg.pattern.reference_window.timeframe)
    start_ts = cfg.universe.date_range.start
    end_ts = cfg.universe.date_range.end
    include_delta = bool(cfg.pattern.feature_set.delta)

    try:
        bars_df = load_bars(
            instrument=instrument,
            timeframe=timeframe,
            start_ts=start_ts,
            end_ts=end_ts,
            include_delta=include_delta,
            config=config_snapshot,
        )

        # Cap.8 expects bars_df indexed by timestamp (DatetimeIndex)
        if "timestamp" not in bars_df.columns:
            raise ValueError("bars_df must contain a 'timestamp' column")

        # normalize + index by timestamp (keep column for matcher)
        bars_df["timestamp"] = pd.to_datetime(bars_df["timestamp"], utc=True)
        bars_df = (
            bars_df.sort_values("timestamp")
            .set_index("timestamp", drop=False)
        )

    except NoDataError:
        raise
    except FileNotFoundError as e:
        raise ValueError(
            "Bars source file not found while loading data.\n"
            f"instrument={instrument} timeframe={timeframe} "
            f"start={start_ts} end={end_ts}\n"
            "Check your YAML data source paths and that the raw file exists."
        ) from e
    except Exception as e:
        msg = str(e)
        if "cannot parse raw bars file:" in msg or "No such file or directory" in msg:
            raise ValueError(
                "Bars loading failed (missing raw file or invalid data source).\n"
                f"instrument={instrument} timeframe={timeframe} "
                f"start={start_ts} end={end_ts}\n"
                f"details={msg}\n"
                "Fix: point the YAML to an instrument/dataset that exists (e.g. MNQ), "
                "or update the raw data path in the config."
            ) from e
        raise

    # 5) PatternDefinitionModel (Cap.3)
    rw = cfg.pattern.reference_window

    feature_set_payload = _model_to_payload(cfg.pattern.feature_set)
    reference_window_payload = _model_to_payload(rw)

    # normalization_mode: mapping robusto (Cap.5/Cap.2 possono usare nomi diversi)
    normalization_mode: str | None = None
    if hasattr(cfg.pattern, "price_normalizer") and hasattr(cfg.pattern.price_normalizer, "mode"):
        normalization_mode = str(cfg.pattern.price_normalizer.mode)
    if normalization_mode is None and hasattr(cfg.pattern, "normalization_mode"):
        v = getattr(cfg.pattern, "normalization_mode")
        if v is not None:
            normalization_mode = str(v)
    if normalization_mode is None and hasattr(cfg.pattern, "normalization") and hasattr(
        cfg.pattern.normalization, "mode"
    ):
        normalization_mode = str(cfg.pattern.normalization.mode)

    if normalization_mode is None:
        raise ValueError(
            "Cannot resolve normalization_mode from config. Expected one of:\n"
            "- pattern.price_normalizer.mode (recommended)\n"
            "- pattern.normalization_mode\n"
            "- pattern.normalization.mode\n"
            "Fix your YAML or update the normalization_mode mapping in run_engine.py."
        )

    # pattern_id: se non esiste nel config, deterministico
    pattern_id: str | None = None
    for attr in ("pattern_id", "id", "name", "pattern_name"):
        if hasattr(cfg.pattern, attr):
            v = getattr(cfg.pattern, attr)
            if v:
                pattern_id = str(v)
                break
    if pattern_id is None:
        pattern_id = _make_deterministic_pattern_id(
            instrument=str(rw.instrument),
            timeframe=str(rw.timeframe),
            start_ts=rw.start_ts,
            length_bars=int(rw.length_bars),
            feature_set_payload=feature_set_payload,
            normalization_mode=normalization_mode,
        )

    # Coerce reference start_ts to an actual bar timestamp (matcher requires exact hit)
    coerced_start_ts = _coerce_ref_start_ts_to_bars(bars_df, rw.start_ts)
    reference_window_payload["start_ts"] = coerced_start_ts

    effective_weights, normalized_weights = cfg.pattern.compute_effective_and_normalized_weights()
    weights_payload = normalized_weights.model_dump()
    distance_caps_payload = cfg.similarity.distance_caps.model_dump()

    pattern_def = PatternDefinitionModel(
        pattern_id=pattern_id,
        engine_version=engine_version,
        run_id=run_id_final,
        instrument=str(rw.instrument),
        timeframe=str(rw.timeframe),
        length_bars=int(rw.length_bars),
        reference_window=reference_window_payload,
        normalization_mode=normalization_mode,
        feature_set=feature_set_payload,
        weights=weights_payload,
        distance_caps=distance_caps_payload,
    )

    # 6) matcher (Cap.7)
    # IMPORTANT: non passare None a similarity_engine (weights/distance_caps)
    

    matches: list[PatternMatchModel] = find_pattern_matches(
        pattern_def=pattern_def,
        bars_df=bars_df,
        tolerance=float(cfg.similarity.tolerance),
    )

    matches = sorted(
        matches,
        key=lambda m: (-float(m.similarity_score), m.start_ts),
    )


    # 7) outcome (Cap.8)
    try:
        stats: PatternStatsModel = compute_outcome_stats(
            matches=matches,
            bars_df=bars_df,
            horizon_bars=int(cfg.outcome.horizon_bars),
            targets_ticks=list(cfg.outcome.targets_ticks),
            compute_atr_multiples=bool(cfg.outcome.compute_atr_multiples),
        )
    except ValueError as e:
        if "No matches with sufficient future bars" in str(e):
            raise ValueError(
                "Outcome failed: no matches have enough future bars to compute horizon.\n"
                f"horizon_bars={int(cfg.outcome.horizon_bars)}\n"
                "Fix: extend universe.date_range.end or reduce outcome.horizon_bars."
            ) from e
        raise

    # 8) export (Cap.9)
    out_dir = Path(output_dir) if output_dir is not None else Path(cfg.export.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = export_run_level(
        output_dir=out_dir,
        engine_version=engine_version,
        run_id=run_id_final,
        pattern_definition=pattern_def,
        matches=matches,
        stats=stats,
        bars_df=bars_df,
        config_snapshot=config_snapshot,
        export_parquet=export_parquet,
        export_schema_json=export_schema_json,
    )

    _validate_artifacts_paths(artifacts)
    return artifacts
