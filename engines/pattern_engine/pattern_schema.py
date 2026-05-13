from __future__ import annotations

from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field
from pydantic import field_validator, model_validator


# =========================
# Enums
# =========================

class FeatureGroup(str, Enum):
    price = "price"
    volume = "volume"
    delta = "delta"


# =========================
# Helper Models
# =========================

class FeatureSetModel(BaseModel):
    """
    Coerente con Capitolo 2: boolean flags per gruppi feature.
    """
    price: bool = False
    volume: bool = False
    delta: bool = False

    @model_validator(mode="after")
    def at_least_one_enabled(self):
        if not (self.price or self.volume or self.delta):
            raise ValueError(
                "feature_set must enable at least one of: price, volume, delta"
            )
        return self


class ReferenceWindowModel(BaseModel):
    instrument: str
    timeframe: str
    start_ts: datetime
    length_bars: int = Field(..., ge=2)

    @field_validator("start_ts")
    @classmethod
    def ts_must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("start_ts must be timezone-aware (ISO-8601)")
        return v


class DistributionStatsModel(BaseModel):
    mean: float
    median: float
    q25: float
    q75: float
    q90: float

    @model_validator(mode="after")
    def check_quantile_order(self):
        if not (self.q25 <= self.median <= self.q75 <= self.q90):
            raise ValueError("Quantiles must satisfy q25 <= median <= q75 <= q90")
        return self


class LevelProbabilityModel(BaseModel):
    level: float
    probability: float = Field(..., ge=0.0, le=1.0)


class HitRatesModel(BaseModel):
    mfe_levels: List[LevelProbabilityModel] = Field(default_factory=list)
    mae_levels: List[LevelProbabilityModel] = Field(default_factory=list)
    tp_before_sl: Optional[float] = Field(default=None, ge=0.0, le=1.0)


# =========================
# Domain Models
# =========================

class PatternDefinitionModel(BaseModel):
    """
    Pattern definito dallâ€™utente (metadati/contratto), coerente con config Capitolo 2.
    """
    pattern_id: str
    length_bars: int = Field(..., ge=2)
    timeframe: str
    instrument: str

    reference_window: ReferenceWindowModel

    normalization_mode: str

    feature_set: FeatureSetModel

    # accetta chiavi stringa "price"|"volume"|"delta"
    weights: Optional[Dict[str, float]] = None
    distance_caps: Optional[Dict[str, float]] = None

    engine_version: str
    run_id: Optional[str] = None
    config_snapshot_sha256: Optional[str] = None

    @model_validator(mode="after")
    def check_reference_window_coherence(self):
        rw = self.reference_window

        if rw.length_bars != self.length_bars:
            raise ValueError("reference_window.length_bars must match length_bars")

        if rw.instrument != self.instrument:
            raise ValueError("reference_window.instrument must match instrument")

        if rw.timeframe != self.timeframe:
            raise ValueError("reference_window.timeframe must match timeframe")

        return self

    @field_validator("weights", mode="before")
    @classmethod
    def coerce_weight_keys_to_str(cls, v):
        if v is None:
            return v
        if not isinstance(v, dict):
            raise TypeError("weights must be a mapping {feature_name: float}")
        return {str(k): v[k] for k in v}

    @field_validator("weights")
    @classmethod
    def validate_and_normalize_weights(cls, v, info):
        if v is None:
            return v

        fs: FeatureSetModel = info.data.get("feature_set")
        if fs is None:
            return v

        allowed = {fg.value for fg in FeatureGroup}

        for k, w in v.items():
            if k not in allowed:
                raise ValueError(
                    f"weights key '{k}' must be one of: {sorted(allowed)}"
                )
            if w < 0:
                raise ValueError("Weights must be non-negative")

            enabled = getattr(fs, k)
            if (not enabled) and w > 0:
                raise ValueError(
                    f"Weight for disabled feature '{k}' must be 0 or omitted"
                )

        active = {k: w for k, w in v.items() if getattr(fs, k) and w > 0}
        if not active:
            raise ValueError(
                "Weights must include at least one positive weight on enabled features"
            )

        total = sum(active.values())
        if total <= 0:
            raise ValueError(
                "Weights must sum to a positive value on enabled features"
            )

        normalized = {k: w / total for k, w in active.items()}

        # manteniamo eventuali zeri espliciti
        for k, w in v.items():
            if k not in normalized and w == 0:
                normalized[k] = 0.0

        return normalized


