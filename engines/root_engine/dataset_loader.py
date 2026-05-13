from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any


class DatasetLoaderError(RuntimeError):
    """Errore base del loader dataset del Root Engine."""


def _require_mapping(dataset: Any) -> dict[str, Any]:
    if not isinstance(dataset, dict):
        raise DatasetLoaderError("dataset must be a dict")
    return dataset


def _require_single_instrument(dataset: dict[str, Any]) -> str:
    instruments = dataset.get("instruments")
    if not isinstance(instruments, list) or len(instruments) != 1:
        raise DatasetLoaderError(
            "Root Engine EDI-2B supports exactly one instrument: "
            "len(dataset['instruments']) must be 1"
        )
    instrument = instruments[0]
    if not isinstance(instrument, str) or not instrument.strip():
        raise DatasetLoaderError("dataset['instruments'][0] must be a non-empty string")
    return instrument


def _require_str_field(dataset: dict[str, Any], field: str) -> str:
    value = dataset.get(field)
    if not isinstance(value, str) or not value.strip():
        raise DatasetLoaderError(f"dataset['{field}'] must be a non-empty string")
    return value


def _parse_iso_date(value: str, field: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception as exc:
        raise DatasetLoaderError(
            f"dataset['{field}'] must be ISO-8601 compatible, got: {value!r}"
        ) from exc

def _resolve_market_data_root() -> Path:
    raw = os.environ.get("MARKET_DATA_ROOT")
    if not raw:
        raise DatasetLoaderError("MARKET_DATA_ROOT is not set")
    root = Path(raw)
    if not root.exists():
        raise DatasetLoaderError(f"MARKET_DATA_ROOT does not exist: {root}")
    if not root.is_dir():
        raise DatasetLoaderError(f"MARKET_DATA_ROOT is not a directory: {root}")
    return root


def _candidate_files(
    *,
    root: Path,
    instrument: str,
    timeframe: str,
    start_dt: datetime,
    end_dt: datetime,
) -> list[Path]:
    base_dir = root / instrument / timeframe
    if not base_dir.exists():
        raise DatasetLoaderError(f"Dataset path not found: {base_dir}")
    if not base_dir.is_dir():
        raise DatasetLoaderError(f"Dataset path is not a directory: {base_dir}")

    files: list[Path] = []
    for year in range(start_dt.year, end_dt.year + 1):
        path = base_dir / f"data_{year}.txt"
        if path.exists():
            files.append(path)

    if not files:
        raise DatasetLoaderError(
            f"No yearly txt files found for instrument={instrument!r}, "
            f"timeframe={timeframe!r}, years={start_dt.year}-{end_dt.year}"
        )

    return files


def _parse_txt_line(line: str, *, file_path: Path, line_no: int) -> dict[str, Any]:
    parts = [p.strip() for p in line.rstrip("\n\r").split(";")]
    if len(parts) < 9:
        raise DatasetLoaderError(
            f"Malformed row in {file_path} at line {line_no}: expected at least 9 columns"
        )

    try:
        bar_time = datetime.strptime(parts[2], "%d/%m/%Y %H:%M:%S")
        high = float(parts[3].replace(",", "."))
        low = float(parts[4].replace(",", "."))
        open_ = float(parts[5].replace(",", "."))
        close = float(parts[6].replace(",", "."))
        bid_volume = float(parts[7].replace(",", "."))
        ask_volume = float(parts[8].replace(",", "."))
    except Exception as exc:
        raise DatasetLoaderError(
            f"Unparseable row in {file_path} at line {line_no}"
        ) from exc

    return {
        "time": bar_time,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": bid_volume + ask_volume,
        "delta": ask_volume - bid_volume,
    }


def _load_file(file_path: Path, *, start_dt: datetime, end_dt: datetime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    with file_path.open("r", encoding="utf-8-sig") as f:
        header = f.readline()
        if not header:
            return rows

        for line_no, line in enumerate(f, start=2):
            if not line.strip():
                continue
            if line.startswith("Name;Index;DateTime;"):
                continue
            bar = _parse_txt_line(line, file_path=file_path, line_no=line_no)
            if start_dt <= bar["time"] <= end_dt:
                rows.append(bar)

    return rows


def load_dataset(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Load Root Engine bars from runtime canonical dataset.

    Expected dataset shape:
    {
        "dataset_id": "...",
        "instruments": ["MNQ"],
        "timeframe": "1m",
        "start_date": "...",
        "end_date": "..."
    }
    """
    dataset = _require_mapping(dataset)

    instrument = _require_single_instrument(dataset)
    timeframe = _require_str_field(dataset, "timeframe")
    start_date = _require_str_field(dataset, "start_date")
    end_date = _require_str_field(dataset, "end_date")

    start_dt = _parse_iso_date(start_date, "start_date")
    end_dt = _parse_iso_date(end_date, "end_date")
    if end_dt < start_dt:
        raise DatasetLoaderError("dataset['end_date'] must be >= dataset['start_date']")

    root = _resolve_market_data_root()
    files = _candidate_files(
        root=root,
        instrument=instrument,
        timeframe=timeframe,
        start_dt=start_dt,
        end_dt=end_dt,
    )

    bars: list[dict[str, Any]] = []
    for file_path in files:
        bars.extend(_load_file(file_path, start_dt=start_dt, end_dt=end_dt))

    bars.sort(key=lambda b: b["time"])
    return bars

def load_dataset_for_timeframe(dataset: dict[str, Any], timeframe: str) -> list[dict[str, Any]]:
    """
    Load the same canonical dataset window using an overridden timeframe.

    Keeps:
    - instrument
    - start_date
    - end_date
    - dataset_id (if present)

    Overrides only:
    - timeframe
    """
    dataset = _require_mapping(dataset).copy()

    if not isinstance(timeframe, str) or not timeframe.strip():
        raise DatasetLoaderError("override timeframe must be a non-empty string")

    dataset["timeframe"] = timeframe
    return load_dataset(dataset)