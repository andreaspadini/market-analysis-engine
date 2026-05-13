from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ReportMeta:
    metric: str
    filters: list[dict[str, Any]]
    group_by: list[str]
    value_field: str | None = None
    target_field: str | None = None
    success_condition: dict[str, Any] | None = None
    event_predicate: dict[str, Any] | None = None
    condition_predicate: dict[str, Any] | None = None
    normalization: str | None = None
    score_metric: str | None = None
    sort_direction: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReportSummary:
    rows_total: int
    rows_valid: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReportRow:
    group_key: dict[str, Any]
    rows_total: int
    rows_valid: int
    result: Any
    condition_count: int | None = None
    event_and_condition_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "group_key": self.group_key,
            "rows_total": self.rows_total,
            "rows_valid": self.rows_valid,
            "result": self.result,
        }

        if self.condition_count is not None:
            payload["condition_count"] = self.condition_count

        if self.event_and_condition_count is not None:
            payload["event_and_condition_count"] = self.event_and_condition_count

        return payload


@dataclass(frozen=True)
class ReportRankingRow:
    rank: int
    group_key: dict[str, Any]
    score: int | float
    rows_valid: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QueryReport:
    meta: ReportMeta
    summary: ReportSummary
    data: list[ReportRow] | None
    ranking: list[ReportRankingRow] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta.to_dict(),
            "summary": self.summary.to_dict(),
            "data": None if self.data is None else [row.to_dict() for row in self.data],
            "ranking": None if self.ranking is None else [row.to_dict() for row in self.ranking],
        }