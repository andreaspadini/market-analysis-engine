from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from engines.root_engine.dataset_loader import (
    load_dataset,
    load_dataset_for_timeframe,
)
from engines.root_engine.processing.balance.balance_detector import BalanceDetector
from engines.root_engine.processing.breakout.breakout_detector import BreakoutDetector


TOOL_ID = "root_engine"


def _canonical_dumps(obj: Any) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="market_analysis_engine.root_engine")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args(argv)

    in_path = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = json.loads(in_path.read_text(encoding="utf-8-sig"))

    tool_id = payload.get("tool_id", TOOL_ID)
    if tool_id != TOOL_ID:
        raise ValueError(f"tool_id mismatch: expected {TOOL_ID}, got {tool_id}")

    config: Dict[str, Any] = payload.get("config", {}) or {}
    dataset = payload.get("dataset")

    if dataset is None:
        raise ValueError("Root Engine EDI-2B requires payload['dataset']")

    bars = load_dataset(dataset)
    lower_tf_bars: List[Dict[str, Any]] = []

    early_cfg = config.get("breakout", {}).get("early_detection", {}) or {}
    if early_cfg.get("enabled", False):
        lower_tf = early_cfg.get("lower_timeframe")
        ref_tf = early_cfg.get("reference_timeframe")

        dataset_tf = dataset.get("timeframe")
        if (
            isinstance(lower_tf, str)
            and lower_tf.strip()
            and lower_tf != dataset_tf
            and (not ref_tf or ref_tf == dataset_tf)
        ):
            lower_tf_bars = load_dataset_for_timeframe(dataset, lower_tf)

    balance_detector = BalanceDetector(config=config, bars=bars)
    balances = balance_detector.run()

    detector = BreakoutDetector(
        config=config,
        bars=bars,
        lower_tf_bars=lower_tf_bars,
        balances=balances,
    )

    try:
        breakouts = detector.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise

    artifact = {
        "tool_id": TOOL_ID,
        "balances": [b.model_dump(mode="json") for b in balances],
        "breakouts": [b.model_dump(mode="json") for b in breakouts],
        "counts": {
            "balances": len(balances),
            "bars": len(bars),
            "lower_tf_bars": len(lower_tf_bars),
            "breakouts": len(breakouts),
        },
    }

    artifact_path = out_dir / "root_engine_result.json"
    artifact_path.write_bytes(_canonical_dumps(artifact))

    sys.stdout.buffer.write(
        _canonical_dumps(
            {
                "tool_id": TOOL_ID,
                "artifacts": ["root_engine_result.json"],
                "counts": artifact["counts"],
            }
        )
    )
    sys.stdout.buffer.write(b"\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())