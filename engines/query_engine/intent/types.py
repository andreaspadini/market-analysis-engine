from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


Predicate = dict[str, Any]
Condition = dict[str, Any]


@dataclass(frozen=True)
class ParsedIntent:
    metric: str
    filters: list[Predicate] = field(default_factory=list)
    group_by: list[str] = field(default_factory=list)
    value_field: str | None = None
    target_field: str | None = None
    success_condition: Condition | None = None
    event_predicate: Predicate | None = None
    condition_predicate: Predicate | None = None
    normalization: str | None = None
    score_metric: str | None = None
    sort_direction: str | None = None


@dataclass(frozen=True)
class MappedIntent:
    metric: str
    filters: list[Predicate] = field(default_factory=list)
    group_by: list[str] = field(default_factory=list)
    value_field: str | None = None
    target_field: str | None = None
    success_condition: Condition | None = None
    event_predicate: Predicate | None = None
    condition_predicate: Predicate | None = None
    normalization: str | None = None
    score_metric: str | None = None
    sort_direction: str | None = None