from __future__ import annotations

from typing import List, Optional
import pandas as pd


class DatasetLoaderError(Exception):
    """Raised when dataset loading or validation fails."""
    pass


def load_statistical_dataset(path: str) -> pd.DataFrame:
    """
    Load StatisticalDataset from parquet file.

    This function performs ONLY structural loading.
    No coercion, no transformation, no inference.
    """
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        raise DatasetLoaderError(f"Failed to load dataset from path: {path}") from e

    if df is None or df.empty:
        # Empty dataset is allowed, but must be a valid DataFrame
        return df

    return df


def validate_columns_exist(
    df: pd.DataFrame,
    required_columns: List[str]
) -> None:
    """
    Validate that required columns exist in dataset.

    Raises:
        DatasetLoaderError if any column is missing
    """
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise DatasetLoaderError(
            f"Missing required columns: {missing}"
        )


def is_numeric_series(series: pd.Series) -> bool:
    """
    Check if a pandas Series is numeric.

    No coercion is performed.
    """
    return pd.api.types.is_numeric_dtype(series)


def validate_numeric_column(
    df: pd.DataFrame,
    column: str
) -> None:
    """
    Validate that a column is numeric.

    Raises:
        DatasetLoaderError if column is not numeric
    """
    if column not in df.columns:
        raise DatasetLoaderError(f"Column not found: {column}")

    if not is_numeric_series(df[column]):
        raise DatasetLoaderError(
            f"Column '{column}' must be numeric, found dtype={df[column].dtype}"
        )


def validate_categorical_column(
    df: pd.DataFrame,
    column: str
) -> None:
    """
    Validate that a column is non-numeric (categorical-like).

    NOTE:
    This is a soft validation: we only ensure it's not numeric.
    """
    if column not in df.columns:
        raise DatasetLoaderError(f"Column not found: {column}")

    if is_numeric_series(df[column]):
        raise DatasetLoaderError(
            f"Column '{column}' expected categorical, found numeric dtype={df[column].dtype}"
        )