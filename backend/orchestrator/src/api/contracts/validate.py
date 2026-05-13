from __future__ import annotations

from typing import Any, Dict
from .pattern_run_parameters_v1 import PatternRunParametersV1
from .pipeline_parameters_v1 import PipelineParametersV1
from .query_run_parameters_v1 import QueryRunParametersV1
from .root_run_parameters_v1 import RootRunParametersV1
from .statistical_run_parameters_v1 import StatisticalRunParametersV1
from engines.query_engine.intent import validate_public_intent
from engines.query_engine.intent.errors import IntentValidationError



class PipelineParametersValidationError(ValueError):
    pass

class PublicIntentValidationError(PipelineParametersValidationError):
    pass


def validate_root_run_parameters_v1(payload: Dict[str, Any]) -> RootRunParametersV1:
    return RootRunParametersV1.model_validate(payload)


def validate_statistical_run_parameters_v1(
    payload: Dict[str, Any],
) -> StatisticalRunParametersV1:
    return StatisticalRunParametersV1.model_validate(payload)


def validate_query_run_parameters_v1(payload: Dict[str, Any]) -> QueryRunParametersV1:
    model = QueryRunParametersV1.model_validate(payload)

    q = model.query
    try:
        validate_public_intent(q.intent_id, q.params)
    except IntentValidationError as exc:
        raise PublicIntentValidationError(str(exc)) from exc

    return model

def validate_pattern_run_parameters_v1(payload: Dict[str, Any]) -> PatternRunParametersV1:
    return PatternRunParametersV1.model_validate(payload)


def validate_pipeline_parameters_v1(
    payload: Dict[str, Any],
    intents_json_path=None,
) -> PipelineParametersV1:
    """
    Strict validator:
    1) Pydantic strict on DTO (extra forbid, types)
    2) Query strict validation against QRY-2 public intent registry
    """
    model = PipelineParametersV1.model_validate(payload)

    q = model.engines.query
    try:
        validate_public_intent(q.intent_id, q.params)
    except IntentValidationError as exc:
        raise PublicIntentValidationError(str(exc)) from exc

    return model