from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, Union


EVENT_VERSION: Literal["1.0"] = "1.0"

# --- Event payload types (strict-by-type) ---

@dataclass(frozen=True)
class RunSubmittedPayload:
    pipeline: str
    config_fingerprint: str


@dataclass(frozen=True)
class RunStartedPayload:
    pass


@dataclass(frozen=True)
class RunSucceededPayload:
    pass


@dataclass(frozen=True)
class RunFailedPayload:
    error_type: str
    error_message: str


@dataclass(frozen=True)
class NodeStartedPayload:
    node_id: str


@dataclass(frozen=True)
class NodeSucceededPayload:
    node_id: str


@dataclass(frozen=True)
class NodeFailedPayload:
    node_id: str
    error_type: str
    error_message: str


@dataclass(frozen=True)
class NodeSkippedPayload:
    node_id: str
    reason: str


EventType = Literal[
    "RunSubmitted",
    "RunStarted",
    "NodeStarted",
    "NodeSucceeded",
    "NodeFailed",
    "NodeSkipped",
    "RunSucceeded",
    "RunFailed",
]

EventPayload = Union[
    RunSubmittedPayload,
    RunStartedPayload,
    NodeStartedPayload,
    NodeSucceededPayload,
    NodeFailedPayload,
    NodeSkippedPayload,
    RunSucceededPayload,
    RunFailedPayload,
]


_TYPE_TO_PAYLOAD = {
    "RunSubmitted": RunSubmittedPayload,
    "RunStarted": RunStartedPayload,
    "NodeStarted": NodeStartedPayload,
    "NodeSucceeded": NodeSucceededPayload,
    "NodeFailed": NodeFailedPayload,
    "NodeSkipped": NodeSkippedPayload,
    "RunSucceeded": RunSucceededPayload,
    "RunFailed": RunFailedPayload,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class EventEnvelopeV1:
    """
    O7 event envelope (pure observability).

    Guardrail: ts is informative only.
    """
    event_version: Literal["1.0"]
    run_id: str
    seq: int
    type: EventType
    payload: Dict[str, Any]
    ts: Optional[str] = None

    @staticmethod
    def new(*, run_id: str, seq: int, type: EventType, payload: EventPayload, ts: Optional[str] = None) -> "EventEnvelopeV1":
        if not isinstance(seq, int) or seq < 1:
            raise ValueError("seq must be int >= 1")
        if not run_id or not isinstance(run_id, str):
            raise ValueError("run_id must be non-empty str")
        if type not in _TYPE_TO_PAYLOAD:
            raise ValueError(f"Unknown event type: {type}")

        expected = _TYPE_TO_PAYLOAD[type]
        if not isinstance(payload, expected):
            raise TypeError(f"Payload for type={type} must be {expected.__name__}")

        return EventEnvelopeV1(
            event_version=EVENT_VERSION,
            run_id=run_id,
            seq=seq,
            type=type,
            payload=payload.__dict__.copy(),
            ts=ts if ts is not None else _now_iso(),
        )

    @staticmethod
    def validate_dict(d: Dict[str, Any]) -> None:
        """
        Strict validator for decoded JSON object (from JSONL).
        Raises ValueError/TypeError if invalid.
        """
        if not isinstance(d, dict):
            raise TypeError("event must be a dict")
        if d.get("event_version") != EVENT_VERSION:
            raise ValueError("event_version must be '1.0'")
        for k in ("run_id", "seq", "type", "payload"):
            if k not in d:
                raise ValueError(f"missing field: {k}")

        if not isinstance(d["run_id"], str) or not d["run_id"]:
            raise TypeError("run_id must be non-empty str")
        if not isinstance(d["seq"], int) or d["seq"] < 1:
            raise TypeError("seq must be int >= 1")
        if d["type"] not in _TYPE_TO_PAYLOAD:
            raise ValueError(f"Unknown event type: {d['type']}")
        if not isinstance(d["payload"], dict):
            raise TypeError("payload must be dict")

        # Strict payload schema by type: keys must match dataclass fields exactly.
        payload_cls = _TYPE_TO_PAYLOAD[d["type"]]
        expected_keys = set(payload_cls.__dataclass_fields__.keys())
        actual_keys = set(d["payload"].keys())
        if expected_keys != actual_keys:
            raise ValueError(f"payload keys mismatch for {d['type']}: expected {sorted(expected_keys)}, got {sorted(actual_keys)}")

        # Type checks for payload fields (basic)
        for fname, fdef in payload_cls.__dataclass_fields__.items():
            val = d["payload"].get(fname)
            # Accept None only if Optional, here we have none Optional in payloads.
            ann = fdef.type
            if ann is str and not isinstance(val, str):
                raise TypeError(f"payload.{fname} must be str")
            if ann is int and not isinstance(val, int):
                raise TypeError(f"payload.{fname} must be int")

        # ts informative only; if present must be str
        if "ts" in d and d["ts"] is not None and not isinstance(d["ts"], str):
            raise TypeError("ts must be str or null")
