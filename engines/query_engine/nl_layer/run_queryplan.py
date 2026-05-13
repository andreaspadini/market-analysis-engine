import argparse
import json
import os
import subprocess
from pathlib import Path
import sys

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8-sig")

def main() -> int:
    ap = argparse.ArgumentParser(description="Run QueryPlan via frozen runner (no executor imports).")
    ap.add_argument("--queryplan", required=True, help="Path to QueryPlan JSON")
    ap.add_argument("--out", required=True, help="Output directory for runner artifacts")
    from importlib import resources
    ap.add_argument("--frozen-root", default=str(resources.files("market_analysis_engine.query_engine") / "frozen"),
                    help="Frozen root directory")
    ap.add_argument("--cache-dir", default=r".\qe_cache", help="Cache dir for materialized views")
    args = ap.parse_args()

    qp_path = Path(args.queryplan)
    out_dir = Path(args.out)
    frozen_root = Path(args.frozen_root)
    cache_dir = Path(args.cache_dir)

    qp = json.loads(read_text(qp_path))

    api_version = qp.get("api_version")
    if api_version != "1.0.0":
        raise ValueError(f"Unsupported QueryPlan api_version={api_version!r}. Expected '1.0.0'.")

    # Bridge mode (recommended for now): intent = {"name": "spec_path", "spec": "<path>"}
    intent = qp.get("intent", {})
    if intent.get("name") != "spec_path":
        raise ValueError("This runner expects intent.name == 'spec_path' for now.")
    spec_path = Path(intent.get("spec", ""))

    # If spec is relative to the frozen bundle (e.g. .\specs\calendar\...),
    # resolve it under --frozen-root.
    if not spec_path.is_absolute():
        s = str(spec_path).replace("/", "\\")
        if s.startswith(".\\specs\\") or s.startswith("specs\\"):
            spec_path = frozen_root / spec_path

    if not spec_path.exists():
        raise FileNotFoundError(f"Spec not found: {spec_path}")


    runner = frozen_root / "run_query_frozen.py"
    if not runner.exists():
        raise FileNotFoundError(f"Frozen runner not found: {runner}")

    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, str(runner),
        "--frozen-root", str(frozen_root),
        "--spec", str(spec_path),
        "--out", str(out_dir),
        "--cache-dir", str(cache_dir),
    ]

    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

    # Print a tiny summary
    spec_stem = spec_path.stem
    csv_path = out_dir / f"{spec_stem}.csv"
    meta_path = out_dir / f"{spec_stem}.meta.json"

    print("\nArtifacts:")
    print(" -", csv_path)
    print(" -", meta_path)

    if csv_path.exists():
        # Print first non-empty line
        with csv_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    print("\nCSV preview (first line):")
                    print(line)
                    break

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
