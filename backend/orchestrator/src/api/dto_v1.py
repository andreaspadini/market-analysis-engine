from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple
from .contracts.artifact_ref_v1 import ArtifactRefV1
from .contracts.pattern_run_parameters_v1 import PatternRunParametersV1
from .contracts.pattern_run_parameters_v1 import PatternRunConfig


class DtoValidationError(ValueError):
    """Raised when a DTO fails strict validation (missing/extra fields, types, version)."""


def _parse_api_version_1x(api_version: Any) -> Tuple[int, int]:
    if not isinstance(api_version, str):
        raise DtoValidationError("api_version must be a string like '1.0'")
    parts = api_version.split(".")
    if len(parts) != 2:
        raise DtoValidationError("api_version must be in 'major.minor' format, e.g. '1.0'")
    try:
        major = int(parts[0])
        minor = int(parts[1])
    except ValueError as e:
        raise DtoValidationError("api_version major/minor must be integers") from e
    if major != 1:
        raise DtoValidationError("Only api_version 1.* is supported")
    if minor < 0:
        raise DtoValidationError("api_version minor must be >= 0")
    return major, minor


def _require_keys(d: Mapping[str, Any], required: List[str], allowed: List[str]) -> None:
    missing = [k for k in required if k not in d]
    if missing:
        raise DtoValidationError(f"Missing required fields: {missing}")
    extra = [k for k in d.keys() if k not in allowed]
    if extra:
        raise DtoValidationError(f"Unexpected extra fields: {extra}")


def _require_type(name: str, value: Any, typ: type) -> None:
    if not isinstance(value, typ):
        raise DtoValidationError(f"Field '{name}' must be {typ.__name__}")


def _optional_type(name: str, value: Any, typ: type) -> None:
    if value is None:
        return
    if not isinstance(value, typ):
        raise DtoValidationError(f"Field '{name}' must be {typ.__name__} or None")


# -------------------------
# Enums (stringly typed)
# -------------------------

# Keep them as strings to avoid leaking internal runtime models.
RunStatusV1 = str
NodeStatusV1 = str


# -------------------------
# DTOs
# -------------------------

@dataclass(frozen=True)
class RunSubmitRequest:
    api_version: str
    config: Dict[str, Any]

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "RunSubmitRequest":
        _require_keys(d, required=["api_version", "config"], allowed=["api_version", "config"])
        _parse_api_version_1x(d["api_version"])
        _require_type("config", d["config"], dict)
        return RunSubmitRequest(api_version=d["api_version"], config=dict(d["config"]))

    def to_dict(self) -> Dict[str, Any]:
        return {"api_version": self.api_version, "config": self.config}
    
