from __future__ import annotations
from ...artifacts.manifest_validator import validate_manifest
import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable, Mapping, Any, Sequence, List, Dict

from .ports import ArtifactStorePort, ArtifactPayload, Manifest, OutputItem
from .workspace_layout import (
    StorageInvariantError,
    WorkspaceLayout,
    validate_fingerprint_lower_hex,
    validate_relpath_safe,
    validate_tool_id,
    resolve_within_root,
)

# Freeze #4: O3 deve usare serializer canonico O1 (unico).
# IMPORTA il modulo di O1 (da adattare al path reale nel repo orchestrator).
# Questo file NON deve reimplementare canonical JSON.
from ...artifacts.manifest_json import (
    dump_manifest_json_bytes,
    load_manifest_json_bytes,
    assert_canonical_json_bytes,
)



class ArtifactNotFoundError(FileNotFoundError):
    pass


def _sha256_hex(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()  # lower-hex


def _fsync_dir_best_effort(dir_path: Path) -> None:
    try:
        fd = os.open(str(dir_path), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except Exception:
        # best-effort
        return


def _atomic_replace_dir(src: Path, dst: Path) -> None:
    """
    Rename atomico directory -> directory (stesso filesystem).
    """
    os.replace(str(src), str(dst))


def _write_bytes_atomic(file_path: Path, data: bytes) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = file_path.with_name(file_path.name + f".tmp.{uuid.uuid4().hex}")
    with open(tmp, "wb") as f:
        f.write(data)
        try:
            f.flush()
            os.fsync(f.fileno())
        except Exception:
            pass
    os.replace(str(tmp), str(file_path))
    _fsync_dir_best_effort(file_path.parent)


def _read_manifest(path: Path) -> Mapping[str, Any]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as e:
        raise ArtifactNotFoundError(str(path)) from e

    # opzionale ma utile: garantisce che ciò che leggiamo è in forma canonica O1
    try:
        assert_canonical_json_bytes(raw)
    except Exception as e:
        raise StorageInvariantError(f"Invalid manifest.json (non-canonical): {e}") from e

    try:
        return load_manifest_json_bytes(raw)
    except Exception as e:
        raise StorageInvariantError(f"Invalid manifest.json (cannot parse): {e}") from e


def _write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    raw: bytes = dump_manifest_json_bytes(dict(manifest))
    _write_bytes_atomic(path, raw)



@dataclass
class FilesystemArtifactStore(ArtifactStorePort):
    store_root: Path

    def __post_init__(self) -> None:
        self._layout = WorkspaceLayout(self.store_root)
        self._layout.ensure_base_dirs()

    # ----------------------------
    # ArtifactStorePort
    # ----------------------------
    def put_artifact(self, *, tool_id: str, fingerprint: str, payload: ArtifactPayload, manifest: Manifest) -> None:
        validate_tool_id(tool_id)
        validate_fingerprint_lower_hex(fingerprint)

        final_dir = self._layout.artifact_dir(tool_id=tool_id, fingerprint=fingerprint)
        final_manifest_path = self._layout.manifest_path(tool_id=tool_id, fingerprint=fingerprint)

        # Idempotenza: se già esiste manifest valido, riusa
        if final_manifest_path.exists():
            _ = _read_manifest(final_manifest_path)  # validate parse
            return

        # --- O1 strict: il manifest è contract, NON va riscritto dallo store ---
        m: Dict[str, Any] = dict(manifest)  # shallow copy

        # producer.tool_id deve corrispondere al tool richiesto (coerenza store)
        producer = dict(m.get("producer") or {})
        producer["tool_id"] = tool_id
        m["producer"] = producer

        # Validazione O1 strict (bytes obbligatorio per ogni output)
        validate_manifest(dict(m), strict=True)

        outputs = m.get("outputs") or []
        if not isinstance(outputs, list) or not outputs:
            raise StorageInvariantError("Manifest invariant: outputs[] must be non-empty (O1).")

        # staging
        staging_dir = self._layout.staging_root() / tool_id / fingerprint / uuid.uuid4().hex
        staging_artifact_dir = staging_dir / "artifact"
        staging_manifest_path = staging_artifact_dir / "manifest.json"
        staging_outputs_root = staging_artifact_dir / "outputs"
        staging_outputs_root.mkdir(parents=True, exist_ok=True)

        try:
            # Materializza outputs seguendo il MANIFEST (relpath deve essere outputs/<...>)
            payload_items = list(payload.iter_outputs())
            by_filename: Dict[str, Any] = {}
            for it in payload_items:
                fn = str(PurePosixPath(it.filename))
                by_filename[fn] = it

            for i, out in enumerate(outputs):
                if not isinstance(out, dict):
                    raise StorageInvariantError(f"Manifest outputs[{i}] must be an object.")

                rel = out.get("relpath")
                if not isinstance(rel, str) or not rel:
                    raise StorageInvariantError(f"Manifest outputs[{i}].relpath must be non-empty str.")

                rp = PurePosixPath(rel)

                # O1: nel tuo sistema il relpath contract è relativo all'artifact root (es: outputs/result.json)
                if rp.is_absolute() or any(part in ("..", "", ".") for part in rp.parts):
                    raise StorageInvariantError(f"Manifest outputs[{i}].relpath must be a clean relative path: {rel}")

                if not rp.parts or rp.parts[0] != "outputs":
                    raise StorageInvariantError(
                        f"Manifest outputs[{i}].relpath must start with 'outputs/': {rel}"
                    )

                # File path effettivo nello staging
                out_path = staging_artifact_dir.joinpath(*rp.parts)
                out_path.parent.mkdir(parents=True, exist_ok=True)

                # Determina quale OutputItem scrivere:
                # - se filename coincide con basename (es. result.json), ok
                # - altrimenti prova match completo su 'outputs/<filename>' o 'filename'
                #   (per compat con payload che dà filename senza prefisso outputs/)
                wanted_filename = rp.name
                item = by_filename.get(wanted_filename) or by_filename.get(str(rp)) or by_filename.get(str(rp.relative_to("outputs")))

                if item is None:
                    raise StorageInvariantError(
                        f"Payload missing OutputItem for manifest outputs[{i}] relpath={rel} (expected filename={wanted_filename})."
                    )

                out_path.write_bytes(item.data)

                # Checksum/bytes: lo store NON li inventa nel manifest,
                # ma può verificare coerenza se presenti (strict li richiede)
                declared_bytes = out.get("bytes")
                if isinstance(declared_bytes, int) and declared_bytes != len(item.data):
                    raise StorageInvariantError(
                        f"Manifest outputs[{i}].bytes mismatch for {rel}: declared={declared_bytes} actual={len(item.data)}"
                    )

                chk = out.get("checksum") or {}
                if isinstance(chk, dict) and chk.get("alg") == "sha256" and isinstance(chk.get("value"), str):
                    actual = _sha256_hex(item.data)
                    if actual != chk["value"]:
                        raise StorageInvariantError(
                            f"Manifest outputs[{i}].checksum mismatch for {rel}: declared={chk['value']} actual={actual}"
                        )

            # Scrive manifest in staging (AS-IS)
            _write_manifest(staging_manifest_path, m)

            # fsync dirs best-effort
            _fsync_dir_best_effort(staging_outputs_root)
            _fsync_dir_best_effort(staging_artifact_dir)

            # Promozione atomica
            final_dir.parent.mkdir(parents=True, exist_ok=True)
            if final_dir.exists():
                # race: qualcuno ha già vinto
                _ = _read_manifest(final_manifest_path)
                return

            try:
                _atomic_replace_dir(staging_artifact_dir, final_dir)
            except OSError:
                # Race tra exists() e replace(): se ora esiste un manifest valido, è idempotenza.
                if final_manifest_path.exists():
                    _ = _read_manifest(final_manifest_path)
                    return
                raise

            _fsync_dir_best_effort(final_dir.parent)

        finally:
            # Cleanup staging (se non già moved)
            try:
                if staging_dir.exists():
                    shutil.rmtree(staging_dir, ignore_errors=True)
            except Exception:
                pass

    def exists(self, *, tool_id: str, fingerprint: str) -> bool:
        validate_tool_id(tool_id)
        validate_fingerprint_lower_hex(fingerprint)
        return self._layout.manifest_path(tool_id=tool_id, fingerprint=fingerprint).exists()

    def get_manifest(self, *, tool_id: str, fingerprint: str) -> Manifest:
        validate_tool_id(tool_id)
        validate_fingerprint_lower_hex(fingerprint)
        return _read_manifest(self._layout.manifest_path(tool_id=tool_id, fingerprint=fingerprint))

    def open_output(self, *, tool_id: str, fingerprint: str, relpath: str) -> BinaryIO:
        validate_tool_id(tool_id)
        validate_fingerprint_lower_hex(fingerprint)
        rel = validate_relpath_safe(relpath)

        artifact_dir = self._layout.artifact_dir(
            tool_id=tool_id,
            fingerprint=fingerprint,
        ).resolve()

        # Resolve relpath against the specific artifact root, not the global store root.
        abs_path = resolve_within_root(artifact_dir, rel)

        # Enforce that served files stay within this artifact outputs directory.
        artifact_outputs = self._layout.outputs_root(
            tool_id=tool_id,
            fingerprint=fingerprint,
        ).resolve()

        try:
            abs_path.relative_to(artifact_outputs)
        except Exception as e:
            raise StorageInvariantError(
                "Requested relpath is not within this artifact outputs directory."
            ) from e

        try:
            return open(abs_path, "rb")
        except FileNotFoundError as e:
            raise ArtifactNotFoundError(str(abs_path)) from e

    def list_artifacts(self, *, tool_id: str) -> Sequence[str]:
        validate_tool_id(tool_id)
        tool_fp_dir = self._layout.tools_root() / tool_id / "fp"
        if not tool_fp_dir.exists():
            return []
        fps: List[str] = []
        for child in tool_fp_dir.iterdir():
            if child.is_dir():
                fps.append(child.name)
        fps.sort()
        return fps
