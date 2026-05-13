from __future__ import annotations

import mimetypes
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from ..service_v1 import ApiServiceV1
from ..api_impl_v1 import ApiErrorV1, ApiImplV1
from ..dto_v1 import (
    RootRunSubmitRequest,
    StatisticalRunSubmitRequest,
    QueryRunSubmitRequest,
    PatternRunSubmitRequest,
    RunSubmitRequest,
    RunSubmitResponse,
    RunGetResponse,
    RunNodesResponse,
    ManifestGetResponse,
)
from .dependencies import get_api_service_v1_root
from .dependencies import get_api_service_v1
from .dependencies import get_api_service_v1_statistical
from .dependencies import get_api_service_v1_query
from .dependencies import get_api_service_v1_pattern

router = APIRouter()


@router.post("/runs/root")
def post_root_run(
    payload: Dict[str, Any] = Body(...),
    svc: ApiServiceV1 = Depends(get_api_service_v1_root),
) -> JSONResponse:
    req = RootRunSubmitRequest.from_dict(payload)
    res: RunSubmitResponse = svc.submit_root_run(req)
    return JSONResponse(content=res.to_dict())


@router.post("/runs/statistical")
def post_statistical_run(
    payload: Dict[str, Any] = Body(...),
    svc: ApiServiceV1 = Depends(get_api_service_v1_statistical),
) -> JSONResponse:
    req = StatisticalRunSubmitRequest.from_dict(payload)
    res: RunSubmitResponse = svc.submit_statistical_run(req)
    return JSONResponse(content=res.to_dict())


@router.post("/runs")
def post_runs(
    payload: Dict[str, Any] = Body(...),
    svc: ApiServiceV1 = Depends(get_api_service_v1),
) -> JSONResponse:
    """
    Legacy full-pipeline compatibility endpoint.

    Executes the full pipeline:

        root -> statistical -> query

    Canonical stepwise endpoints:
    - POST /runs/root
    - POST /runs/statistical
    - POST /runs/query

    Notes:
    - /runs is not a stepwise endpoint
    - /runs does not accept stepwise payloads
    - /runs does not perform implicit artifact reuse
    - /runs remains available for backward compatibility only
    """
    req = RunSubmitRequest.from_dict(payload)
    res: RunSubmitResponse = svc.submit_run(req)
    return JSONResponse(content=res.to_dict())


@router.post("/runs/query")
def post_query_run(
    payload: Dict[str, Any] = Body(...),
    svc: ApiServiceV1 = Depends(get_api_service_v1_query),
) -> JSONResponse:
    req = QueryRunSubmitRequest.from_dict(payload)
    res: RunSubmitResponse = svc.submit_query_run(req)
    return JSONResponse(content=res.to_dict())


@router.get("/query/public-intents")
def get_query_public_intents() -> JSONResponse:
    from engines.query_engine.intent import list_public_intent_catalog

    example_by_intent = {
        "success_by_weekday_report": {
            "example_description": "Legacy weekday success report with no params.",
            "example_params": {},
        },
        "success_rate": {
            "example_description": "Deprecated compatibility success rate by session.",
            "example_params": {
                "group_by": ["session"],
            },
        },
        "true_breakout_rate": {
            "example_description": "Canonical true breakout rate by session.",
            "example_params": {
                "group_by": ["session"],
            },
        },
        "non_failed_rate": {
            "example_description": "Legacy non-failed rate by session.",
            "example_params": {
                "group_by": ["session"],
            },
        },
        "mean": {
            "example_description": "Mean max excursion by session.",
            "example_params": {
                "value_field": "max_excursion",
                "group_by": ["session"],
            },
        },

        "count": {
            "example_description": "Count events by session.",
            "example_params": {
                "group_by": ["session"],
            },
        },
        "median": {
            "example_description": "Median max excursion by session.",
            "example_params": {
                "value_field": "max_excursion",
                "group_by": ["session"],
            },
        },
        "std": {
            "example_description": "Standard deviation of max excursion by session.",
            "example_params": {
                "value_field": "max_excursion",
                "group_by": ["session"],
            },
        },
        "distribution": {
            "example_description": "Distribution of breakout outcomes.",
            "example_params": {
                "value_field": "breakout_outcome",
                "normalization": "none",
            },
        },
        "probability": {
            "example_description": "Probability of max excursion above threshold during NY session.",
            "example_params": {
                "event_predicate": {
                    "field": "max_excursion",
                    "operator": ">",
                    "value": 10,
                },
                "condition_predicate": {
                    "field": "session",
                    "operator": "==",
                    "value": "ny",
                },
            },
        },
        "ranking": {
            "example_description": "Rank sessions by canonical true breakout rate.",
            "example_params": {
                "group_by": ["session"],
                "score_metric": "true_breakout_rate",
                "target_field": "breakout_outcome",
                "success_condition": {
                    "operator": "==",
                    "value": "true_breakout",
                },
                "sort_direction": "desc",
            },
        },
    }

    items = []
    for item in list_public_intent_catalog():
        intent_id = item.get("intent_id")
        extra = example_by_intent.get(intent_id, {})
        items.append({**item, **extra})

    return JSONResponse(
        content={
            "api_version": "1.0",
            "items": items,
        }
    )
