from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .artifact_ref_v1 import ArtifactRefV1
from .pipeline_parameters_v1 import QueryEngineConfigV1


class QueryRunParametersV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    api_version: str = Field(..., pattern=r"^1\.\d+$")
    statistical_artifact_ref: ArtifactRefV1
    query: QueryEngineConfigV1