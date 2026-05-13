from pydantic import BaseModel, ConfigDict, Field
from .pipeline_parameters_v1 import DatasetV1, RootEngineConfigV1

class RootRunParametersV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    api_version: str = Field(..., pattern=r"^1\.\d+$")
    dataset: DatasetV1
    config: RootEngineConfigV1