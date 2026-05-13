from __future__ import annotations

import abc
import csv
import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional, Mapping, Iterable

from .core_types import CoreResult, ProducedArtifact


RUNTIME_FIELDS_BLACKLIST = {
    "run_id",
    "timestamp",
    "generated_at",
    "execution_time",
    "computation_time",
    "computation_timestamp",
    "generatedAt",
    "created_at",
    "createdAt",
}

_INT_RE = re.compile(r"^[+-]?\d+$")
_DEC_RE = re.compile(r"^[+-]?\d+(\.\d+)?([eE][+-]?\d+)?$")


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def _remove_runtime_fields(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if k in RUNTIME_FIELDS_BLACKLIST:
                continue
            out[k] = _remove_runtime_fields(v)
        return out
    if isinstance(obj, list):
        return [_remove_runtime_fields(x) for x in obj]
    return obj


def _json_dumps_deterministic(obj: Any) -> str:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _coerce_csv_value(v: str) -> Any:
    vv = (v or "").strip()
    if vv == "":
        return None
    low = vv.lower()
    if low in {"true", "false"}:
        return low == "true"

    if _INT_RE.match(vv):
        try:
            return int(vv)
        except Exception:
            return vv

    if _DEC_RE.match(vv):
        try:
            d = Decimal(vv)
            n = format(d.normalize(), "f")
            if "." in n:
                n = n.rstrip("0").rstrip(".")
            return n if n != "" else "0"
        except (InvalidOperation, ValueError):
            return vv

    return vv


def _load_csv_as_json_strict(csv_path: Path) -> Any:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, Any]] = []
        for row in reader:
            rows.append({k: _coerce_csv_value(v) for k, v in row.items()})
        return rows


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    input_dir: Path
    output_dir: Path
    logs_dir: Path


