from __future__ import annotations
import hashlib

_DELIM = "\n"

def compute_artifact_identity_hash(*, input_hash: str, config_hash: str, engine_version: str) -> str:
    if not isinstance(input_hash, str):
        raise TypeError("input_hash must be str")
    if not isinstance(config_hash, str):
        raise TypeError("config_hash must be str")
    if not isinstance(engine_version, str):
        raise TypeError("engine_version must be str")
    payload = _DELIM.join([input_hash, config_hash, engine_version]).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def compute_o3_fingerprint(*, input_hash: str, config_hash: str, engine_version: str) -> str:
    return compute_artifact_identity_hash(
        input_hash=input_hash,
        config_hash=config_hash,
        engine_version=engine_version,
    )
