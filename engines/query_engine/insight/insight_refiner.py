from __future__ import annotations

from typing import List

from .insight_types import InsightItem


def refine_insights(items: List[InsightItem]) -> List[InsightItem]:
    if not items:
        return items

    items = _deduplicate(items)
    items = _filter_noise(items)

    return items


def _same_target(left: InsightItem, right: InsightItem) -> bool:
    return left.dimension == right.dimension and left.value == right.value


def _same_target_any(item: InsightItem, candidates: list[InsightItem]) -> bool:
    return any(_same_target(item, candidate) for candidate in candidates)


# -------------------------
# Deduplication / noise reduction
# -------------------------
def _deduplicate(items: List[InsightItem]) -> List[InsightItem]:
    result: List[InsightItem] = []

    top_items = [i for i in items if i.type == "top_performer"]
    bottom_items = [i for i in items if i.type == "bottom_performer"]
    dominant_items = [i for i in items if i.type == "dominant_segment"]
    imbalanced_items = [i for i in items if i.type == "imbalanced_distribution"]

    semantic_winners = top_items + bottom_items + dominant_items + imbalanced_items

    for item in items:
        if item.type == "scalar":
            if _same_target_any(item, top_items):
                continue
            if _same_target_any(item, bottom_items):
                continue

        if item.type == "distribution":
            if _same_target_any(item, semantic_winners):
                continue

        if item.type == "top_performer":
            if _same_target_any(item, dominant_items):
                continue

        if item.type == "bottom_performer":
            if _same_target_any(item, imbalanced_items):
                continue

        result.append(item)

    return result


# -------------------------
# Noise filtering
# -------------------------
def _filter_noise(items: List[InsightItem]) -> List[InsightItem]:
    result: List[InsightItem] = []

    for item in items:
        if item.classification == "D":
            continue

        if item.type in {"top_gap", "range_gap"}:
            if isinstance(item.metric_value, (int, float)) and item.metric_value <= 0:
                continue

        result.append(item)

    return result