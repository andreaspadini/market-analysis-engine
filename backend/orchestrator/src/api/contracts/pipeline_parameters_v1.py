from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator

from engines.pattern_engine.pattern_config import PatternConfig


# -------------------------
# DATASET
# -------------------------

class DatasetV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    instruments: List[str]
    timeframe: str
    start_date: str
    end_date: str


# -------------------------
# ROOT ENGINE (1:1 root_config.yaml, EXCLUDING engine_version)
# -------------------------


class Root_Rotations(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    merge_same_direction: bool
    whipsaw_bars: int
    min_rotation_bars: int
    min_rotation_amplitude: float

    min_rotation_amplitude_micro: float
    min_rotation_amplitude_standard: float
    min_rotation_amplitude_structural: float



class Root_Balance_Volume_Profile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    bin_size: float
    hvn_threshold_factor: float
    lvn_threshold_factor: float
    window_around_poc: float
    window_around_mid: float


class Root_Balance_Classification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    compressed_width_factor: float
    wide_width_factor: float
    asymmetry_threshold: float
    center_volume_threshold: float
    edge_volume_threshold: float
    hvn_density_threshold: float
    lvn_density_threshold: float

class Root_Balance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    min_rotations: int
    max_gap_bars: int
    min_bars: int
    min_width: float
    max_width: float

    volume_profile: Root_Balance_Volume_Profile
    classification: Root_Balance_Classification


# ----- Breakout subtree (complete 1:1) -----

class Root_Breakout_EarlyDetection_Trigger(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    type: str
    min_consecutive: int
    min_penetration: float

class Root_Breakout_EarlyDetection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enabled: bool
    lower_timeframe: str
    reference_timeframe: str
    max_lead_minutes: int
    trigger: Root_Breakout_EarlyDetection_Trigger

class Root_Breakout_Classification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    failure_retrace_factor: float
    retest_window: int
    accumulation_bars: int
    min_progress_factor: float


class Root_Breakout_Strength(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    momentum_weight: float
    delta_weight: float
    volume_spike_weight: float
    volatility_weight: float
    distance_from_vpoc_weight: float
    hvn_lvn_break_weight: float


class Root_Breakout_StrengthNormalization(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enabled: bool
    method: str
    min_raw: float
    max_raw: float
    sigmoid_k: float


class Root_Breakout_ATR(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enabled: bool
    period: int
    normalization_factor: float


class Root_Breakout_VolatilityFilter(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enable_filter: bool
    min_compression_ratio: float
    max_compression_ratio: float
    min_stability_score: float
    soft_penalty: float


class Root_Breakout_FollowThrough(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    observation_bars: int

class Root_Breakout_Rotations(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    require_structural_rotation: bool



class Root_Breakout_RotationsFilter(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    min_rotations: int
    min_directional_bias: float

class Root_Breakout_Confirmation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enabled: bool
    max_bars: int
    closes_required: int
    delta_confirmation: bool
    delta_min_abs: float


class Root_Breakout(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    early_detection: Root_Breakout_EarlyDetection
    mode: str
    post_balance_bars: int
    confirmation: Root_Breakout_Confirmation
    classification: Root_Breakout_Classification
    strength: Root_Breakout_Strength
    strength_normalization: Root_Breakout_StrengthNormalization
    atr: Root_Breakout_ATR
    volatility_filter: Root_Breakout_VolatilityFilter
    follow_through: Root_Breakout_FollowThrough
    rotations_filter: Root_Breakout_RotationsFilter
    rotations: Root_Breakout_Rotations



class Root_SessionLevels_Session(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    open_time: str
    close_time: str
    region: str
    enabled: bool
    timezone: str


class Root_SessionLevels_Sessions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    Asia: Root_SessionLevels_Session
    Europe: Root_SessionLevels_Session
    US: Root_SessionLevels_Session


class Root_SessionLevels_VolumeProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    bin_size: float
    value_area_pct: float


class Root_SessionLevels_VWAP(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enabled: bool


class Root_SessionLevels(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: str
    sessions: Root_SessionLevels_Sessions
    volume_profile: Root_SessionLevels_VolumeProfile
    vwap: Root_SessionLevels_VWAP


class RootEngineConfigV1(BaseModel):
    """
    Source: root_config.yaml
    NOTE: engine_version is EXCLUDED by contract (M2 explicit exclusions).
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    
    rotations: Root_Rotations
    balance: Root_Balance
    breakout: Root_Breakout
    session_levels: Root_SessionLevels


# -------------------------
# STATISTICAL ENGINE (1:1 statistical config.yaml pasted)
# -------------------------

NumRange = Tuple[float, float]
IntRange = Tuple[int, int]
TimeRange = Tuple[str, str]


class Stat_Target_Primary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str
    atr_multiplier: float


class Stat_Target_Secondary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str
    ticks: int


class Stat_Targets(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    primary: Stat_Target_Primary
    secondary: Stat_Target_Secondary


class Stat_TargetScan_XScan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    start: float
    end: float
    step: float


class Stat_TargetScan_SuccessATRScan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    base_target: str
    x_scan: Stat_TargetScan_XScan


class Stat_TargetScans(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    success_ATR_scan: Stat_TargetScan_SuccessATRScan


class Stat_TickScan_SuccessTicks(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    levels: List[int]


class Stat_TickScan_CleanTicks(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    levels: List[int]


class Stat_TickScan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tick_size: float
    success_ticks: Stat_TickScan_SuccessTicks
    clean_ticks: Stat_TickScan_CleanTicks


class Stat_CleanQuant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    base_target: str
    clean_atr_threshold: float



class Stat_Bucketizers_CompressionBucket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    ultra_compressed_max: float
    compressed_max: float
    balanced_max: float
    expanded_max: float


class Stat_Bucketizers_DeltaBucket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    delta_0_100_max: int
    delta_100_300_max: int
    delta_300_600_max: int
    delta_600_1000_max: int


class Stat_Bucketizers_VolumeBucket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    very_low_max: int
    low_max: int
    medium_max: int
    high_max: int


class Stat_Bucketizers_ATRBucket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    atr_0_0_5_max: float
    atr_0_5_1_0_max: float
    atr_1_0_1_5_max: float
    atr_1_5_2_5_max: float


class Stat_Bucketizers_PreBoBucket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    pre_neg_max: float
    pre_0_2_max: float
    pre_2_4_max: float
    pre_4_6_max: float


class Stat_Bucketizers_TimeBucket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tb_00_04_max: float
    tb_04_08_max: float
    tb_08_12_max: float
    tb_12_16_max: float
    tb_16_20_max: float
    tb_20_24_max: float


class Stat_Bucketizers(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    compression_bucket: Optional[Stat_Bucketizers_CompressionBucket] = None
    delta_bucket: Optional[Stat_Bucketizers_DeltaBucket] = None
    volume_bucket: Optional[Stat_Bucketizers_VolumeBucket] = None
    atr_bucket: Optional[Stat_Bucketizers_ATRBucket] = None
    pre_bo_bucket: Optional[Stat_Bucketizers_PreBoBucket] = None
    time_bucket: Optional[Stat_Bucketizers_TimeBucket] = None



class StatisticalConfigV1(BaseModel):
    """
    Canonical Statistical config accepted by /runs/statistical.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    targets: Stat_Targets
    target_scans: Stat_TargetScans
    tick_scan: Stat_TickScan
    clean_quant: Stat_CleanQuant
    bucketizers: Optional[Stat_Bucketizers] = None

class StatisticalEngineConfigV1(BaseModel):
    """
    M2 Contract: strict + coverage completa dei 4 file:
    - statistical_engine/config/config.yaml   -> config
    - statistical_engine/config/mapping.yml   -> mapping
    - statistical_engine/config/sessions.yml  -> sessions_def
    - statistical_engine/config/targets.yml   -> targets_def
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    config: StatisticalConfigV1
    mapping: Stat_Mapping_V1
    sessions_def: Stat_Sessions_Definition_V1
    targets_def: Stat_Targets_Definition_V1

# -------------------------
# STATISTICAL: mapping.yml (1:1)
# -------------------------

class Stat_Mapping_V1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str

    core_fields: Dict[str, str]
    directional: Dict[str, str]
    prices: Dict[str, str]
    balance_structure: Dict[str, str]
    volume_delta_volatility: Dict[str, str]
    strength_follow: Dict[str, str]
    rotations: Dict[str, str]
    pre_breakout: Dict[str, str]
    ranking: Dict[str, str]
    meta: Dict[str, str]


# -------------------------
# STATISTICAL: sessions.yml (1:1)
# -------------------------

class Stat_SessionWindow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    start: str
    end: str


class Stat_Sessions_Definition_V1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    timezone: str
    sessions: Dict[str, Stat_SessionWindow]
    fallback_session: str


# -------------------------
# STATISTICAL: targets.yml (1:1)
# -------------------------

class Stat_Targets_BaseMetrics_MaxExcursionSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    field: str
    key: str


class Stat_Targets_BaseMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    max_excursion_source: Stat_Targets_BaseMetrics_MaxExcursionSource
    atr_source: Dict[str, str]  # { field: atr_before }


class Stat_Targets_XScan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    start: float
    end: float
    step: float


class Stat_TargetDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str
    type: str
    logic: str
    enabled: bool

    # opzionali (presenti solo su alcuni target)
    threshold_type: Optional[str] = None
    clean_label: Optional[str] = None
    x_scan: Optional[Stat_Targets_XScan] = None


class Stat_FailureDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    field: str
    true_value: bool


class Stat_Targets_Definition_V1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    base_metrics: Stat_Targets_BaseMetrics
    targets: Dict[str, Stat_TargetDefinition]
    failure_definition: Stat_FailureDefinition

# -------------------------
# QUERY ENGINE (M2 PROVISIONAL STRICT)
# -------------------------

class QueryEngineConfigV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    intent_id: str
    params: Dict[str, Any]


# -------------------------
# ENGINES WRAPPER
# -------------------------

class EnginesV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    root: RootEngineConfigV1
    statistical: StatisticalEngineConfigV1
    pattern: Optional[PatternConfig] = None
    query: QueryEngineConfigV1

# -------------------------
# TOP LEVEL
# -------------------------

class PipelineParametersV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    api_version: str = Field(..., pattern=r"^1\.\d+$")
    dataset: DatasetV1
    engines: EnginesV1

    @field_validator("api_version")
    @classmethod
    def _api_version_must_be_1x(cls, v: str) -> str:
        if not v.startswith("1."):
            raise ValueError("api_version must be 1.*")
        return v


__all__ = [
    "PipelineParametersV1",
    "DatasetV1",
    "EnginesV1",
    "RootEngineConfigV1",
    "StatisticalEngineConfigV1",
    "QueryEngineConfigV1",
]