from typing import Tuple
from datetime import datetime
import re

from .dataset_schema import DatasetSelection, DatasetResolved


_CANONICAL_TIMEFRAMES = {
    "1m",
    "5m",
    "15m",
    "1h",
    "1d",
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _canonicalize_instruments(values: Tuple[str, ...]) -> Tuple[str, ...]:
    cleaned = []

    for v in values:
        v = v.strip()
        if not v:
            continue
        v = v.upper()
        cleaned.append(v)

    unique = sorted(set(cleaned))

    if not unique:
        raise ValueError("Dataset must contain at least one instrument")

    return tuple(unique)


def _validate_timeframe(tf: str) -> str:
    tf = tf.strip().lower()

    if tf not in _CANONICAL_TIMEFRAMES:
        raise ValueError(f"Invalid timeframe: {tf}")

    return tf


def _validate_date(date_str: str) -> str:
    if not _DATE_RE.match(date_str):
        raise ValueError(f"Invalid date format: {date_str}")

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date value: {date_str}")

    return date_str


def _validate_date_range(start: str, end: str) -> None:
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")

    if start_dt > end_dt:
        raise ValueError("start_date must be <= end_date")


def _build_dataset_id(
    instruments: Tuple[str, ...],
    timeframe: str,
    start_date: str,
    end_date: str,
) -> str:
    instruments_part = "-".join(i.lower() for i in instruments)

    return f"{instruments_part}_{timeframe}_{start_date}_{end_date}"


def resolve_dataset(selection: DatasetSelection) -> DatasetResolved:
    """
    Resolve DatasetSelection into a canonical DatasetResolved.

    Applies deterministic canonicalization and validation.
    """

    instruments = _canonicalize_instruments(selection.instruments)

    timeframe = _validate_timeframe(selection.timeframe)

    start_date = _validate_date(selection.start_date)
    end_date = _validate_date(selection.end_date)

    _validate_date_range(start_date, end_date)

    dataset_id = _build_dataset_id(
        instruments,
        timeframe,
        start_date,
        end_date,
    )

    return DatasetResolved(
        instruments=instruments,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        dataset_id=dataset_id,
    )