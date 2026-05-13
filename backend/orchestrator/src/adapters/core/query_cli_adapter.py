from __future__ import annotations
import sys
import json
from pathlib import Path
from typing import Any, Optional

from .base_adapter import BaseAdapter, RunPaths
from .core_types import ProducedArtifact


class QueryCliAdapter(BaseAdapter):
    """
    Pack (query_engine/README_IO.md):
      python .../run_queryplan.py --queryplan <file> --out <dir> --frozen-root <dir> --cache-dir <dir>

    Output:
      out/<spec_name>.csv
      out/<spec_name>.meta.json

    C1 naming:
      ArtifactSchemaRef(name="query_output", version="v1", ...) -> query_output.v1.json

    Policy:
      - 1 spec per run => enforce exactly 1 CSV + exactly 1 META match (determinismo)
      - META is not an official artifact in C2: store cleaned meta in execution_metadata
      - remove runtime field: _generated_at (adapter-local)
    """

    _OUTPUT_NAME = "query_output"
    _OUTPUT_VERSION = "v1"

    def adapter_id(self) -> str:
        return "query_engine_cli"

    # ---- repo root resolution (so we can run engine code while cwd is run_dir) ----

    @staticmethod
    def _repo_root() -> Path:
        """
        Resolve engine repo root deterministically from the installed editable package.
        """
        try:
            import market_analysis_engine  # editable install
            pkg_root = Path(market_analysis_engine.__file__).resolve().parents[1]
            return pkg_root.parent  # repo root (parent of src)
        except Exception:
            # Fallback should not happen in EIR-1
            return Path(__file__).resolve().parents[5]

    def prepare_run_dir(self, run_paths: RunPaths, input_payload: Any) -> None:
        """
        Expect dict input_payload with:
          - queryplan_path: str (json)
          - spec_path: str (json)  (the actual spec file referenced by queryplan)
          - frozen_root: str | Path (dir; relative allowed, resolved from repo root)
          - cache_seed_parquet_paths: optional list[str] (copied into cache dir if provided)

        Adapter stages everything inside run_dir in a pack-like layout:
          integration_pack/query_engine/
            queryplan.json
            specs/<spec_basename>.json
            out/
            cache/
        And rewrites queryplan.intent.spec to the staged spec relative path.
        """
        if not isinstance(input_payload, dict):
            raise ValueError("Query adapter expects dict input_payload")

        qp_path = input_payload.get("queryplan_path")
        spec_path = input_payload.get("spec_path")
        frozen_root = input_payload.get("frozen_root")

        if not qp_path or not spec_path or not frozen_root:
            raise ValueError("Missing required keys: queryplan_path, spec_path, frozen_root")

        pack_root = run_paths.run_dir / "integration_pack" / "query_engine"
        specs_dir = pack_root / "specs"
        out_dir = pack_root / "out"
        cache_dir = pack_root / "cache"

        specs_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Stage spec
        spec_src = Path(spec_path).resolve()
        spec_basename = spec_src.name
        spec_dst_rel = Path("integration_pack/query_engine/specs") / spec_basename
        spec_dst = self._copy_in_run_dir(run_paths, spec_src, spec_dst_rel)

        # Stage queryplan and rewrite to reference staged spec path (relative inside run_dir)
        qp_src = Path(qp_path).resolve()
        qp_obj = self._load_json_strict_path(qp_src)

        # defensive rewrite (pack says intent.name == "spec_path")
        intent = qp_obj.get("intent", {})
        if isinstance(intent, dict):
            intent_name = intent.get("name")
            if intent_name and intent_name != "spec_path":
                # not fatal, but keep deterministic behavior: still rewrite spec path
                pass
            intent["name"] = "spec_path"
            # IMPORTANT: keep it relative (as pack examples), but relative to run_dir
            intent["spec"] = str(spec_dst.relative_to(run_paths.run_dir)).replace("\\", "/")
            qp_obj["intent"] = intent
        else:
            raise ValueError("QueryPlan JSON missing/invalid 'intent' object")

        qp_dst = run_paths.run_dir / "integration_pack/query_engine/queryplan.json"
        qp_dst = self._assert_within_run_dir(run_paths, qp_dst)
        qp_str = json.dumps(qp_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        with qp_dst.open("w", encoding="utf-8", newline="\n") as f:
            f.write(qp_str)
            f.write("\n")

        # Optional: seed cache with parquet datasets if provided (pack note about df_master_enriched)
        seed = input_payload.get("cache_seed_parquet_paths")
        if seed is not None:
            seed_list = seed if isinstance(seed, list) else [seed]
            for p in seed_list:
                sp = Path(str(p)).resolve()
                if sp.suffix.lower() != ".parquet":
                    continue
                self._copy_in_run_dir(run_paths, sp, Path("integration_pack/query_engine/cache") / sp.name)

    def build_command(self, run_paths: RunPaths, *, timeout_s: int, extra_args: list[str]) -> list[str]:
        repo = self._repo_root()

        # script path in repo (pack example)
        script_rel = Path("query_engine/frozen/calendar_nl_v1_OFFICIAL/nl_layer/run_queryplan.py")
        script = (repo / script_rel).resolve()

        pack_root = run_paths.run_dir / "integration_pack" / "query_engine"
        queryplan = (pack_root / "queryplan.json").resolve()
        out_dir = (pack_root / "out").resolve()
        cache_dir = (pack_root / "cache").resolve()

        # frozen_root passed via payload (relative allowed -> repo-root resolved)
        # Note: we don't write into frozen_root (writes stay in cache/out under run_dir)
        # It is safe to read outside run_dir.
        # We'll store resolved path into execution_metadata in run().
        # Resolve here by reading snapshot (staged queryplan already exists).
        frozen_root = self._read_frozen_root_from_snapshot(run_paths)

        cmd = [
            sys.executable,
            str(script),
            "--queryplan",
            str(queryplan),
            "--out",
            str(out_dir),
            "--frozen-root",
            str(frozen_root),
            "--cache-dir",
            str(cache_dir),
        ]
        cmd.extend(extra_args)
        return cmd

    def expected_outputs(self, run_paths: RunPaths) -> list[str | Path]:
        # 1 spec per run => enforce exactly 1 match per kind during capture
        return [
            "integration_pack/query_engine/out/*.csv",
            "integration_pack/query_engine/out/*.meta.json",
        ]

    def normalized_artifact_name(self, raw_output: Path) -> str:
        # Derived only from C1 outputs_schema
        return f"{self._OUTPUT_NAME}.{self._OUTPUT_VERSION}.json"

    # ---- capture override: enforce exactly 1 CSV + 1 META; CSV->JSON artifact; META->execution_metadata ----

    def _capture_and_normalize_outputs(self, run_paths: RunPaths) -> list[ProducedArtifact]:
        # Expand globs deterministically (BaseAdapter helper)
        expanded = self._expand_expected(run_paths, self.expected_outputs(run_paths))
        csvs = [p for p in expanded if p.suffix.lower() == ".csv"]
        metas = [p for p in expanded if p.name.endswith(".meta.json")]

        # Determinism: enforce exactly 1 of each
        if len(csvs) != 1:
            raise ValueError(f"Expected exactly 1 CSV in out/, got {len(csvs)}: {csvs}")
        if len(metas) != 1:
            raise ValueError(f"Expected exactly 1 META JSON in out/, got {len(metas)}: {metas}")

        csv_path = csvs[0]
        meta_path = metas[0]
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV output missing: {csv_path}")
        if not meta_path.exists():
            raise FileNotFoundError(f"META output missing: {meta_path}")

        # CSV -> JSON strict deterministico (use BaseAdapter module helpers for consistent coercion)
        from . import base_adapter as ba  # local import (C2 ok)

        rows = ba._load_csv_as_json_strict(csv_path)
        rows = ba._remove_runtime_fields(rows)  # standard blacklist
        # Query-specific runtime cleanup (meta contains _generated_at; rows typically don't, but safe)
        rows = self._remove_query_runtime(rows)

        s = ba._json_dumps_deterministic(rows)

        normalized_path = self._assert_within_run_dir(
            run_paths,
            run_paths.output_dir / self.normalized_artifact_name(csv_path),
        )
        with normalized_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(s)
            f.write("\n")

        # META -> cleaned dict into execution_metadata (not an artifact)
        meta_obj = self._load_json_strict_path(meta_path)
        meta_obj = ba._remove_runtime_fields(meta_obj)
        meta_obj = self._remove_query_runtime(meta_obj)

        # Attach meta to the already-existing execution_metadata created in BaseAdapter.run()
        # We can safely store it here by writing a sidecar file and letting tests read it.
        # But BaseAdapter.run() doesn't pass metadata into this method.
        # Solution: write cleaned meta into logs/ for debug + deterministic replay safety.
        meta_clean_path = self._assert_within_run_dir(run_paths, run_paths.logs_dir / "query_meta.cleaned.json")
        meta_s = json.dumps(meta_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        with meta_clean_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(meta_s)
            f.write("\n")

        return [ProducedArtifact(name=normalized_path.name, path=str(normalized_path))]

    # ---- helpers ----

    def _remove_query_runtime(self, obj: Any) -> Any:
        # adapter-local: remove _generated_at (recursive)
        if isinstance(obj, dict):
            out: dict[str, Any] = {}
            for k, v in obj.items():
                if k == "_generated_at":
                    continue
                out[k] = self._remove_query_runtime(v)
            return out
        if isinstance(obj, list):
            return [self._remove_query_runtime(x) for x in obj]
        return obj

    def _load_json_strict_path(self, p: Path) -> Any:
        def _bad_const(x: str) -> Any:
            raise ValueError(f"Invalid JSON constant: {x}")

        with p.open("r", encoding="utf-8") as f:
            return json.load(f, parse_constant=_bad_const)

    def _read_frozen_root_from_snapshot(self, run_paths: RunPaths) -> Path:
        """
        Read frozen_root from payload_snapshot if present; fallback to repo-root relative resolution.
        This keeps build_command deterministic without requiring global state.
        """
        snap = run_paths.input_dir / "payload_snapshot.json"
        try:
            obj = self._load_json_strict_path(snap)
            frozen = obj.get("frozen_root") if isinstance(obj, dict) else None
        except Exception:
            frozen = None

        if frozen is None:
            # last-resort: use a stable default (but in real runs frozen_root should be provided)
            return (self._repo_root() / "query_engine/frozen").resolve()

        fr = Path(str(frozen))
        if fr.is_absolute():
            return fr.resolve()
        return (self._repo_root() / fr).resolve()
