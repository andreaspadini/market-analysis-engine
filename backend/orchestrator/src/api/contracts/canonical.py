from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def config_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


# NOTE:
# - engines.root must be /config.yaml without engine_version (explicitly excluded in M2 spec)
# - engines.statistical groups 4 sources: config/mapping/sessions/targets (lossless)
# - engines.pattern mirrors config_pattern.yaml (validated by PatternConfig)
# - engines.query uses intents.json schema

GOLDEN_CANONICAL_HASH_V1 = "3cd57229b4b39438eea88af10eb45d737c904760e4554882fab8f99d684fc45b"

# Populate this dict by loading the real YAML/JSON and assembling it (freeze file in repo).
# (You can also store it as a .json file under docs/contracts and load it here.)
CANONICAL_PIPELINE_PARAMETERS_V1: Dict[str, Any] = {}