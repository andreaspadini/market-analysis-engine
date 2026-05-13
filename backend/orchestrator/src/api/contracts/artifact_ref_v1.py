from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ArtifactRefV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_id: str
    fingerprint: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    manifest_version: str | None = None
    producer_version: str | None = None