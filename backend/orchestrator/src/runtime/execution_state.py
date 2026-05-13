"""ExecutionState: in-memory state container + transition enforcement.

Guardrails (frozen):
- Allowed transitions:
  * PENDING -> RUNNING
  * PENDING -> SKIPPED (ONLY for nodes in plan.cached)
  * RUNNING -> SUCCESS
  * RUNNING -> FAILED
  * RUNNING -> PENDING (ONLY for retry)

State is in-memory only for O5A (no persistence, no concurrency).
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, Iterable, Optional, Any

from .runtime_types import RuntimeRecord, Status


class InvalidTransitionError(RuntimeError):
    pass


class UnknownNodeError(KeyError):
    pass


class ExecutionState:
    """Holds runtime records for a single run."""

    def __init__(self, node_ids: Optional[Iterable[str]] = None):
        self._records: Dict[str, RuntimeRecord] = {}
        if node_ids is not None:
            for nid in node_ids:
                self._records[str(nid)] = RuntimeRecord(node_id=str(nid))

    def ensure_node(self, node_id: str) -> None:
        if node_id not in self._records:
            self._records[node_id] = RuntimeRecord(node_id=node_id)

    def get(self, node_id: str) -> RuntimeRecord:
        try:
            return self._records[node_id]
        except KeyError as e:
            raise UnknownNodeError(node_id) from e

    def all_records(self) -> Dict[str, RuntimeRecord]:
        # Return a shallow copy to avoid external mutation.
        return dict(self._records)

    def set_meta(self, node_id: str, meta: Dict[str, Any]) -> RuntimeRecord:
        """
        Runtime-only helper: aggiorna meta in modo deterministico (record è frozen).
        """
        self.ensure_node(node_id)
        rec = self._records[node_id]
        new_rec = replace(rec, meta=dict(meta))
        self._records[node_id] = new_rec
        return new_rec

    def set_artifact_ref(
        self,
        node_id: str,
        *,
        tool_id: str,
        fingerprint: str,
        status: str,
    ) -> RuntimeRecord:
        """
        Store minimal deterministic upstream artifact reference in RuntimeRecord.meta.
        """
        meta = dict(self.get(node_id).meta or {})
        meta["artifact_ref"] = {
            "tool_id": str(tool_id),
            "fingerprint": str(fingerprint),
            "status": str(status),
        }
        return self.set_meta(node_id, meta)

    def get_artifact_ref(self, node_id: str) -> Optional[Dict[str, str]]:
        meta = dict(self.get(node_id).meta or {})
        ref = meta.get("artifact_ref")
        if not isinstance(ref, dict):
            return None
        out: Dict[str, str] = {}
        for key in ("tool_id", "fingerprint", "status"):
            value = ref.get(key)
            if isinstance(value, str) and value:
                out[key] = value
        return out or None

    # --- transitions ---

    def mark_running(self, node_id: str) -> RuntimeRecord:
        return self._transition(node_id, Status.RUNNING)

    def mark_skipped_cached(self, node_id: str) -> RuntimeRecord:
        # PENDING -> SKIPPED only if explicitly marked as cached.
        return self._transition(node_id, Status.SKIPPED, cached=True)

    def mark_success(self, node_id: str) -> RuntimeRecord:
        return self._transition(node_id, Status.SUCCESS)

    def mark_failed(self, node_id: str) -> RuntimeRecord:
        return self._transition(node_id, Status.FAILED)

    def mark_pending_for_retry(self, node_id: str) -> RuntimeRecord:
        # RUNNING -> PENDING only for retry (attempt increment is applied).
        rec = self._transition(node_id, Status.PENDING, retry=True)
        rec2 = replace(rec, attempt=rec.attempt + 1)
        self._records[node_id] = rec2
        return rec2

    def _transition(
        self,
        node_id: str,
        to_status: Status,
        *,
        cached: bool = False,
        retry: bool = False,
    ) -> RuntimeRecord:
        self.ensure_node(node_id)
        rec = self._records[node_id]
        frm = rec.status

        allowed = False
        if frm == Status.PENDING and to_status == Status.RUNNING:
            allowed = True
        elif frm == Status.PENDING and to_status == Status.SKIPPED:
            allowed = cached
        elif frm == Status.RUNNING and to_status in (Status.SUCCESS, Status.FAILED):
            allowed = True
        elif frm == Status.RUNNING and to_status == Status.PENDING:
            allowed = retry

        if not allowed:
            why = ""
            if frm == Status.PENDING and to_status == Status.SKIPPED and not cached:
                why = " (SKIPPED allowed only for cached nodes)"
            if frm == Status.RUNNING and to_status == Status.PENDING and not retry:
                why = " (RUNNING->PENDING allowed only for retry)"
            raise InvalidTransitionError(f"Invalid transition {frm.value} -> {to_status.value} for {node_id}{why}")

        new_rec = replace(rec, status=to_status)
        self._records[node_id] = new_rec
        return new_rec