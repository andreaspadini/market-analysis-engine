from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd
import yaml

from .errors import EmptyDatasetError, MixedInstrumentError, MixedTimeframeError


# -------------------------
# Helpers (deterministic)
# -------------------------

def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        # Treat naive datetimes as UTC to keep deterministic behavior
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _yyyymmdd(dt: datetime) -> str:
    dt = _ensure_utc(dt)
    return dt.strftime("%Y%m%d")


def _date_range_from_matches(matches: Sequence[Any]) -> str:
    # Uses start_ts/end_ts if present, otherwise timestamp
    def _get_dt(m: Any, attr: str) -> Optional[datetime]:
        v = getattr(m, attr, None)
        return v if isinstance(v, datetime) else None

    starts: List[datetime] = []
    ends: List[datetime] = []

    for m in matches:
        s = _get_dt(m, "start_ts") or _get_dt(m, "timestamp")
        e = _get_dt(m, "end_ts") or _get_dt(m, "timestamp")
        if s:
            starts.append(_ensure_utc(s))
        if e:
            ends.append(_ensure_utc(e))

    if not starts or not ends:
        # last resort deterministic placeholder
        return "unknown-unknown"

    return f"{_yyyymmdd(min(starts))}-{_yyyymmdd(max(ends))}"


def _stable_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _coerce_rows(items: Sequence[Any], prefer_method: str = "to_row") -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for it in items:
        if hasattr(it, prefer_method) and callable(getattr(it, prefer_method)):
            r = getattr(it, prefer_method)()
            if not isinstance(r, dict):
                raise TypeError(f"{type(it).__name__}.{prefer_method}() must return dict, got {type(r)}")
            rows.append(r)
        elif hasattr(it, "model_dump") and callable(getattr(it, "model_dump")):
            rows.append(it.model_dump())
        elif isinstance(it, dict):
            rows.append(it)
        else:
            raise TypeError(f"Cannot convert {type(it).__name__} to row dict")
    return rows


def _assert_single_value(values: Iterable[str], exc_type: type[Exception]) -> str:
    vals = sorted({v for v in values if v is not None})
    if len(vals) != 1:
        raise exc_type(f"Expected exactly 1 unique value, got {vals}")
    return vals[0]


def _write_csv_deterministic(df: pd.DataFrame, path: Path) -> None:
    # Deterministic CSV: fixed column order, no index, consistent line endings, quoting minimal.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(list(df.columns))
        for row in df.itertuples(index=False, name=None):
            writer.writerow(list(row))


def _try_write_parquet(df: pd.DataFrame, path: Path) -> bool:
    # Optional Parquet: only if engine available (pyarrow or fastparquet)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(path, index=False)
        return True
    except Exception:
        return False


# -------------------------
# Public API
# -------------------------

@dataclass(frozen=True)
class ExportArtifacts:
    frozen_root: Path
    version_dir: Path
    matches_path: Optional[Path]
    stats_path: Optional[Path]
    config_snapshot_path: Path
    schema_paths: List[Path]
    manifest_path: Path


