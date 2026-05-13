from dataclasses import dataclass
from typing import Any, Mapping, Tuple


@dataclass(frozen=True)
class DatasetSelection:
    """
    Dataset selection coming directly from configuration (O2 layer).

    Pure declarative DTO.
    No runtime semantics.
    """

    instruments: Tuple[str, ...]
    timeframe: str
    start_date: str
    end_date: str


@dataclass(frozen=True)
class DatasetResolved:
    """
    DTO produced by the Dataset Resolver (D2).

    Represents a canonicalized dataset selection with a deterministic
    logical dataset identifier.
    """

    instruments: Tuple[str, ...]
    timeframe: str
    start_date: str
    end_date: str
    dataset_id: str


@dataclass(frozen=True)
class DatasetInputView:
    """
    Canonical input view used for compute_input_hash.

    This structure is serialized to strict canonical JSON before hashing.

    Construction logic is implemented later (D3).
    """

    tool_id: str
    inputs: Mapping[str, Any]
    parameters: Mapping[str, Any]