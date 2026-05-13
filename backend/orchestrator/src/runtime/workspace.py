from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from adapters.storage.ports import WorkspacePort



@dataclass
class LocalWorkspace(WorkspacePort):
    """
    Lifecycle workspace (runtime): crea root e store root.
    Nessuna conoscenza di mapping artifact.
    """
    _workspace_root: Path

    def workspace_root(self) -> Path:
        return self._workspace_root

    def store_root(self) -> Path:
        return self._workspace_root / "store"

    def ensure_layout(self) -> None:
        self._workspace_root.mkdir(parents=True, exist_ok=True)
        self.store_root().mkdir(parents=True, exist_ok=True)
