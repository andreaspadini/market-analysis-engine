from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel

from .volume_profile_stats import VolumeProfileStats


class BalanceClassification(BaseModel):
    balance_standard: bool = False
    balance_wide: bool = False
    balance_compressed: bool = False
    balance_asymmetric: bool = False
    balance_high_volume_center: bool = False
    balance_edge_volume_concentrated: bool = False


class PreBreakoutSignals(BaseModel):
    is_pre_breakout: bool = False
    volatility_pickup: bool = False
    boundary_volume_drop: bool = False
    lvns_near_boundaries: bool = False
    directional_bias: Optional[Literal["up", "down", "neutral"]] = "neutral"
    comment: Optional[str] = None


class BalanceInfo(BaseModel):
    # --- struttura price-based ---
    high: float
    low: float
    mid_price: float
    width: float

    start_time: datetime
    end_time: datetime
    duration_bars: int

    num_rotations: int
    rotation_ids: List[int]  # o List[str] se RotationInfo usa stringhe

    symmetry: float               # 0 = perfetta, >0 sbilanciata
    internal_whipsaw: float       # misura di choppiness interna
    residual_directionality: float
    internal_momentum: float
    up_down_rotation_ratio: float
    range_compression: float

    # --- volume-based ---
    volume_stats: VolumeProfileStats

    # --- classificazione & punteggi ---
    classification: BalanceClassification
    equilibrium_score: float
    pre_breakout_signals: PreBreakoutSignals
