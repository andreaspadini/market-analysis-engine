from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, Protocol, Sequence, Tuple, Mapping, Any


# O1 Manifest: O3 non reinterpreta, lo tratta come dato strutturato.
# Manteniamo tipo generico, ma portiamo vincoli nel runtime/store.
Manifest = Mapping[str, Any]


@dataclass(frozen=True)
class OutputItem:
    """
    Un singolo file da materializzare dentro artifact_dir/outputs.
    - logical_name: chiave stabile per riconciliare con manifest.outputs (se presente)
    - filename: relativo (POSIX-like) sotto outputs/ (non relpath O1)
    - data: bytes del contenuto
    """
    logical_name: str
    filename: str
    data: bytes


class ArtifactPayload(Protocol):
    """
    Payload generico: O3 non interpreta il contenuto, ma materializza file/bytes.
    """
    def iter_outputs(self) -> Iterable[OutputItem]:
        ...


class ArtifactStorePort(Protocol):
    """
    Port interno: nessun dettaglio filesystem esposto.
    Chiave primaria congelata: (tool_id, fingerprint).
    """

    def put_artifact(self, *, tool_id: str, fingerprint: str, payload: ArtifactPayload, manifest: Manifest) -> None:
        ...

    def exists(self, *, tool_id: str, fingerprint: str) -> bool:
        ...

    def get_manifest(self, *, tool_id: str, fingerprint: str) -> Manifest:
        ...

    def open_output(self, *, tool_id: str, fingerprint: str, relpath: str) -> BinaryIO:
        ...

    def list_artifacts(self, *, tool_id: str) -> Sequence[str]:
        ...


class WorkspacePort(Protocol):
    """
    Runtime-only lifecycle: crea/risolve root e layout base.
    Non espone mapping artifact.
    """

    def workspace_root(self) -> Path:
        ...

    def store_root(self) -> Path:
        ...

    def ensure_layout(self) -> None:
        ...
