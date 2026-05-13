from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class BreakoutDirection(str):
    UP = "up"
    DOWN = "down"


class BreakoutType(str):
    CLEAN = "clean"                      # breakout pulito
    DIRTY = "dirty"                      # breakout con “sporco” / rientri
    FALSE = "false_breakout"             # falsa rottura, rientra subito
    FAILED = "failed_follow_through"     # confermato ma senza continuazione
    WITH_RETEST = "with_retest"          # breakout + retest sul bordo
    ACCUMULATION = "accumulation"        # base di accumulo/distribuzione post-breakout


class BreakoutConfirmationStatus(str):
    PENDING = "pending"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"


class BreakoutStrengthComponents(BaseModel):
    momentum_score: float
    delta_imbalance_score: float
    volume_spike_score: float
    volatility_score: float
    distance_from_vpoc_score: float
    hvn_lvn_break_score: float

    overall_strength_score: float
    overall_strength_normalized: float  # 0–1 (o simile)

    # usato dal BreakoutDetector._compute_strength_components
    volatility_filter_pass: bool = True


class FollowThroughMetrics(BaseModel):
    max_excursion: float                     # distanza max dal prezzo di breakout
    max_excursion_bars: int                  # barre per raggiungerla
    close_after_n_bars: float                # close dopo N barre
    retracement_depth: float                 # profondità max ritracciamento
    retracement_bars: int
    time_to_retest_boundary: Optional[int]   # barre al primo retest
    boundary_hold_bars: Optional[int]        # barre in cui regge il boundary
    failure_price: Optional[float]           # livello dove consideriamo il fallimento
    failure_bars_from_breakout: Optional[int]
    post_breakout_volatility: float          # ATR/vol post-breakout
    post_breakout_volume_mean: float         # volume medio post-breakout


class PostBreakoutVolumeProfile(BaseModel):
    vpoc: float
    hvn: List[float]
    lvn: List[float]
    skewness: float
    kurtosis: float
    concentration: float
    asymmetry: float
    edge_volume: float
    range_width: float


class PreBreakoutSignal(BaseModel):
    compression_score: float
    lvn_proximity_score: float
    volatility_score: float
    delta_bias_score: float
    total_score: float
    is_candidate: bool


class BreakoutModel(BaseModel):
    breakout_id: str
    parent_balance_id: str
    instrument: str
    symbol: Optional[str] = None
    session_id: str
    timeframe: str

    breakout_time: datetime
    breakout_bar_index: int
    confirmation_time: Optional[datetime] = None
    confirmation_bar_index: Optional[int] = None
    computation_timestamp: datetime
    version: str = "0.2.1"


    direction: str
    breakout_type: str
    confirmation_status: str

    breakout_price: float
    confirmation_price: Optional[float] = None

    boundary_price: float
    boundary_type: str

    balance_high: float
    balance_low: float
    balance_midpoint: float
    balance_range_size: float
    balance_vpoc: float
    balance_hvn: Optional[List[float]] = None
    balance_lvn: Optional[List[float]] = None
    balance_equilibrium_score: Optional[float] = None
    balance_rotation_quality_score: Optional[float] = None
    balance_structural_integrity_score: Optional[float] = None

    initial_volume: float
    initial_volume_zscore: Optional[float] = None
    initial_delta: float
    delta_peak: Optional[float] = None
    delta_mean_post_breakout: Optional[float] = None

    atr_before: Optional[float] = None
    atr_after: Optional[float] = None

    strength_components: BreakoutStrengthComponents
    follow_through: FollowThroughMetrics
    post_breakout_volume_profile: Optional[PostBreakoutVolumeProfile] = None

    bar_count_initial_move: int

    # ==== CAMPI CHE TI MANCANO ORA ====
    bars_observed: int
    is_failed: bool
    is_retest_occurred: bool

    config_snapshot: Dict
    tags: List[str] = []
    notes: Optional[str] = None

    early_time: Optional[datetime] = None
    early_price: Optional[float] = None
    early_bar_index: Optional[int] = None
    early_timeframe: Optional[str] = None
    minutes_of_anticipation: Optional[float] = None

    rotation_context: Optional[Dict[str, Any]] = None
    pre_breakout_signal: Optional[PreBreakoutSignal] = None

    global_rank: Optional[int] = None
    session_rank: Optional[int] = None