@dataclass(frozen=True)
class RootRunSubmitRequest:
    api_version: str
    dataset: Dict[str, Any]
    config: Dict[str, Any]

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "RootRunSubmitRequest":
        _require_keys(
            d,
            required=["api_version", "dataset", "config"],
            allowed=["api_version", "dataset", "config"],
        )
        _parse_api_version_1x(d["api_version"])
        _require_type("dataset", d["dataset"], dict)
        _require_type("config", d["config"], dict)
        return RootRunSubmitRequest(
            api_version=d["api_version"],
            dataset=dict(d["dataset"]),
            config=dict(d["config"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_version": self.api_version,
            "dataset": self.dataset,
            "config": self.config,
        }
    
@dataclass(frozen=True)
class StatisticalRunSubmitRequest:
    api_version: str
    root_artifact_ref: ArtifactRefV1
    config: Dict[str, Any]

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "StatisticalRunSubmitRequest":
        _require_keys(
            d,
            required=["api_version", "root_artifact_ref", "config"],
            allowed=["api_version", "root_artifact_ref", "config"],
        )
        _parse_api_version_1x(d["api_version"])
        _require_type("root_artifact_ref", d["root_artifact_ref"], dict)
        _require_type("config", d["config"], dict)

        return StatisticalRunSubmitRequest(
            api_version=d["api_version"],
            root_artifact_ref=ArtifactRefV1.model_validate(d["root_artifact_ref"]),
            config=dict(d["config"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_version": self.api_version,
            "root_artifact_ref": self.root_artifact_ref.model_dump(exclude_none=True),
            "config": self.config,
        }

@dataclass(frozen=True)
class QueryRunSubmitRequest:
    api_version: str
    statistical_artifact_ref: ArtifactRefV1
    intent_id: str
    params: Dict[str, Any]

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "QueryRunSubmitRequest":
        _require_keys(
            d,
            required=["api_version", "statistical_artifact_ref", "intent_id", "params"],
            allowed=["api_version", "statistical_artifact_ref", "intent_id", "params"],
        )
        _parse_api_version_1x(d["api_version"])
        _require_type("statistical_artifact_ref", d["statistical_artifact_ref"], dict)
        _require_type("intent_id", d["intent_id"], str)
        _require_type("params", d["params"], dict)

        intent_id = d["intent_id"].strip()
        if not intent_id:
            raise DtoValidationError("Field 'intent_id' must be a non-empty string")

        return QueryRunSubmitRequest(
            api_version=d["api_version"],
            statistical_artifact_ref=ArtifactRefV1.model_validate(d["statistical_artifact_ref"]),
            intent_id=intent_id,
            params=dict(d["params"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_version": self.api_version,
            "statistical_artifact_ref": self.statistical_artifact_ref.model_dump(exclude_none=True),
            "intent_id": self.intent_id,
            "params": self.params,
        }

@dataclass(frozen=True)
class PatternRunSubmitRequest:
    api_version: str
    dataset: Dict[str, Any]
    config: PatternRunConfig

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "PatternRunSubmitRequest":
        _require_keys(
            d,
            required=["api_version", "dataset", "config"],
            allowed=["api_version", "dataset", "config"],
        )
        _parse_api_version_1x(d["api_version"])
        _require_type("dataset", d["dataset"], dict)
        _require_type("config", d["config"], dict)

        # strict contract validation
        PatternRunParametersV1.model_validate(d)

        validated = PatternRunParametersV1.model_validate(d)

        return PatternRunSubmitRequest(
            api_version=validated.api_version,
            dataset=validated.dataset.model_dump(),
            config=validated.config,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_version": self.api_version,
            "dataset": self.dataset,
            "config": (
                self.config.model_dump()
                if hasattr(self.config, "model_dump")
                else self.config
            ),
        }

@dataclass(frozen=True)
class SummaryV1:
    total_nodes: int
    pending: int
    running: int
    succeeded: int
    failed: int
    cached: int
    skipped: int

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "SummaryV1":
        allowed = ["total_nodes", "pending", "running", "succeeded", "failed", "cached", "skipped"]
        _require_keys(d, required=allowed, allowed=allowed)
        for k in allowed:
            _require_type(k, d[k], int)
            if d[k] < 0:
                raise DtoValidationError(f"Field '{k}' must be >= 0")
        return SummaryV1(**{k: int(d[k]) for k in allowed})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_nodes": self.total_nodes,
            "pending": self.pending,
            "running": self.running,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "cached": self.cached,
            "skipped": self.skipped,
        }


@dataclass(frozen=True)
class RunSubmitResponse:
    api_version: str
    run_id: str
    fingerprint: str
    status: RunStatusV1
    artifact: Optional[ArtifactRefV1] = None

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "RunSubmitResponse":
        _require_keys(
            d,
            required=["api_version", "run_id", "fingerprint", "status"],
            allowed=["api_version", "run_id", "fingerprint", "status", "artifact"],
        )
        _parse_api_version_1x(d["api_version"])
        _require_type("run_id", d["run_id"], str)
        _require_type("fingerprint", d["fingerprint"], str)
        _require_type("status", d["status"], str)

        artifact = None
        if "artifact" in d:
            _require_type("artifact", d["artifact"], dict)
            artifact = ArtifactRefV1.model_validate(d["artifact"])

        return RunSubmitResponse(
            api_version=d["api_version"],
            run_id=d["run_id"],
            fingerprint=d["fingerprint"],
            status=d["status"],
            artifact=artifact,
        )

    def to_dict(self) -> Dict[str, Any]:
        out = {
            "api_version": self.api_version,
            "run_id": self.run_id,
            "fingerprint": self.fingerprint,
            "status": self.status,
        }
        if self.artifact is not None:
            out["artifact"] = self.artifact.model_dump(exclude_none=True)
        return out


@dataclass(frozen=True)
class RunGetResponse:
    api_version: str
    run_id: str
    fingerprint: str
    status: RunStatusV1
    summary: SummaryV1

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "RunGetResponse":
        _require_keys(d, required=["api_version", "run_id", "fingerprint", "status", "summary"],
                      allowed=["api_version", "run_id", "fingerprint", "status", "summary"])
        _parse_api_version_1x(d["api_version"])
        _require_type("run_id", d["run_id"], str)
        _require_type("fingerprint", d["fingerprint"], str)
        _require_type("status", d["status"], str)
        _require_type("summary", d["summary"], dict)
        return RunGetResponse(
            api_version=d["api_version"],
            run_id=d["run_id"],
            fingerprint=d["fingerprint"],
            status=d["status"],
            summary=SummaryV1.from_dict(d["summary"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_version": self.api_version,
            "run_id": self.run_id,
            "fingerprint": self.fingerprint,
            "status": self.status,
            "summary": self.summary.to_dict(),
        }


@dataclass(frozen=True)
class NodeSummaryV1:
    # "astratto": niente node_id, niente lock model, niente execution plan internals
    name: str
    status: NodeStatusV1
    is_cached: bool
    is_skipped: bool
    error: Optional[Dict[str, Any]] = None  # optional public-ish error payload

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "NodeSummaryV1":
        allowed = ["name", "status", "is_cached", "is_skipped", "error"]
        _require_keys(d, required=["name", "status", "is_cached", "is_skipped"], allowed=allowed)
        _require_type("name", d["name"], str)
        _require_type("status", d["status"], str)
        _require_type("is_cached", d["is_cached"], bool)
        _require_type("is_skipped", d["is_skipped"], bool)
        if "error" in d:
            _optional_type("error", d["error"], dict)
        return NodeSummaryV1(
            name=d["name"],
            status=d["status"],
            is_cached=bool(d["is_cached"]),
            is_skipped=bool(d["is_skipped"]),
            error=d.get("error"),
        )

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "name": self.name,
            "status": self.status,
            "is_cached": self.is_cached,
            "is_skipped": self.is_skipped,
        }
        if self.error is not None:
            out["error"] = self.error
        return out


@dataclass(frozen=True)
class RunNodesResponse:
    api_version: str
    run_id: str
    fingerprint: str
    nodes: List[NodeSummaryV1]

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "RunNodesResponse":
        _require_keys(d, required=["api_version", "run_id", "fingerprint", "nodes"],
                      allowed=["api_version", "run_id", "fingerprint", "nodes"])
        _parse_api_version_1x(d["api_version"])
        _require_type("run_id", d["run_id"], str)
        _require_type("fingerprint", d["fingerprint"], str)
        _require_type("nodes", d["nodes"], list)
        nodes: List[NodeSummaryV1] = []
        for i, item in enumerate(d["nodes"]):
            if not isinstance(item, dict):
                raise DtoValidationError(f"nodes[{i}] must be an object")
            nodes.append(NodeSummaryV1.from_dict(item))
        return RunNodesResponse(
            api_version=d["api_version"],
            run_id=d["run_id"],
            fingerprint=d["fingerprint"],
            nodes=nodes,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_version": self.api_version,
            "run_id": self.run_id,
            "fingerprint": self.fingerprint,
            "nodes": [n.to_dict() for n in self.nodes],
        }


@dataclass(frozen=True)
class ManifestGetResponse:
    api_version: str
    tool_id: str
    fingerprint: str
    manifest: Dict[str, Any]

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "ManifestGetResponse":
        _require_keys(d, required=["api_version", "tool_id", "fingerprint", "manifest"],
                      allowed=["api_version", "tool_id", "fingerprint", "manifest"])
        _parse_api_version_1x(d["api_version"])
        _require_type("tool_id", d["tool_id"], str)
        _require_type("fingerprint", d["fingerprint"], str)
        _require_type("manifest", d["manifest"], dict)
        return ManifestGetResponse(
            api_version=d["api_version"],
            tool_id=d["tool_id"],
            fingerprint=d["fingerprint"],
            manifest=dict(d["manifest"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_version": self.api_version,
            "tool_id": self.tool_id,
            "fingerprint": self.fingerprint,
            "manifest": self.manifest,
        }