def export_pattern_run(
    *,
    frozen_root: Path,
    engine_version: str,
    run_id: str,
    pattern_definition: Any,
    matches: Sequence[Any],
    stats: Any,
    bars_df: pd.DataFrame,
    config_snapshot: Mapping[str, Any],
    export_parquet: bool = False,
    export_schema_json: bool = False,
) -> ExportArtifacts:
    """
    Pure export, deterministic, reproducible.

    Writes inside:
      pattern_engine_frozen/pattern_engine_vX_Y_Z/{matches,stats,config,schema}/...

    Required:
      - matches dataset (non-empty)
      - stats dataset (non-empty single-row)
      - config snapshot
      - manifest_sha256.json

    No analysis is performed.
    """
    frozen_root = Path(frozen_root)
    version_dir = frozen_root / f"pattern_engine_v{engine_version}"

    # Create required dirs
    matches_dir = version_dir / "matches"
    stats_dir = version_dir / "stats"
    dataset_dir = version_dir / "dataset"
    config_dir = version_dir / "config"
    schema_dir = version_dir / "schema"

    for d in (matches_dir, stats_dir, dataset_dir, config_dir, schema_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Always write VERSION.txt (deterministic content)
    (version_dir / "VERSION.txt").write_text(f"{engine_version}\n", encoding="utf-8")

    # Minimal CHANGELOG.md if missing (do not inject timestamps)
    changelog = version_dir / "CHANGELOG.md"
    if not changelog.exists():
        changelog.write_text(
            "# Changelog\n\n"
            f"## v{engine_version}\n"
            "- Export artifacts generated by Export Engine (Capitolo 9)\n",
            encoding="utf-8",
        )

    # -------------------------
    # Matches dataset (required)
    # -------------------------
    if not matches:
        raise EmptyDatasetError("matches is empty (required)")

    match_rows = _coerce_rows(matches, prefer_method="to_row")
    df_matches = pd.DataFrame(match_rows)

    # Enforce single-instrument / single-timeframe per file
    instrument = _assert_single_value(df_matches["instrument"].astype(str).tolist(), MixedInstrumentError)
    timeframe = _assert_single_value(df_matches["timeframe"].astype(str).tolist(), MixedTimeframeError)

    date_range = _date_range_from_matches(matches)

    matches_basename = f"pattern_matches_v{engine_version}_{instrument}_{timeframe}_{date_range}"
    matches_csv_path = matches_dir / f"{matches_basename}.csv"
    _write_csv_deterministic(df_matches, matches_csv_path)

    matches_parquet_path: Optional[Path] = None
    if export_parquet:
        p = matches_dir / f"{matches_basename}.parquet"
        if _try_write_parquet(df_matches, p):
            matches_parquet_path = p

    # -------------------------
    # Stats dataset (required)
    # -------------------------
    stats_row = _coerce_rows([stats], prefer_method="to_row")[0]
    df_stats = pd.DataFrame([stats_row])

    # Enforce same instrument/timeframe if present in stats (recommended)
    if "instrument" in df_stats.columns:
        instrument_stats = _assert_single_value(df_stats["instrument"].astype(str).tolist(), MixedInstrumentError)
        if instrument_stats != instrument:
            raise MixedInstrumentError(f"Stats instrument {instrument_stats} != matches instrument {instrument}")
    if "timeframe" in df_stats.columns:
        timeframe_stats = _assert_single_value(df_stats["timeframe"].astype(str).tolist(), MixedTimeframeError)
        if timeframe_stats != timeframe:
            raise MixedTimeframeError(f"Stats timeframe {timeframe_stats} != matches timeframe {timeframe}")

    if df_stats.empty:
        raise EmptyDatasetError("stats is empty after conversion (required)")

    stats_basename = f"pattern_stats_v{engine_version}_{instrument}_{timeframe}_{date_range}"
    stats_csv_path = stats_dir / f"{stats_basename}.csv"
    _write_csv_deterministic(df_stats, stats_csv_path)

    stats_parquet_path: Optional[Path] = None
    if export_parquet:
        p = stats_dir / f"{stats_basename}.parquet"
        if _try_write_parquet(df_stats, p):
            stats_parquet_path = p

    # -------------------------
    # OHLC dataset (required for drill-down visualization)
    # -------------------------
    if bars_df is None or bars_df.empty:
        raise EmptyDatasetError("bars_df is empty (required for OHLC export)")

    ohlc_columns = [c for c in ["timestamp", "open", "high", "low", "close", "volume", "delta"] if c in bars_df.columns]
    if not {"timestamp", "open", "high", "low", "close"}.issubset(set(ohlc_columns)):
        raise EmptyDatasetError("bars_df missing required OHLC columns for export")

    df_ohlc = bars_df.loc[:, ohlc_columns].copy()

    if "timestamp" in df_ohlc.columns:
        df_ohlc["timestamp"] = pd.to_datetime(df_ohlc["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    ohlc_basename = f"pattern_ohlc_v{engine_version}_{instrument}_{timeframe}_{date_range}"
    ohlc_csv_path = dataset_dir / f"{ohlc_basename}.csv"
    _write_csv_deterministic(df_ohlc, ohlc_csv_path)

    ohlc_parquet_path: Optional[Path] = None
    if export_parquet:
        p = dataset_dir / f"{ohlc_basename}.parquet"
        if _try_write_parquet(df_ohlc, p):
            ohlc_parquet_path = p

    # -------------------------
    # Config snapshot (required)
    # -------------------------
    config_snapshot_path = config_dir / "config_snapshot.yaml"
    # Deterministic YAML dump: sorted keys, stable formatting
    config_snapshot_path.write_text(
        yaml.safe_dump(
            dict(config_snapshot),
            sort_keys=True,
            allow_unicode=True,
            default_flow_style=False,
            width=120,
        ),
        encoding="utf-8",
    )

    # -------------------------
    # Schema JSON (optional)
    # -------------------------
    schema_paths: List[Path] = []
    if export_schema_json:
        # Reflect Pydantic model schema if available, otherwise reflect dataset columns.
        def _write_schema(name: str, schema_obj: Dict[str, Any]) -> Path:
            p = schema_dir / f"{name}_v{engine_version}.schema.json"
            p.write_text(_stable_json_dumps(schema_obj) + "\n", encoding="utf-8")
            return p

        # Matches schema
        if hasattr(type(matches[0]), "model_json_schema"):
            schema_obj = type(matches[0]).model_json_schema()
        else:
            schema_obj = {
                "title": "PatternMatchesDataset",
                "type": "object",
                "properties": {c: {"type": "string"} for c in df_matches.columns},
                "required": list(df_matches.columns),
            }
        schema_paths.append(_write_schema("pattern_matches", schema_obj))

        # Stats schema
        if hasattr(type(stats), "model_json_schema"):
            schema_obj = type(stats).model_json_schema()
        else:
            schema_obj = {
                "title": "PatternStatsDataset",
                "type": "object",
                "properties": {c: {"type": "string"} for c in df_stats.columns},
                "required": list(df_stats.columns),
            }
        schema_paths.append(_write_schema("pattern_stats", schema_obj))

        # PatternDefinition schema (nice-to-have, still reflective)
        if hasattr(type(pattern_definition), "model_json_schema"):
            schema_paths.append(_write_schema("pattern_definition", type(pattern_definition).model_json_schema()))

    # -------------------------
    # Manifest sha256 (required, deterministic)
    # -------------------------
    files_to_hash: List[Path] = [
        matches_csv_path,
        stats_csv_path,
        ohlc_csv_path,
        config_snapshot_path,
        version_dir / "VERSION.txt",
        version_dir / "CHANGELOG.md",
    ]
    if matches_parquet_path:
        files_to_hash.append(matches_parquet_path)
    if stats_parquet_path:
        files_to_hash.append(stats_parquet_path)
    if ohlc_parquet_path:
        files_to_hash.append(ohlc_parquet_path)
    files_to_hash.extend(schema_paths)

    # Build relative manifest with stable ordering
    manifest: Dict[str, Any] = {
        "engine_version": engine_version,
        "run_id": run_id,
        "files": [],
    }

    rels = sorted([p.relative_to(version_dir).as_posix() for p in files_to_hash])
    rel_to_abs = {p.relative_to(version_dir).as_posix(): p for p in files_to_hash}

    for rel in rels:
        p = rel_to_abs[rel]
        manifest["files"].append(
            {
                "path": rel,
                "sha256": _sha256_file(p),
                "bytes": int(p.stat().st_size),
            }
        )

    manifest_path = version_dir / "manifest_sha256.json"
    manifest_path.write_text(_stable_json_dumps(manifest) + "\n", encoding="utf-8")

    return ExportArtifacts(
        frozen_root=frozen_root,
        version_dir=version_dir,
        matches_path=matches_csv_path,
        stats_path=stats_csv_path,
        config_snapshot_path=config_snapshot_path,
        schema_paths=schema_paths,
        manifest_path=manifest_path,
    )
