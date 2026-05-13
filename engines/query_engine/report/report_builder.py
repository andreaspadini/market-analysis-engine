from __future__ import annotations

from typing import Any, Mapping

from engines.query_engine.core.query_planner import ExecutionPlan

from .errors import ReportBuildError
from .report_normalizer import normalize_query_result
from .report_types import QueryReport, ReportMeta, ReportSummary
from .report_validator import validate_report


def build_report(
    plan: ExecutionPlan,
    query_result: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Build canonical QRY-3 report from an execution plan and QRY-1 output.
    """
    try:
        normalized = normalize_query_result(plan, query_result)

        report = QueryReport(
            meta=_build_meta(plan),
            summary=_build_summary(normalized),
            data=normalized["data"],
            ranking=normalized["ranking"],
        )

        report_dict = report.to_dict()
        validate_report(report_dict)
        return report_dict

    except Exception as exc:
        if isinstance(exc, ReportBuildError):
            raise
        raise ReportBuildError(str(exc)) from exc


def _build_meta(plan: ExecutionPlan) -> ReportMeta:
    return ReportMeta(
        metric=plan.metric,
        filters=plan.filters,
        group_by=plan.group_by,
        value_field=plan.value_field,
        target_field=plan.target_field,
        success_condition=plan.success_condition,
        event_predicate=plan.event_predicate,
        condition_predicate=plan.condition_predicate,
        normalization=plan.normalization,
        score_metric=plan.score_metric,
        sort_direction=plan.sort_direction,
        metadata=plan.metadata,
    )


def _build_summary(normalized: Mapping[str, Any]) -> ReportSummary:
    summary = normalized["summary"]

    return ReportSummary(
        rows_total=summary["rows_total"],
        rows_valid=summary["rows_valid"],
    )