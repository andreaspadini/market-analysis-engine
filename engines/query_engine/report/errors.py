from __future__ import annotations


class ReportBuildError(Exception):
    """Raised when report building fails."""


class ReportNormalizationError(Exception):
    """Raised when query output cannot be normalized into canonical report shape."""


class ReportValidationError(Exception):
    """Raised when a normalized report violates the QRY-3 contract."""