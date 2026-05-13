from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .artifact_ref_v1 import ArtifactRefV1
from .pipeline_parameters_v1 import StatisticalConfigV1


class StatisticalRunParametersV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    api_version: str = Field(..., pattern=r"^1\.\d+$")
    root_artifact_ref: ArtifactRefV1
    config: StatisticalConfigV1