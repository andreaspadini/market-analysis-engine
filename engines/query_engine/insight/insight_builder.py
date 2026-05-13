from __future__ import annotations

from typing import Any

from .insight_evaluator import evaluate_insight
from .insight_refiner import refine_insights
from .insight_rules import extract_base_insights, extract_advanced_insights
from .insight_scorer import score_insights
from .insight_types import (
    InsightItem,
    InsightMeta,
    InsightReport,
    InsightSummary,
    InsightSupport,
)
from .insight_validator import validate_insight_report


def build_insight(report: dict[str, Any]) -> dict[str, Any]:
    """
    Entry point QRY-5E / QRY-6A / QRY-6B / QRY-6C:
    report.json -> insight.json
    """

    base_insights = extract_base_insights(report)
    advanced_insights = extract_advanced_insights(report)
    all_insights = base_insights + advanced_insights

    insight_items: list[InsightItem] = []

    for raw in all_insights:
        classification, flags = evaluate_insight(raw)

        item = InsightItem(
            type=raw["type"],
            dimension=raw.get("dimension"),
            value=raw.get("value"),
            metric_value=raw.get("metric_value"),
            support=InsightSupport(rows_valid=raw.get("rows_valid")),
            classification=classification,
            flags=flags,
        )

        insight_items.append(item)

    insight_items = refine_insights(insight_items)
    insight_items = score_insights(insight_items)

    insight_report = InsightReport(
        meta=InsightMeta(
            source_metric=report["meta"]["metric"],
            derived_metric=None,
            group_by=report["meta"]["group_by"],
            filters=report["meta"]["filters"],
        ),
        summary=InsightSummary(
            rows_total=report["summary"]["rows_total"],
            rows_valid=report["summary"]["rows_valid"],
        ),
        insights=insight_items,
    )

    result = insight_report.to_dict()

    validate_insight_report(result)
    return result