from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ErrorCodeV1(str, Enum):
    INVALID_CONFIG = "INVALID_CONFIG"
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_VERSION = "INVALID_VERSION"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_ARTIFACT_REF = "INVALID_ARTIFACT_REF"
    INVALID_INTENT = "INVALID_INTENT"


@dataclass(frozen=True)
class ErrorEnvelopeV1:
    api_version: str
    error_code: ErrorCodeV1
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "api_version": self.api_version,
            "error_code": self.error_code.value,
            "message": self.message,
        }
        if self.details is not None:
            out["details"] = self.details
        return out


def invalid_config(api_version: str, message: str = "Invalid config", *, details: Optional[Dict[str, Any]] = None) -> ErrorEnvelopeV1:
    return ErrorEnvelopeV1(api_version=api_version, error_code=ErrorCodeV1.INVALID_CONFIG, message=message, details=details)

def invalid_artifact_ref(api_version: str, message: str = "Invalid artifact ref", *, details: Optional[Dict[str, Any]] = None) -> ErrorEnvelopeV1:
    return ErrorEnvelopeV1(api_version=api_version, error_code=ErrorCodeV1.INVALID_ARTIFACT_REF, message=message, details=details)


def invalid_intent(api_version: str, message: str = "Invalid intent", *, details: Optional[Dict[str, Any]] = None) -> ErrorEnvelopeV1:
    return ErrorEnvelopeV1(api_version=api_version, error_code=ErrorCodeV1.INVALID_INTENT, message=message, details=details)


def invalid_request(api_version: str, message: str = "Invalid request", *, details: Optional[Dict[str, Any]] = None) -> ErrorEnvelopeV1:
    return ErrorEnvelopeV1(api_version=api_version, error_code=ErrorCodeV1.INVALID_REQUEST, message=message, details=details)


def invalid_version(api_version: str, message: str = "Invalid API version", *, details: Optional[Dict[str, Any]] = None) -> ErrorEnvelopeV1:
    return ErrorEnvelopeV1(api_version=api_version, error_code=ErrorCodeV1.INVALID_VERSION, message=message, details=details)


def not_found(api_version: str, message: str = "Not found", *, details: Optional[Dict[str, Any]] = None) -> ErrorEnvelopeV1:
    return ErrorEnvelopeV1(api_version=api_version, error_code=ErrorCodeV1.NOT_FOUND, message=message, details=details)


def internal_error(api_version: str, message: str = "Internal error", *, details: Optional[Dict[str, Any]] = None) -> ErrorEnvelopeV1:
    return ErrorEnvelopeV1(api_version=api_version, error_code=ErrorCodeV1.INTERNAL_ERROR, message=message, details=details)
