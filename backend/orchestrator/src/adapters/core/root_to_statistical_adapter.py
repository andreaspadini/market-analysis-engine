from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .statistical_input_contract import (
    REQUIRED_COLUMNS_ORDERED,
    REQUIRED_NON_NULL_COLUMNS,
    OPTIONAL_PASSTHROUGH_COLUMNS,
    STATISTICAL_INPUT_SCHEMA_VERSION,
    StatisticalInputContractError,
    ordered_output_columns,
    validate_schema_version_values,
)

CSV_REQUIRED_SOURCE_COLUMNS: list[str] = [
    "schema_version",
    "breakout_id",
    "direction",
    "breakout_price",
    "balance_range_size",
    "initial_delta",
    "initial_volume",
    "atr_before",
    "follow_through",
    "is_failed",
]


def adapt_root_to_statistical(
    root_dataset_path: Path,
    adapted_dataset_path: Path,
) -> Path:
    """
    Deterministic, stateless adapter:
    Root dataset (JSON envelope or legacy CSV) -> StatisticalInputDataset
    """

    root_dataset_path = Path(root_dataset_path).resolve()
    adapted_dataset_path = Path(adapted_dataset_path).resolve()

    df = _load_root_dataset(root_dataset_path)

    df = _normalize_schema_version(df)

    df = _ensure_optional_contract_columns(df)

    df = _append_follow_through_columns(df)

    _validate_required_columns(df)
    _validate_non_null(df)
    _validate_schema_version(df)

    df = _order_columns(df)

    adapted_dataset_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(adapted_dataset_path, index=False)

    return adapted_dataset_path


def _load_root_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Root dataset not found: {path}")

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("Root dataset is empty")

    # 🔴 FIX: prova sempre JSON prima (robusto)
    try:
        payload = json.loads(raw)

        if isinstance(payload, dict) and "breakouts" in payload:
            breakouts = payload["breakouts"]

            if not isinstance(breakouts, list) or not breakouts:
                raise ValueError("Root dataset is empty or invalid")

            return pd.DataFrame(breakouts)

    except Exception:
        pass  # fallback CSV

    # fallback legacy CSV
    return _load_root_csv_legacy(path)


def _load_root_json_envelope(raw: str, path: Path) -> pd.DataFrame:
    try:
        payload = json.loads(raw)
    except Exception as e:
        raise ValueError(f"Invalid JSON root dataset: {path}") from e

    if not isinstance(payload, dict):
        raise ValueError("Root JSON dataset must be an object")

    breakouts = payload.get("breakouts")
    if not isinstance(breakouts, list):
        raise ValueError("Root JSON dataset missing 'breakouts' list")

    if not breakouts:
        raise ValueError("Root dataset is empty")

    df = pd.DataFrame(breakouts)
    return df


def _load_root_csv_legacy(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise ValueError(f"Invalid CSV root dataset: {path}") from e

    if df.empty:
        raise ValueError("Root dataset is empty")

    missing_required = [c for c in CSV_REQUIRED_SOURCE_COLUMNS if c not in df.columns]
    if missing_required:
        raise StatisticalInputContractError(
            f"Missing required source columns in root dataset: {missing_required}"
        )

    return df


def _parse_follow_through(v: Any) -> dict[str, Any] | None:
    if isinstance(v, dict):
        return v

    if pd.isna(v):
        return None

    if isinstance(v, str):
        text = v.strip()
        if not text:
            return None
        try:
            parsed = ast.literal_eval(text)
        except Exception:
            try:
                parsed = json.loads(text)
            except Exception as e:
                raise StatisticalInputContractError(
                    "Invalid follow_through payload: not parseable as dict"
                ) from e
        if parsed is None:
            return None
        if not isinstance(parsed, dict):
            raise StatisticalInputContractError(
                "Invalid follow_through payload: expected dict"
            )
        return parsed

    raise StatisticalInputContractError(
        f"Invalid follow_through payload type: {type(v).__name__}"
    )


def _append_follow_through_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "follow_through" not in df.columns:
        raise StatisticalInputContractError("Missing 'follow_through' column")

    parsed = df["follow_through"].apply(_parse_follow_through)

    df["max_excursion"] = parsed.apply(
        lambda d: d.get("max_excursion") if isinstance(d, dict) else None
    )
    df["retracement_depth"] = parsed.apply(
        lambda d: d.get("retracement_depth") if isinstance(d, dict) else None
    )
    df["time_to_retest_boundary"] = parsed.apply(
        lambda d: d.get("time_to_retest_boundary") if isinstance(d, dict) else None
    )

    return df


def _validate_required_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS_ORDERED if c not in df.columns]
    if missing:
        raise StatisticalInputContractError(f"Missing required columns: {missing}")


def _validate_non_null(df: pd.DataFrame) -> None:
    for col in REQUIRED_NON_NULL_COLUMNS:
        if df[col].isna().any():
            raise StatisticalInputContractError(
                f"Null values found in required column: {col}"
            )


def _validate_schema_version(df: pd.DataFrame) -> None:
    if "schema_version" not in df.columns:
        raise StatisticalInputContractError("Missing 'schema_version' column")

    validate_schema_version_values(df["schema_version"].tolist())


def _order_columns(df: pd.DataFrame) -> pd.DataFrame:
    ordered_cols = ordered_output_columns(list(df.columns))
    return df[ordered_cols]

def _normalize_schema_version(df: pd.DataFrame) -> pd.DataFrame:
    df["schema_version"] = STATISTICAL_INPUT_SCHEMA_VERSION
    return df

def _ensure_optional_contract_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in OPTIONAL_PASSTHROUGH_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df