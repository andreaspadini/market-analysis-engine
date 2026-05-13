from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

_EPS = 1e-12


@dataclass(frozen=True)
class PriceNormalizer:
    """
    Normalizzatore prezzi per pattern "in scala" (no tick assoluti).

    Modes supportati:
    - "window_mean_range": scala = mean(high - low) sulla finestra
    - "pattern_mean_range": alias di "window_mean_range" (compatibilità config/progetto)
    - "atr": scala = ATR passato dall'esterno, preso da:
        1) df_window.attrs["atr"] (float) oppure
        2) colonna df_window["atr"] (costante o ultimo valore)
    """

    mode: str

    def scale(self, df_window: pd.DataFrame) -> float:
        if self.mode in {"window_mean_range", "pattern_mean_range"}:
            rng = (
                df_window["high"].to_numpy(dtype=float)
                - df_window["low"].to_numpy(dtype=float)
            )
            s = float(np.nanmean(rng))
            return max(s, _EPS)

        if self.mode == "atr":
            atr = df_window.attrs.get("atr", None)
            if atr is not None:
                return max(float(atr), _EPS)

            if "atr" in df_window.columns:
                v = float(df_window["atr"].to_numpy(dtype=float)[-1])
                return max(v, _EPS)

            raise ValueError(
                "normalization_mode='atr' requires external ATR "
                "(df_window.attrs['atr'] or df_window['atr'])."
            )

        raise ValueError(f"Unknown normalization_mode: {self.mode}")


def safe_ratio(x: np.ndarray, denom: float) -> np.ndarray:
    denom = float(denom)
    if not np.isfinite(denom) or abs(denom) < _EPS:
        denom = _EPS
    return x / denom


def ratio_to_mean(x: np.ndarray) -> np.ndarray:
    m = float(np.nanmean(x))
    if not np.isfinite(m) or abs(m) < _EPS:
        m = _EPS
    return x / m

