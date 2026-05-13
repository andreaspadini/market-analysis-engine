# pattern_engine/similarity/similarity_engine.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any

import numpy as np


class SimilarityError(ValueError):
    """Raised when inputs are invalid for similarity computation."""


def _safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception as e:
        raise SimilarityError(f"Cannot convert to float: {x!r}") from e


def _validate_1d(a: np.ndarray, name: str) -> np.ndarray:
    if not isinstance(a, np.ndarray):
        raise SimilarityError(f"{name} must be a numpy.ndarray")
    if a.ndim != 1:
        raise SimilarityError(f"{name} must be 1D, got shape={a.shape}")
    if not np.all(np.isfinite(a)):
        raise SimilarityError(f"{name} contains NaN/inf")
    return a.astype(np.float64, copy=False)


def _extract_channel_dims(
    total_len: int,
    feature_set: dict,
    weights: dict,
    distance_caps: dict,
) -> Tuple[int, int, int]:
    """
    Tries to infer (price_len, volume_len, delta_len).

    Preferred: feature_set["channel_dims"] = {"price": int, "volume": int, "delta": int}
    Fallbacks: distance_caps["channel_dims"], weights["channel_dims"]

    If missing, infer canonical Cap.5-like layout:
      - P+V+D: total = 6N  => price=4N, volume=N, delta=N
      - P+V or P+D: total = 5N => price=4N, other=N (chosen by feature_set toggles)
      - P only: total = 4N => price=4N

    Last-resort fallback: split equally among enabled channels (NOT recommended).
    """
    # 1) Preferred explicit metadata
    for src in (feature_set, distance_caps, weights):
        cd = (src or {}).get("channel_dims")

        if isinstance(cd, dict) and "price" in cd and "volume" in cd and "delta" in cd:
            p = int(cd["price"])
            v = int(cd["volume"])
            d = int(cd["delta"])
            if p < 0 or v < 0 or d < 0:
                raise SimilarityError("channel_dims cannot contain negative lengths")
            if p + v + d != total_len:
                raise SimilarityError(
                    f"channel_dims sum mismatch: price+volume+delta={p+v+d} != total_len={total_len}"
                )
            return p, v, d

    enabled = [k for k in ("price", "volume", "delta") if bool(feature_set.get(k, False))]
    if not enabled:
        raise SimilarityError("feature_set has no enabled channels")

    # 2) Canonical inference (Cap.5-like)
    # total = 6N => (4N, N, N)
    if total_len % 6 == 0:
        n = total_len // 6
        return 4 * n, n, n

    # total = 5N => (4N, N, 0) or (4N, 0, N)
    if total_len % 5 == 0:
        n = total_len // 5
        vol_on = bool(feature_set.get("volume", False))
        del_on = bool(feature_set.get("delta", False))

        # If only one of the optional channels is enabled, assign it the trailing N.
        # If both are enabled (ambiguous), prefer volume by convention.
        if del_on and not vol_on:
            return 4 * n, 0, n
        return 4 * n, n, 0

    # total = 4N => (4N, 0, 0)
    if total_len % 4 == 0:
        n = total_len // 4
        return 4 * n, 0, 0

    # 3) Last resort: equal split among enabled channels
    n = len(enabled)
    base = total_len // n
    rem = total_len % n
    lens = {k: 0 for k in ("price", "volume", "delta")}
    for i, k in enumerate(enabled):
        lens[k] = base + (1 if i < rem else 0)

    return lens["price"], lens["volume"], lens["delta"]


def _split_channels(
    x: np.ndarray,
    dims: Tuple[int, int, int],
) -> Dict[str, np.ndarray]:
    p, v, d = dims
    out: Dict[str, np.ndarray] = {}
    i0 = 0
    out["price"] = x[i0 : i0 + p]
    i0 += p
    out["volume"] = x[i0 : i0 + v]
    i0 += v
    out["delta"] = x[i0 : i0 + d]
    return out


def _euclidean(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0:
        return 0.0
    diff = a - b
    # normalized by sqrt(n) to keep distances comparable across different channel sizes
    return float(np.linalg.norm(diff) / np.sqrt(a.size))


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0:
        return 0.0
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 and nb == 0.0:
        return 0.0
    if na == 0.0 or nb == 0.0:
        # maximally different direction when one vector is zero and the other is not
        return 1.0
    cos_sim = float(np.dot(a, b) / (na * nb))
    # numerical safety
    cos_sim = max(-1.0, min(1.0, cos_sim))
    # cosine distance in [0, 2]
    return 1.0 - cos_sim


def compute_similarity(
    ref_features: np.ndarray,
    cand_features: np.ndarray,
    *,
    feature_set: dict,
    weights: dict | None,
    distance_caps: dict | None,
    method: str = "euclidean",
) -> float:
    """
    Compute similarity_score ∈ [0,1] between reference and candidate feature vectors.

    - Split feature vectors into channels (price / volume / delta) using channel_dims metadata
      if available (feature_set/distance_caps/weights).
    - Per-channel distance: euclidean (default) or cosine distance
    - Clamp raw distance with per-channel cap
    - Normalize per channel: normalized_dist_channel = clamp(dist, cap) / cap  (=> in [0,1])
    - Combine: dist = Σ w_channel * normalized_dist_channel
    - similarity_score = max(0, 1 - dist)  (=> in [0,1])

    Assumptions:
    - ref_features.shape == cand_features.shape
    - weights already normalized over enabled channels (sum=1 across enabled channels)
    """
    ref = _validate_1d(ref_features, "ref_features")
    cand = _validate_1d(cand_features, "cand_features")

    # HARDENING: treat None as {}
    weights = weights or {}
    distance_caps = distance_caps or {}

    if ref.shape != cand.shape:
        raise SimilarityError(f"Shape mismatch: ref={ref.shape} cand={cand.shape}")

    method = (method or "euclidean").lower().strip()
    if method not in ("euclidean", "cosine"):
        raise SimilarityError(f"Unsupported method={method!r}. Use 'euclidean' or 'cosine'.")

    dims = _extract_channel_dims(ref.size, feature_set, weights, distance_caps)
    ref_ch = _split_channels(ref, dims)
    cand_ch = _split_channels(cand, dims)

    dist_total = 0.0

    for ch in ("price", "volume", "delta"):
        enabled = bool(feature_set.get(ch, False))
        w = _safe_float(weights.get(ch, 0.0))

        # Test 4: feature disabilitata non deve influire
        if (not enabled) or w == 0.0:
            continue

        cap = _safe_float(distance_caps.get(ch, 1.0))
        if cap <= 0.0:
            # A zero/negative cap would break normalization.
            # Treat as "no contribution" but keep determinism.
            continue

        if method == "euclidean":
            raw = _euclidean(ref_ch[ch], cand_ch[ch])
        else:
            raw = _cosine_distance(ref_ch[ch], cand_ch[ch])

        # clamp + normalize into [0,1]
        clamped = min(raw, cap)
        norm = clamped / cap

        dist_total += w * norm

    # Ensure strict bounds and no NaN/inf
    if not np.isfinite(dist_total):
        # safety net: should not happen due to validations
        dist_total = 1.0

    dist_total = max(0.0, min(1.0, dist_total))
    similarity = 1.0 - dist_total
    similarity = max(0.0, min(1.0, similarity))
    return float(similarity)
