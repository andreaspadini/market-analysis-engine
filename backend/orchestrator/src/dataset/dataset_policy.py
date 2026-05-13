from typing import Final

from .dataset_schema import DatasetSelection


ALLOWED_INSTRUMENTS: Final[frozenset[str]] = frozenset(
    {
        "MNQ",
        "MES",
        "NQ",
        "ES",
    }
)

ALLOWED_TIMEFRAMES: Final[frozenset[str]] = frozenset(
    {
        "1m",
        "5m",
        "15m",
        "1h",
        "1d",
    }
)


class DatasetPolicyError(ValueError):
    """
    Raised when DatasetSelection violates Dataset Layer policy.
    """


def validate_dataset_selection(selection: DatasetSelection) -> None:
    """
    Validate DatasetSelection against Dataset Layer declarative policy.

    This function is intentionally strict and fail-fast.
    It enforces only domain/policy guardrails and does not perform:
    - canonicalization
    - dataset resolution
    - runtime availability checks
    - filesystem access
    """

    if not selection.instruments:
        raise DatasetPolicyError(
            "DatasetSelection requires at least one instrument."
        )

    for instrument in selection.instruments:
        if instrument == "":
            raise DatasetPolicyError(
                "DatasetSelection instruments cannot contain empty strings."
            )

        if instrument not in ALLOWED_INSTRUMENTS:
            raise DatasetPolicyError(
                f"DatasetSelection contains unsupported instrument: {instrument!r}."
            )

    if selection.timeframe == "":
        raise DatasetPolicyError(
            "DatasetSelection timeframe cannot be empty."
        )

    if selection.timeframe not in ALLOWED_TIMEFRAMES:
        raise DatasetPolicyError(
            f"DatasetSelection contains unsupported timeframe: {selection.timeframe!r}."
        )

    if selection.start_date == "":
        raise DatasetPolicyError(
            "DatasetSelection start_date cannot be empty."
        )

    if selection.end_date == "":
        raise DatasetPolicyError(
            "DatasetSelection end_date cannot be empty."
        )