@router.post("/runs/pattern")
def post_pattern_run(
    payload: Dict[str, Any] = Body(...),
    svc = Depends(get_api_service_v1_pattern),
) -> JSONResponse:
    req = PatternRunSubmitRequest.from_dict(payload)  # type: ignore
    res: RunSubmitResponse = svc.submit_pattern_run(req)
    return JSONResponse(content=res.to_dict())

@router.get("/runs/{run_id}")
def get_run(
    run_id: str,
) -> JSONResponse:
    services = (
        get_api_service_v1_root(),
        get_api_service_v1_statistical(),
        get_api_service_v1_query(),
        get_api_service_v1_pattern(),
        get_api_service_v1(),
    )

    for svc in services:
        try:
            res: RunGetResponse = svc.get_run(run_id, api_version="1.0")
            return JSONResponse(content=res.to_dict())
        except Exception:
            continue

    return JSONResponse(
        status_code=404,
        content={
            "api_version": "1.0",
            "error": {
                "code": "not_found",
                "message": "run_id not found",
            },
        },
    )


@router.get("/runs/{run_id}/nodes")
def get_run_nodes(
    run_id: str,
) -> JSONResponse:
    services = (
        get_api_service_v1_root(),
        get_api_service_v1_statistical(),
        get_api_service_v1_query(),
        get_api_service_v1_pattern(),
        get_api_service_v1(),
    )

    for svc in services:
        try:
            res: RunNodesResponse = svc.list_nodes(run_id, api_version="1.0")
            return JSONResponse(content=res.to_dict())
        except Exception:
            continue

    return JSONResponse(
        status_code=404,
        content={
            "api_version": "1.0",
            "error": {
                "code": "not_found",
                "message": "run_id not found",
            },
        },
    )


@router.get("/manifests/{tool_id}/{fingerprint}")
def get_manifest(
    tool_id: str,
    fingerprint: str,
    svc: ApiServiceV1 = Depends(get_api_service_v1),
) -> JSONResponse:
    res: ManifestGetResponse = svc.get_manifest(tool_id, fingerprint, api_version="1.0")
    return JSONResponse(content=res.to_dict())


@router.get("/artifacts/{tool_id}/{fingerprint}/{relpath:path}")
def get_artifact_output(
    tool_id: str,
    fingerprint: str,
    relpath: str,
    svc: ApiServiceV1 = Depends(get_api_service_v1),
):
    fh = svc.open_artifact_output(
        tool_id=tool_id,
        fingerprint=fingerprint,
        relpath=relpath,
        api_version="1.0",
    )

    media_type, _ = mimetypes.guess_type(relpath)
    if not media_type:
        media_type = "application/octet-stream"

    filename = relpath.rsplit("/", 1)[-1]
    return StreamingResponse(
        fh,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )
