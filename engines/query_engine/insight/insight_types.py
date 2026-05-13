from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class InsightMeta:
    source_metric: str
    derived_metric: str | None
    group_by: list[str]
    filters: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InsightSummary:
    rows_total: int
    rows_valid: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InsightSupport:
    rows_valid: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InsightItem:
    type: str
    dimension: str | None
    value: Any
    metric_value: Any
    support: InsightSupport
    classification: str
    flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["support"] = self.support.to_dict()
        return payload


@dataclass(frozen=True)
class InsightReport:
    meta: InsightMeta
    summary: InsightSummary
    insights: list[InsightItem]

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta.to_dict(),
            "summary": self.summary.to_dict(),
            "insights": [item.to_dict() for item in self.insights],
        }