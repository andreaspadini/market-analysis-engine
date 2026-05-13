"""Type definitions for the O2 Config Schema v1.

The config layer is intentionally lightweight and does not depend on runtime/storage.
Types here are primarily for developer ergonomics; validation is enforced by
`config_validator`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping, Optional, TypedDict, Union


# JSON domain (strict) --------------------------------------------------------

JSONScalar = Union[str, int, float, bool, None]
JSONValue = Union[JSONScalar, "JSONObject", "JSONArray"]
JSONObject = Dict[str, JSONValue]
JSONArray = List[JSONValue]


# Config schema ----------------------------------------------------------------


class PipelineStep(TypedDict, total=False):
    step_id: str
    op: str
    with_: JSONObject  # NOTE: stored under key "with" in JSON; see validator.
    needs: List[str]


class Pipeline(TypedDict, total=False):
    id: str
    revision: str
    steps: List[Mapping[str, Any]]


class RunConfig(TypedDict, total=False):
    config_version: str
    pipeline: Mapping[str, Any]
    parameters: Mapping[str, Any]
    resources: Mapping[str, Any]
    metadata: Mapping[str, Any]
