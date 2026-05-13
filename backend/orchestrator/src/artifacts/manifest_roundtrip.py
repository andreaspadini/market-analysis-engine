from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict

from ..artifacts.manifest_validator import ManifestValidationError, validate_manifest


class ManifestMaterializationError(ValueError):
    """Raised when manifest outputs do not match created files."""


def compute_sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 64), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_outputs_match_files(base_dir: Path, manifest: Dict[str, Any]) -> None:
    """
    Checks that for each output:
      - file exists under base_dir/relpath
      - is a file (not a dir)
      - bytes match actual file size
      - checksum matches sha256 (v1 constraint)

    NOTE: This is not O3 storage logic. It only validates the relationship
    between a dummy artifact directory and its manifest.
    """
    if not isinstance(base_dir, Path):
        raise ManifestMaterializationError("base_dir must be a pathlib.Path")
    if not base_dir.exists():
        raise ManifestMaterializationError("base_dir must exist")

    # Structural validation first (pure, no FS), then FS consistency.
    try:
        validate_manifest(manifest, strict=True)
    except ManifestValidationError as e:
        raise ManifestMaterializationError(f"Manifest invalid: {e}") from e

    outputs = manifest["outputs"]
    for item in outputs:
        relpath = item["relpath"]
        expected_bytes = item["bytes"]
        expected_alg = item["checksum"]["alg"]
        expected_sum = item["checksum"]["value"]

        if expected_alg != "sha256":
            raise ManifestMaterializationError("Only sha256 is supported in v1.")

        p = base_dir / relpath
        if not p.exists():
            raise ManifestMaterializationError(f"Missing output file: {relpath}")
        if not p.is_file():
            raise ManifestMaterializationError(f"Output path is not a file: {relpath}")

        actual_bytes = p.stat().st_size
        if actual_bytes != expected_bytes:
            raise ManifestMaterializationError(
                f"Byte size mismatch for {relpath}: expected {expected_bytes}, got {actual_bytes}"
            )

        actual_sum = compute_sha256_hex(p)
        if actual_sum != expected_sum:
            raise ManifestMaterializationError(f"Checksum mismatch for {relpath}")