class PatternMatchModel(BaseModel):
    pattern_id: str

    instrument: str
    timeframe: str

    start_ts: datetime
    end_ts: datetime

    start_bar_index: Optional[int] = None
    session_name: Optional[str] = None

    similarity_score: float = Field(..., ge=0.0, le=1.0)

    distance_components: Optional[Dict[FeatureGroup, float]] = None
    feature_summary: Optional[Dict[str, float]] = None

    engine_version: str
    run_id: str

    @field_validator("start_ts", "end_ts")
    @classmethod
    def ts_must_be_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("Timestamps must be timezone-aware (ISO-8601)")
        return v

    @model_validator(mode="after")
    def check_time_order(self):
        if self.end_ts <= self.start_ts:
            raise ValueError("end_ts must be strictly greater than start_ts")
        return self

    @field_validator("distance_components")
    @classmethod
    def distance_components_non_negative(cls, v):
        if v is None:
            return v
        for value in v.values():
            if value < 0:
                raise ValueError("distance_components must be non-negative")
        return v

    def to_row(self) -> Dict[str, object]:
        """
        Flat representation suitable for CSV / Parquet.
        """
        row = self.model_dump()

        # rimuoviamo sempre i campi raw opzionali
        row.pop("distance_components", None)
        row.pop("feature_summary", None)

        if self.distance_components:
            for k, v in self.distance_components.items():
                row[f"distance_{k}"] = v

        return row


class PatternStatsModel(BaseModel):
    pattern_id: str
    instrument: str
    timeframe: str

    horizon_bars: int = Field(..., ge=1)
    n_occurrences: int = Field(..., ge=1)

    long_mfe: DistributionStatsModel
    long_mae: DistributionStatsModel
    short_mfe: DistributionStatsModel
    short_mae: DistributionStatsModel

    hit_rates: Optional[HitRatesModel] = None

    def to_row(self) -> Dict[str, object]:
        """
        Flattened representation for tabular storage.
        """
        base = {
            "pattern_id": self.pattern_id,
            "instrument": self.instrument,
            "timeframe": self.timeframe,
            "horizon_bars": self.horizon_bars,
            "n_occurrences": self.n_occurrences,
        }

        def flatten(prefix: str, d: DistributionStatsModel) -> Dict[str, float]:
            return {
                f"{prefix}_mean": d.mean,
                f"{prefix}_median": d.median,
                f"{prefix}_q25": d.q25,
                f"{prefix}_q75": d.q75,
                f"{prefix}_q90": d.q90,
            }

        base.update(flatten("long_mfe", self.long_mfe))
        base.update(flatten("long_mae", self.long_mae))
        base.update(flatten("short_mfe", self.short_mfe))
        base.update(flatten("short_mae", self.short_mae))

        if self.hit_rates:
            for lp in self.hit_rates.mfe_levels:
                base[f"hit_mfe_ge_{lp.level}"] = lp.probability
            for lp in self.hit_rates.mae_levels:
                base[f"hit_mae_le_{lp.level}"] = lp.probability
            if self.hit_rates.tp_before_sl is not None:
                base["hit_tp_before_sl"] = self.hit_rates.tp_before_sl

        return base


# =========================
# Schema Export
# =========================

def export_schema_json(path: str) -> None:
    import json

    schema = {
        "PatternDefinitionModel": PatternDefinitionModel.model_json_schema(),
        "PatternMatchModel": PatternMatchModel.model_json_schema(),
        "PatternStatsModel": PatternStatsModel.model_json_schema(),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    
