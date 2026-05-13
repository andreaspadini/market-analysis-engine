from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from .normalization import PriceNormalizer, ratio_to_mean

_EPS = 1e-12


def _require_cols(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"df_window missing required columns: {missing}")


def extract_features(
    df_window: pd.DataFrame,
    *,
    feature_set: dict,
    normalization_mode: str,
) -> np.ndarray:
    """
    Trasforma una finestra OHLCV (N barre) in un feature vector 1D float, senza NaN/inf.

    Ordine feature nel vettore (stabile):
    1) PRICE shape: per barra [range, body, upper_wick, lower_wick] normalizzati (N*4)
    2) VOLUME (se abilitato): ratio vs mean finestra (N*1)
    3) DELTA  (se abilitato): ratio vs mean finestra (N*1)

    Note:
    - Normalizzazione prezzi: sempre relativa (no tick assoluti).
    - Volume/Delta: ratio vs media finestra (robusta, evita std=0).
    """
    if not isinstance(df_window, pd.DataFrame):
        raise TypeError("df_window must be a pandas DataFrame")

    if len(df_window) <= 0:
        raise ValueError("df_window must contain at least 1 bar")

    # feature_set atteso: {"price": bool, "volume": bool, "delta": bool}
    price_on = bool(feature_set.get("price", False))
    vol_on = bool(feature_set.get("volume", False))
    delta_on = bool(feature_set.get("delta", False))

    if not (price_on or vol_on or delta_on):
        raise ValueError("feature_set must enable at least one of: price, volume, delta")

    feats: list[np.ndarray] = []

    if price_on:
        _require_cols(df_window, ["open", "high", "low", "close"])
        o = df_window["open"].to_numpy(dtype=float)
        h = df_window["high"].to_numpy(dtype=float)
        l = df_window["low"].to_numpy(dtype=float)
        c = df_window["close"].to_numpy(dtype=float)

        rng = h - l
        body = np.abs(c - o)
        upper = h - np.maximum(o, c)
        lower = np.minimum(o, c) - l

        # Clip minimo per evitare micro-negativi da floating
        rng = np.maximum(rng, 0.0)
        body = np.maximum(body, 0.0)
        upper = np.maximum(upper, 0.0)
        lower = np.maximum(lower, 0.0)

        scale = PriceNormalizer(normalization_mode).scale(df_window)
        scale = max(float(scale), _EPS)

        # (N,4) -> flat (N*4,)
        price_mat = np.stack([rng / scale, body / scale, upper / scale, lower / scale], axis=1)
        feats.append(price_mat.reshape(-1).astype(float, copy=False))

    if vol_on:
        _require_cols(df_window, ["volume"])
        v = df_window["volume"].to_numpy(dtype=float)
        v_norm = ratio_to_mean(v)
        feats.append(v_norm.reshape(-1).astype(float, copy=False))

    if delta_on:
        if "delta" not in df_window.columns:
            raise ValueError("feature_set requires delta but df_window has no 'delta' column")
        d = df_window["delta"].to_numpy(dtype=float)
        d_norm = ratio_to_mean(d)
        feats.append(d_norm.reshape(-1).astype(float, copy=False))

    out = np.concatenate(feats, axis=0).astype(float, copy=False)

    # Hard gate: nessun NaN/inf
    if not np.isfinite(out).all():
        # prova a rendere esplicito dove si rompe
        bad = np.where(~np.isfinite(out))[0]
        raise ValueError(f"Non-finite values in features at indices {bad[:10].tolist()} (showing up to 10)")

    return out
