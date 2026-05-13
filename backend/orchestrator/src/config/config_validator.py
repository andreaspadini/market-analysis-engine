"""O2 Config Schema v1 validator (M2).

Strict-by-default structural validation for the Run Config.

Design constraints (frozen):
- Validation is pure: no I/O, no storage/runtime coupling
- Unknown fields are errors when strict=True (default)
- No implicit defaults that would alter fingerprint
- Strict JSON domain: reject NaN/Infinity and non-JSON Python types
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set


class ConfigValidationError(ValueError):
    """Raised when a config violates the O2 schema."""

    def __init__(self, message: str, path: str = "$") -> None:
        super().__init__(f"{message} (at {path})")
        self.path = path


_CONFIG_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+$")

# Frozen stability constraint (config-spec.md):
# - lowercase only
# - no whitespace, no slashes/paths
# - length 3–64
_PIPELINE_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{2,63}$")


def validate_config(config: Any, *, strict: bool = True) -> Dict[str, Any]:
    """Validate a candidate config.

    Returns the same dict instance (not mutated) if valid.

    Args:
        config: candidate config object
        strict: when True (default), unknown fields are rejected
    """

    if not isinstance(config, dict):
        raise ConfigValidationError("Config must be a JSON object", "$")

    _validate_json_domain(config, path="$", strict_numbers=True)

    # Validate config_version first (invariant)
    if "config_version" not in config:
        raise ConfigValidationError("Missing required field 'config_version'", "$")
    _validate_config_version(config.get("config_version"), path="$.config_version")

    allowed_top = {"config_version", "pipeline", "parameters", "resources", "metadata"}
    if strict:
        _reject_unknown_keys(config, allowed_top, path="$")

    # Required fields
    if "pipeline" not in config:
        raise ConfigValidationError("Missing required field 'pipeline'", "$")
    if "parameters" not in config:
        raise ConfigValidationError("Missing required field 'parameters'", "$")

    pipeline = config.get("pipeline")
    if not isinstance(pipeline, dict):
        raise ConfigValidationError("'pipeline' must be an object", "$.pipeline")
    _validate_pipeline(pipeline, strict=strict, path="$.pipeline")

    parameters = config.get("parameters")
    if not isinstance(parameters, dict):
        raise ConfigValidationError("'parameters' must be an object", "$.parameters")

    resources = config.get("resources")
    if resources is not None and not isinstance(resources, dict):
        raise ConfigValidationError("'resources' must be an object", "$.resources")

    metadata = config.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise ConfigValidationError("'metadata' must be an object", "$.metadata")

    return config


def _validate_config_version(value: Any, *, path: str) -> None:
    if not isinstance(value, str):
        raise ConfigValidationError("'config_version' must be a string", path)
    if not _CONFIG_VERSION_RE.match(value):
        raise ConfigValidationError("'config_version' must match 'X.Y'", path)
    major_str, _minor_str = value.split(".", 1)
    try:
        major = int(major_str)
    except ValueError:
        raise ConfigValidationError("'config_version' must match 'X.Y'", path) from None
    if major != 1:
        raise ConfigValidationError("Unsupported config_version major; expected 1.*", path)


def _validate_pipeline(pipeline: Dict[str, Any], *, strict: bool, path: str) -> None:
    allowed = {"id", "revision", "steps"}
    if strict:
        _reject_unknown_keys(pipeline, allowed, path=path)

    if "id" not in pipeline:
        raise ConfigValidationError("Missing required field 'pipeline.id'", path)
    pid = pipeline.get("id")
    if not isinstance(pid, str):
        raise ConfigValidationError("'pipeline.id' must be a string", f"{path}.id")
    if not _PIPELINE_ID_RE.match(pid):
        raise ConfigValidationError(
            "'pipeline.id' must match ^[a-z][a-z0-9_.-]{2,63}$",
            f"{path}.id",
        )

    if "revision" in pipeline and pipeline["revision"] is not None:
        if not isinstance(pipeline["revision"], str):
            raise ConfigValidationError("'pipeline.revision' must be a string", f"{path}.revision")

    if "steps" in pipeline and pipeline["steps"] is not None:
        steps = pipeline["steps"]
        if not isinstance(steps, list):
            raise ConfigValidationError("'pipeline.steps' must be an array", f"{path}.steps")
        if len(steps) == 0:
            raise ConfigValidationError("'pipeline.steps' must be non-empty when provided", f"{path}.steps")
        _validate_steps(steps, strict=strict, path=f"{path}.steps")


def _validate_steps(steps: List[Any], *, strict: bool, path: str) -> None:
    seen_ids: Set[str] = set()
    declared_ids: List[str] = []

    for i, step in enumerate(steps):
        spath = f"{path}[{i}]"
        if not isinstance(step, dict):
            raise ConfigValidationError("Each step must be an object", spath)

        allowed = {"step_id", "op", "with", "needs"}
        if strict:
            _reject_unknown_keys(step, allowed, path=spath)

        if "step_id" not in step:
            raise ConfigValidationError("Missing required field 'step_id'", spath)
        if "op" not in step:
            raise ConfigValidationError("Missing required field 'op'", spath)

        step_id = step.get("step_id")
        if not isinstance(step_id, str) or not step_id:
            raise ConfigValidationError("'step_id' must be a non-empty string", f"{spath}.step_id")
        if step_id in seen_ids:
            raise ConfigValidationError("Duplicate 'step_id' in steps", f"{spath}.step_id")
        seen_ids.add(step_id)
        declared_ids.append(step_id)

        op = step.get("op")
        if not isinstance(op, str) or not op:
            raise ConfigValidationError("'op' must be a non-empty string", f"{spath}.op")

        if "with" in step and step["with"] is not None:
            if not isinstance(step["with"], dict):
                raise ConfigValidationError("'with' must be an object", f"{spath}.with")

        if "needs" in step and step["needs"] is not None:
            needs = step["needs"]
            if not isinstance(needs, list):
                raise ConfigValidationError("'needs' must be an array of strings", f"{spath}.needs")
            for j, dep in enumerate(needs):
                if not isinstance(dep, str) or not dep:
                    raise ConfigValidationError(
                        "'needs' entries must be non-empty strings",
                        f"{spath}.needs[{j}]",
                    )

    # Second pass: dependency references
    declared_set = set(declared_ids)
    for i, step in enumerate(steps):
        if "needs" not in step or step["needs"] is None:
            continue
        spath = f"{path}[{i}]"
        for j, dep in enumerate(step["needs"]):
            if dep not in declared_set:
                raise ConfigValidationError(
                    "'needs' must reference existing step_id",
                    f"{spath}.needs[{j}]",
                )


def _reject_unknown_keys(obj: Mapping[str, Any], allowed: Set[str], *, path: str) -> None:
    for k in obj.keys():
        if k not in allowed:
            raise ConfigValidationError(f"Unknown field '{k}'", f"{path}.{k}")


def _validate_json_domain(value: Any, *, path: str, strict_numbers: bool) -> None:
    """Validate that `value` is within the strict JSON domain.

    - dict keys must be strings
    - arrays are lists
    - numbers are int/float but float must be finite (no NaN/Infinity)
    - rejects non-JSON Python types (tuple/set/bytes/...)

    This is intentionally independent from the schema shape checks.
    """

    # Order matters: bool is subclass of int
    if value is None or isinstance(value, (str, bool)):
        return

    if isinstance(value, int):
        return

    if isinstance(value, float):
        if strict_numbers and not math.isfinite(value):
            raise ConfigValidationError("Non-finite number (NaN/Infinity) is not allowed", path)
        return

    if isinstance(value, list):
        for i, item in enumerate(value):
            _validate_json_domain(item, path=f"{path}[{i}]", strict_numbers=strict_numbers)
        return

    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise ConfigValidationError("Object keys must be strings", f"{path}")
            _validate_json_domain(v, path=f"{path}.{k}", strict_numbers=strict_numbers)
        return

    # Everything else is rejected as non-JSON
    raise ConfigValidationError(f"Non-JSON type '{type(value).__name__}' is not allowed", path)
