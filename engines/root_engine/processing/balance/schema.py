from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class RotationInfo(BaseModel):
    index: int
    direction: str
    start_time: datetime
    end_time: datetime
    start_price: float
    end_price: float
    amplitude: float
    volume: float
    delta: float
    validity_flag: bool
    rotation_type: str  # "micro" | "standard" | "structural"


class VolumeProfileSlice(BaseModel):
    price: float
    volume: float
    delta: float
    bid: float
    ask: float
    participation_rate: Optional[float] = None
    anomaly_flag: bool = False


class VolatilityMetrics(BaseModel):
    internal_volatility: float
    volatility_spikes: List[float]
    compression_ratio: float
    stability_score: float


class EdgeCaseSignals(BaseModel):
    spike_detected: bool = False
    abnormal_gap_detected: bool = False
    volume_distortion_detected: bool = False
    broken_structure_detected: bool = False
    rotation_quality_issue: bool = False
    session_interrupt_flag: bool = False
    pattern_incoherence_flag: bool = False
    metadata: Dict[str, float] = {}


class BalanceModel(BaseModel):
    # Identificativi principali
    balance_id: str
    instrument: str
    symbol: Optional[str] = None
    session_id: str
    timeframe: str

    # Timeline
    start_time: datetime
    end_time: datetime
    duration_seconds: int

    # Range e struttura
    high: float
    low: float
    midpoint: float
    range_size: float
    effective_range_size: Optional[float] = None

    # Rotazioni
    rotations: List[RotationInfo]
    total_rotations: int
    valid_rotations: int
    rotation_quality_score: float
    bars_count: int

    # Volatilità e compressione
    volatility: VolatilityMetrics
    avg_candle_range: float
    relative_volatility_rank: float

    # Volume e delta profile
    volume_profile: List[VolumeProfileSlice]
    total_volume: float
    total_delta: float
    vpoc: float
    hvn: Optional[List[float]] = None
    lvn: Optional[List[float]] = None
    volume_symmetry_score: float

    # Gap e contesto sessione
    session_gap: float
    contextual_gap: float
    session_interruption_windows: List[Dict]

    # Coerenza interna
    structural_integrity_score: float
    compression_validity_flag: bool
    balance_validity_flag: bool

    # Edge cases & meta
    edge_cases: EdgeCaseSignals
    config_snapshot: Dict
    computation_timestamp: datetime
    version: str = "0.2.1"

