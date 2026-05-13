from __future__ import annotations

from typing import Dict

from engines.root_engine.processing.balance.schema import BalanceModel
from engines.root_engine.processing.breakout.schema import PreBreakoutSignal


class PreBreakoutDetector:
    """
    Calcola il segnale di PRE-BREAKOUT a partire da un BalanceModel.
    """

    def __init__(self, config: Dict):
        # config completo, non solo breakout
        self.cfg = config["breakout"]["pre_breakout"]
        self.weights = self.cfg["weights"]

    def evaluate(self, balance: BalanceModel) -> PreBreakoutSignal:

        # =========================
        # 1. COMPRESSION
        # =========================
        compression_ratio = (
            balance.volatility.compression_ratio
            if balance.volatility is not None
            else 0.0
        )
        compression_score = min(compression_ratio / 1.0, 1.0)

        # =========================
        # 2. LVN PROXIMITY
        # =========================
        if not balance.lvn or balance.range_size == 0:
            lvn_proximity_score = 0.0
        else:
            dist = min(abs(balance.midpoint - lvn) for lvn in balance.lvn)
            norm_dist = dist / balance.range_size
            lvn_proximity_score = 1.0 - min(
                norm_dist / self.cfg["max_lvn_distance"], 1.0
            )

        # =========================
        # 3. VOLATILITY INCREASE
        # =========================
        if balance.avg_candle_range == 0 or balance.volatility is None:
            volatility_score = 0.0
        else:
            vol_score = balance.volatility.internal_volatility / balance.avg_candle_range
            volatility_score = min(
                vol_score / self.cfg["min_volatility_increase"], 1.0
            )

        # =========================
        # 4. DELTA BIAS
        # =========================
        if balance.total_volume == 0:
            delta_bias_score = 0.0
        else:
            delta_ratio = abs(balance.total_delta) / balance.total_volume
            delta_bias_score = min(
                delta_ratio / self.cfg["min_delta_bias"], 1.0
            )

        # =========================
        # TOTAL WEIGHTED SCORE
        # =========================
        total_score = (
            self.weights["compression"] * compression_score +
            self.weights["lvn_proximity"] * lvn_proximity_score +
            self.weights["volatility"] * volatility_score +
            self.weights["delta_bias"] * delta_bias_score
        )

        is_candidate = total_score >= self.cfg["min_score"]

        return PreBreakoutSignal(
            compression_score=compression_score,
            lvn_proximity_score=lvn_proximity_score,
            volatility_score=volatility_score,
            delta_bias_score=delta_bias_score,
            total_score=total_score,
            is_candidate=is_candidate,
        )