class BaseAdapter(abc.ABC):
    def __init__(self, *, tmp_root: Optional[Path] = None):
        self._tmp_root = (tmp_root or Path("tmp")).resolve()

    @abc.abstractmethod
    def adapter_id(self) -> str:
        ...

    @abc.abstractmethod
    def build_command(self, run_paths: RunPaths, *, timeout_s: int, extra_args: list[str]) -> list[str]:
        ...

    @abc.abstractmethod
    def expected_outputs(self, run_paths: RunPaths) -> list[str | Path]:
        """Paths or globs, relative resolved against run_dir."""

    # --- naming hooks (config-only) ---

    def artifact_name_map(self) -> dict[str, str]:
        """Legacy mapping raw basename -> normalized basename."""
        return {}

    def normalized_artifact_name(self, raw_output: Path) -> str:
        """
        Default:
        - if basename in artifact_name_map => mapped name
        - else keep raw basename
        Subclasses can override to force stable names even with dynamic filenames.
        """
        return self.artifact_name_map().get(raw_output.name, raw_output.name)

    # --- runtime config hooks ---

    def env_overrides(self) -> Mapping[str, str]:
        return {}

    def timeout_default_s(self) -> int:
        return 60

    def prepare_run_dir(self, run_paths: RunPaths, input_payload: Any) -> None:
        """Optional staging hook. Default no-op."""

    # ---------- runner ----------

    def run(self, input_payload: Any, *, timeout_s: Optional[int] = None, extra_args: Optional[list[str]] = None) -> CoreResult:
        timeout = int(timeout_s or self.timeout_default_s())
        args = list(extra_args or [])
        run_paths = self._create_isolated_workdir()

        self._write_payload_snapshot(run_paths, input_payload)

        try:
            self.prepare_run_dir(run_paths, input_payload)
        except Exception as e:
            return CoreResult(
                success=False,
                produced_artifacts=[],
                logs_path=str(run_paths.logs_dir),
                execution_metadata={"adapter_id": self.adapter_id(), "stage_exception": repr(e), "run_dir": str(run_paths.run_dir)},
            )

        cmd = self.build_command(run_paths, timeout_s=timeout, extra_args=args)
        meta: dict[str, Any] = {"adapter_id": self.adapter_id(), "command": cmd, "timeout_s": timeout, "run_dir": str(run_paths.run_dir)}

        try:
            completed = self._run_subprocess(cmd, run_paths, timeout_s=timeout)
            meta["returncode"] = completed.returncode
        except Exception as e:
            meta["exception"] = repr(e)
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

        if completed.returncode != 0:
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

        try:
            produced = self._capture_and_normalize_outputs(run_paths)
            return CoreResult(True, produced, str(run_paths.logs_dir), meta)
        except Exception as e:
            meta["capture_exception"] = repr(e)
            return CoreResult(False, [], str(run_paths.logs_dir), meta)

    def _create_isolated_workdir(self) -> RunPaths:
        run_id = uuid.uuid4().hex
        run_dir = (self._tmp_root / f"run_{run_id}").resolve()
        input_dir = (run_dir / "input").resolve()
        output_dir = (run_dir / "output").resolve()
        logs_dir = (run_dir / "logs").resolve()

        input_dir.mkdir(parents=True, exist_ok=False)
        output_dir.mkdir(parents=True, exist_ok=False)
        logs_dir.mkdir(parents=True, exist_ok=False)

        assert run_dir.is_absolute(), "run_dir must be absolute"
        return RunPaths(run_dir=run_dir, input_dir=input_dir, output_dir=output_dir, logs_dir=logs_dir)

    def _assert_within_run_dir(self, run_paths: RunPaths, p: Path) -> Path:
        rp = p.resolve()
        if not _is_relative_to(rp, run_paths.run_dir):
            raise ValueError(f"Path escapes run dir: {rp} not within {run_paths.run_dir}")
        return rp

    def _write_payload_snapshot(self, run_paths: RunPaths, payload: Any) -> None:
        snap = self._assert_within_run_dir(run_paths, run_paths.input_dir / "payload_snapshot.json")
        obj = _remove_runtime_fields(payload) if isinstance(payload, (dict, list)) else {"payload_repr": repr(payload)}
        s = _json_dumps_deterministic(obj)
        with snap.open("w", encoding="utf-8", newline="\n") as f:
            f.write(s)
            f.write("\n")

    def _run_subprocess(self, cmd: list[str], run_paths: RunPaths, *, timeout_s: int) -> subprocess.CompletedProcess[bytes]:
        cwd = run_paths.run_dir.resolve()
        assert cwd.is_absolute(), "cwd must be absolute"

        env = os.environ.copy()
        env.update(dict(self.env_overrides() or {}))

        stderr_path = self._assert_within_run_dir(run_paths, run_paths.logs_dir / "stderr.txt")
        stdout_path = self._assert_within_run_dir(run_paths, run_paths.logs_dir / "stdout.txt")

        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            shell=False,
            timeout=timeout_s,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        stdout_path.write_bytes(completed.stdout or b"")
        stderr_path.write_bytes(completed.stderr or b"")
        return completed

    def _expand_expected(self, run_paths: RunPaths, items: Iterable[str | Path]) -> list[Path]:
        expanded: list[Path] = []
        for it in items:
            s = str(it)
            base = run_paths.run_dir
            candidate = Path(s) if Path(s).is_absolute() else (base / s)

            if any(ch in s for ch in ["*", "?", "["]):
                matches = sorted(candidate.parent.glob(candidate.name))
                for m in matches:
                    expanded.append(self._assert_within_run_dir(run_paths, m))
            else:
                expanded.append(self._assert_within_run_dir(run_paths, candidate))
        return expanded

    def _capture_and_normalize_outputs(self, run_paths: RunPaths) -> list[ProducedArtifact]:
        expected = self._expand_expected(run_paths, self.expected_outputs(run_paths))
        if not expected:
            raise FileNotFoundError("No expected outputs matched (empty set)")

        for p in expected:
            if not p.exists():
                raise FileNotFoundError(f"Expected output missing: {p}")

        produced: list[ProducedArtifact] = []

        for raw_path in expected:
            normalized_name = self.normalized_artifact_name(raw_path)
            normalized_path = self._assert_within_run_dir(run_paths, run_paths.output_dir / normalized_name)

            if raw_path.suffix.lower() == ".json":
                obj = self._load_json_strict(raw_path)
                obj = _remove_runtime_fields(obj)
                s = _json_dumps_deterministic(obj)
                with normalized_path.open("w", encoding="utf-8", newline="\n") as f:
                    f.write(s)
                    f.write("\n")

            elif raw_path.suffix.lower() == ".csv":
                obj = _load_csv_as_json_strict(raw_path)
                obj = _remove_runtime_fields(obj)
                s = _json_dumps_deterministic(obj)
                if not normalized_path.name.endswith(".json"):
                    normalized_path = self._assert_within_run_dir(run_paths, run_paths.output_dir / (normalized_path.name + ".json"))
                with normalized_path.open("w", encoding="utf-8", newline="\n") as f:
                    f.write(s)
                    f.write("\n")

            else:
                normalized_path = raw_path

            produced.append(ProducedArtifact(name=normalized_path.name, path=str(normalized_path)))

        for art in produced:
            self._assert_within_run_dir(run_paths, Path(art.path))

        return produced

    def _load_json_strict(self, p: Path) -> Any:
        def _bad_const(x: str) -> Any:
            raise ValueError(f"Invalid JSON constant: {x}")

        with p.open("r", encoding="utf-8") as f:
            return json.load(f, parse_constant=_bad_const)

    def _copy_in_run_dir(self, run_paths: RunPaths, src: Path, dst_rel: str | Path) -> Path:
        srcp = src.resolve()
        dst = self._assert_within_run_dir(run_paths, run_paths.run_dir / Path(dst_rel))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(srcp, dst)
        return dst
