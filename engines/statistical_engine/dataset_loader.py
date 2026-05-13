from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd


def load_root_dataset(root_dataset_path: Path) -> pd.DataFrame:
    """
    Load the full RootOutputDataset into memory.

    This is the canonical full-load helper used when the dataset size
    is compatible with in-memory processing.
    """
    root_dataset_path = Path(root_dataset_path).resolve()

    if not root_dataset_path.exists():
        raise FileNotFoundError(f"Root dataset not found: {root_dataset_path}")

    return pd.read_csv(root_dataset_path)


def iter_root_dataset_chunks(
    root_dataset_path: Path,
    *,
    chunksize: int = 10_000,
) -> Iterator[pd.DataFrame]:
    """
    Streaming/chunked reader for RootOutputDataset.

    This is required by EDI-3 contract to support large datasets.
    """
    root_dataset_path = Path(root_dataset_path).resolve()

    if not root_dataset_path.exists():
        raise FileNotFoundError(f"Root dataset not found: {root_dataset_path}")

    yield from pd.read_csv(root_dataset_path, chunksize=chunksize)