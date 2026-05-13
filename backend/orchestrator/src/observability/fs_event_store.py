from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .events_v1 import EventEnvelopeV1


@dataclass(frozen=True)
class FsEventStore:
    root_dir: Path

    # lock globale (semplice e affidabile su Windows)
    _append_lock: threading.Lock = threading.Lock()

    def _path_for(self, run_id: str) -> Path:
        return self.root_dir / "runs" / run_id / "events.jsonl"

    def append(self, event: Dict[str, Any]) -> None:
        EventEnvelopeV1.validate_dict(event)

        path = self._path_for(event["run_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, separators=(",", ":"), ensure_ascii=False)

        # SERIALIZZA GLI APPEND: evita file sharing violations / partial writes in concorrenza
        with self._append_lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())

    def read_all(self, run_id: str) -> List[Dict[str, Any]]:
        path = self._path_for(run_id)
        if not path.exists():
            return []

        out: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                    EventEnvelopeV1.validate_dict(obj)
                    out.append(obj)
                except Exception:
                    continue

        out.sort(key=lambda e: e["seq"])
        return out
