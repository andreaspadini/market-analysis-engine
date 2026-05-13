from __future__ import annotations

from typing import Iterable

from .insight_types import InsightItem


MAX_INSIGHTS = 7

TYPE_FACTOR = {
    "dominant_segment": 1.00,
    "top_gap": 0.95,
    "range_gap": 0.90,
    "imbalanced_distribution": 0.88,
    "top_performer": 0.82,
    "bottom_performer": 0.82,
    "probability": 0.80,
    "distribution": 0.76,
    "scalar": 0.72,
}

TYPE_PRIORITY = {
    "dominant_segment": 100,
    "imbalanced_distribution": 90,
    "top_performer": 80,
    "bottom_performer": 70,
    "top_gap": 60,
    "range_gap": 50,
    "probability": 40,
    "distribution": 30,
    "scalar": 20,
}


def score_insights(items: list[InsightItem]) -> list[InsightItem]:
    if not items:
        return items

    scored = [(item, _severity_score(item)) for item in items]
    scored = _prune_invalid(scored)
    scored = _prune_relative_tail(scored)
    scored = _sort(scored)
    scored = _limit(scored)

    return [item for item, _score in scored]


def _severity_score(item: InsightItem) -> float:
    base_signal = _base_signal(item)
    support_factor = _support_factor(item.support.rows_valid)
    classification_factor = _classification_factor(item.classification)
    type_factor = TYPE_FACTOR.get(item.type, 0.60)

    score = base_signal * support_factor * classification_factor * type_factor
    return _clamp01(score)


def _base_signal(item: InsightItem) -> float:
    value = item.metric_value

    if item.type in {"dominant_segment", "imbalanced_distribution", "probability", "distribution"}:
        return _ratio_signal(value)

    if item.type in {"top_gap", "range_gap"}:
        return _compressed_signal(value)

    if item.type in {"top_performer", "bottom_performer", "scalar"}:
        return _compressed_signal(value)

    return _compressed_signal(value)


def _ratio_signal(value: object) -> float:
    if not isinstance(value, (int, float)):
        return 0.0
    return _clamp01(abs(float(value)))


def _compressed_signal(value: object) -> float:
    if not isinstance(value, (int, float)):
        return 0.0

    x = abs(float(value))
    if x <= 0:
        return 0.0

    return x / (1.0 + x)


def _support_factor(rows_valid: int | None) -> float:
    if rows_valid is None or rows_valid <= 0:
        return 0.0

    return rows_valid / (rows_valid + 10.0)


def _classification_factor(classification: str) -> float:
    return {
        "A": 1.00,
        "B": 0.85,
        "C": 0.70,
        "D": 0.00,
    }.get(classification, 0.0)


def _prune_invalid(
    scored: Iterable[tuple[InsightItem, float]]
) -> list[tuple[InsightItem, float]]:
    result: list[tuple[InsightItem, float]] = []

    for item, score in scored:
        if item.classification == "D":
            continue
        if score <= 0:
            continue
        result.append((item, score))

    return result


def _prune_relative_tail(
    scored: list[tuple[InsightItem, float]]
) -> list[tuple[InsightItem, float]]:
    if not scored:
        return scored

    # Il pruning relativo serve solo quando c'è pressione sul limite finale.
    # Se gli insight sono già pochi, manteniamo l'ordinamento senza tagliare code deboli.
    if len(scored) <= MAX_INSIGHTS:
        return scored

    best_score = max(score for _, score in scored)
    if best_score <= 0:
        return []

    threshold = best_score * 0.35

    kept = [(item, score) for item, score in scored if score >= threshold]

    if not kept:
        best = max(scored, key=lambda pair: pair[1])
        return [best]

    return kept


def _sort(
    scored: list[tuple[InsightItem, float]]
) -> list[tuple[InsightItem, float]]:
    def sort_key(pair: tuple[InsightItem, float]) -> tuple:
        item, severity = pair
        type_priority = TYPE_PRIORITY.get(item.type, 0)

        numeric_magnitude = 0.0
        if isinstance(item.metric_value, (int, float)):
            numeric_magnitude = abs(float(item.metric_value))

        return (
            -severity,
            -type_priority,
            -numeric_magnitude,
            str(item.type),
            str(item.dimension),
            str(item.value),
        )

    return sorted(scored, key=sort_key)


def _limit(
    scored: list[tuple[InsightItem, float]]
) -> list[tuple[InsightItem, float]]:
    return scored[:MAX_INSIGHTS]


def _clamp01(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return value