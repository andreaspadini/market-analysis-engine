from __future__ import annotations

from typing import Protocol, BinaryIO

from .dto_v1 import (
    ManifestGetResponse,
    QueryRunSubmitRequest,
    RootRunSubmitRequest,
    StatisticalRunSubmitRequest,
    RunGetResponse,
    RunNodesResponse,
    RunSubmitRequest,
    RunSubmitResponse,
)


class ApiServiceV1(Protocol):
    """
    O6 public facade v1.
    Anti-corruption layer: espone solo DTO v1 (no runtime internals).
    """

    def submit_root_run(self, request: RootRunSubmitRequest) -> RunSubmitResponse:
        ...

    def submit_statistical_run(
        self, request: StatisticalRunSubmitRequest
    ) -> RunSubmitResponse:
        ...

    def submit_query_run(self, request: QueryRunSubmitRequest) -> RunSubmitResponse:
        ...

    def submit_run(self, request: RunSubmitRequest) -> RunSubmitResponse:
        ...

    def get_run(self, run_id: str, *, api_version: str = "1.0") -> RunGetResponse:
        ...

    def list_nodes(self, run_id: str, *, api_version: str = "1.0") -> RunNodesResponse:
        ...

    def get_manifest(
        self, tool_id: str, fingerprint: str, *, api_version: str = "1.0"
    ) -> ManifestGetResponse:
        ...

    def open_artifact_output(
        self,
        tool_id: str,
        fingerprint: str,
        relpath: str,
        *,
        api_version: str = "1.0",
    ) -> BinaryIO:
        ...