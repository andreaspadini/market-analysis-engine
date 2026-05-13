from __future__ import annotations


class ExportEngineError(Exception):
    """Base error for export engine."""


class MixedInstrumentError(ExportEngineError):
    """Raised when matches/stats contain multiple instruments."""


class MixedTimeframeError(ExportEngineError):
    """Raised when matches/stats contain multiple timeframes."""


class EmptyDatasetError(ExportEngineError):
    """Raised when an export would produce an empty required dataset."""
