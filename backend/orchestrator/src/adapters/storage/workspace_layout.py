from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional


_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")  # freeze: lowercase-only


class StorageInvariantError(ValueError):
    pass


def validate_fingerprint_lower_hex(fingerprint: str) -> None:
    if not _FINGERPRINT_RE.match(fingerprint or ""):
        raise StorageInvariantError("Invalid fingerprint: expected 64 lowercase hex chars (sha256).")


def validate_tool_id(tool_id: str) -> None:
    if not tool_id or not tool_id.strip():
        raise StorageInvariantError("Invalid tool_id: must be non-empty.")
    # tool_id come path segment: restrizione minima, evita traversal/OS oddities
    if any(sep in tool_id for sep in ("/", "\\", os.sep)):
        raise StorageInvariantError("Invalid tool_id: must not contain path separators.")
    if tool_id in (".", ".."):
        raise StorageInvariantError("Invalid tool_id.")


def validate_relpath_safe(relpath: str) -> PurePosixPath:
    """
    O1: relpath relativo allo store root.
    Freeze #1: O3 NON impone che relpath rifletta layout.
    Qui facciamo solo safety: relativo, no '..', no assoluti.
    """
    try:
        p = PurePosixPath(relpath)
    except Exception as e:
        raise StorageInvariantError(f"Invalid relpath: {e}") from e

    if relpath is None or relpath == "":
        raise StorageInvariantError("Invalid relpath: empty.")
    if p.is_absolute():
        raise StorageInvariantError("Invalid relpath: must be relative to store root (not absolute).")
    if any(part in ("..", "") for part in p.parts):
        # "" può comparire in casi tipo "a//b" su alcune normalizzazioni: meglio rifiutare
        raise StorageInvariantError("Invalid relpath: must not contain '..' or empty path segments.")
    if str(p).startswith("./") or str(p) == ".":
        raise StorageInvariantError("Invalid relpath: must be a clean relative path, not '.' or './x'.")
    return p


def resolve_within_root(root: Path, rel: PurePosixPath) -> Path:
    """
    Converte relpath POSIX in path locale e garantisce che il resolved resti dentro root.
    """
    # Convertiamo PurePosixPath -> segments
    candidate = root.joinpath(*rel.parts)
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()

    try:
        resolved_candidate.relative_to(resolved_root)
    except Exception as e:
        raise StorageInvariantError("Path traversal detected: resolved path escapes store root.") from e

    return resolved_candidate


@dataclass(frozen=True)
class WorkspaceLayout:
    """
    Layout interno O3, non parte del contract O1.
    """
    store_root: Path

    def tools_root(self) -> Path:
        return self.store_root / "tools"

    def staging_root(self) -> Path:
        return self.store_root / ".staging"

    def artifact_dir(self, *, tool_id: str, fingerprint: str) -> Path:
        validate_tool_id(tool_id)
        validate_fingerprint_lower_hex(fingerprint)
        return self.tools_root() / tool_id / "fp" / fingerprint

    def manifest_path(self, *, tool_id: str, fingerprint: str) -> Path:
        return self.artifact_dir(tool_id=tool_id, fingerprint=fingerprint) / "manifest.json"

    def outputs_root(self, *, tool_id: str, fingerprint: str) -> Path:
        return self.artifact_dir(tool_id=tool_id, fingerprint=fingerprint) / "outputs"

    def ensure_base_dirs(self) -> None:
        self.store_root.mkdir(parents=True, exist_ok=True)
        self.tools_root().mkdir(parents=True, exist_ok=True)
        self.staging_root().mkdir(parents=True, exist_ok=True)
