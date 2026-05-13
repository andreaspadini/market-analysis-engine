from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from engines.pattern_engine.bar_loader import load_bars
from engines.pattern_engine.manual.manual_template_matcher import (
    find_manual_template_matches,
)


def _parse_date_start(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _parse_date_end(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(
        hour=23,
        minute=59,
        second=59,
        tzinfo=timezone.utc,
    )


def _default_run_id_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _pattern_id(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return "manual_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def run_manual_template_engine(
    *,
    config_path: str | Path,
    output_dir: str | Path,
    run_id: str | None = None,
    engine_version: str = "1.0",
) -> dict[str, str]:
    config_path = Path(config_path)
    output_dir = Path(output_dir)

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manual_template config root must be a mapping")

    dataset = payload.get("dataset")
    config = payload.get("config")

    if not isinstance(dataset, dict):
        raise ValueError("manual_template payload requires dataset")
    if not isinstance(config, dict):
        raise ValueError("manual_template payload requires config")

    if config.get("mode") != "manual_template":
        raise ValueError("run_manual_template_engine requires mode='manual_template'")

    builder = config.get("pattern_builder")
    if builder is None:
        builder = config

    if not isinstance(builder, dict):
        raise ValueError("pattern_builder must be a mapping")

    instruments = dataset.get("instruments")
    if not instruments:
        raise ValueError("dataset.instruments is required")

    instrument = str(instruments[0])
    timeframe = str(dataset["timeframe"])
    start_ts = _parse_date_start(str(dataset["start_date"]))
    end_ts = _parse_date_end(str(dataset["end_date"]))

    tick_size = float(builder["tick_size"])
    length_bars = int(builder["length_bars"])
    tolerance = builder["tolerance"]
    candles = builder["candles"]

    if len(candles) != length_bars:
        raise ValueError("length_bars must equal len(candles)")

    include_delta = any(c.get("delta") is not None for c in candles if isinstance(c, dict))

    bars_df = load_bars(
        instrument=instrument,
        timeframe=timeframe,
        start_ts=start_ts,
        end_ts=end_ts,
        include_delta=include_delta,
        config=payload,
    )

    bars_df["timestamp"] = pd.to_datetime(bars_df["timestamp"], utc=True)
    bars_df = bars_df.sort_values("timestamp").reset_index(drop=True)

    run_id_final = run_id or _default_run_id_utc()
    pid = _pattern_id(
        {
            "dataset": dataset,
            "config": config,
            "run_id": run_id_final,
        }
    )

    matches = find_manual_template_matches(
        pattern_id=pid,
        instrument=instrument,
        timeframe=timeframe,
        bars_df=bars_df,
        template_candles=candles,
        tolerance=tolerance,
        tick_size=tick_size,
        min_similarity=float(builder.get("min_similarity", 0.0)),
        engine_version=engine_version,
        run_id=run_id_final,
    )

    version_dir = output_dir / f"pattern_engine_v{engine_version}"

    matches_path = (
        version_dir
        / "matches"
        / f"pattern_matches_v{engine_version}_{instrument}_{timeframe}_{dataset['start_date']}-{dataset['end_date']}.csv"
    )

    stats_path = (
        version_dir
        / "stats"
        / f"pattern_stats_v{engine_version}_{instrument}_{timeframe}_{dataset['start_date']}-{dataset['end_date']}.csv"
    )

    ohlc_path = (
        version_dir
        / "dataset"
        / f"pattern_ohlc_v{engine_version}_{instrument}_{timeframe}_{dataset['start_date']}-{dataset['end_date']}.csv"
    )

    config_snapshot_path = version_dir / "config" / "manual_template_snapshot.yaml"

    match_rows = [m.to_row() for m in matches]
    matches_df = pd.DataFrame(match_rows)
    _write_csv(matches_df, matches_path)

    stats_df = pd.DataFrame(
        [
            {
                "pattern_id": pid,
                "instrument": instrument,
                "timeframe": timeframe,
                "mode": "manual_template",
                "length_bars": length_bars,
                "n_occurrences": len(matches),
                "max_similarity_score": (
                    max([float(m.similarity_score) for m in matches]) if matches else 0.0
                ),
            }
        ]
    )
    _write_csv(stats_df, stats_path)

    ohlc_cols = [c for c in ["timestamp", "open", "high", "low", "close", "volume", "delta"] if c in bars_df.columns]
    _write_csv(bars_df.loc[:, ohlc_cols], ohlc_path)

    config_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    config_snapshot_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    return {
        "matches": str(matches_path),
        "stats": str(stats_path),
        "ohlc": str(ohlc_path),
        "config": str(config_snapshot_path),
    }