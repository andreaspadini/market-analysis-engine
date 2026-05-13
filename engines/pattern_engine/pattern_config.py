# pattern_engine/pattern_config.py  (Pydantic v2.x)

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, PrivateAttr, ConfigDict, field_validator, model_validator

try:
    import yaml  # PyYAML
except Exception:  # pragma: no cover
    yaml = None

import json


# -----------------------------
# Helpers
# -----------------------------
def _parse_dt(v) -> datetime:
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        s = v.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    raise TypeError("Invalid datetime value")


def _dt_to_iso(v):
    if isinstance(v, datetime):
        s = v.isoformat()
        if s.endswith("+00:00"):
            s = s[:-6] + "Z"
        return s
    return v


def _to_json_friendly(obj):
    if isinstance(obj, dict):
        return {k: _to_json_friendly(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_json_friendly(x) for x in obj]
    return _dt_to_iso(obj)


def _sum_positive(values: List[float]) -> float:
    return float(sum(max(0.0, x) for x in values))


# -----------------------------
# Blocks
# -----------------------------
class PatternEngineBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    timeframe: str


class DateRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: datetime
    end: datetime

    @field_validator("start", mode="before")
    @classmethod
    def _parse_start(cls, v):
        return _parse_dt(v)

    @field_validator("end", mode="before")
    @classmethod
    def _parse_end(cls, v):
        return _parse_dt(v)

    @model_validator(mode="after")
    def _check_range(self):
        if self.start > self.end:
            raise ValueError("universe.date_range.start must be <= universe.date_range.end")
        return self


class UniverseBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instruments: List[str] = Field(..., min_length=1)
    date_range: DateRange

    @field_validator("instruments")
    @classmethod
    def _strip_and_unique(cls, v: List[str]):
        cleaned = [str(s).strip() for s in v if str(s).strip()]
        if not cleaned:
            raise ValueError("universe.instruments must contain at least 1 non-empty instrument")
        seen = set()
        out = []
        for x in cleaned:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out


class ReferenceWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument: str
    timeframe: str
    start_ts: datetime
    length_bars: int = Field(..., ge=2)

    @field_validator("start_ts", mode="before")
    @classmethod
    def _parse_start_ts(cls, v):
        return _parse_dt(v)

    @field_validator("instrument", "timeframe")
    @classmethod
    def _nonempty(cls, v):
        s = str(v).strip()
        if not s:
            raise ValueError("reference_window.instrument/timeframe cannot be empty")
        return s


class FeatureSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price: bool = True
    volume: bool = False
    delta: bool = False

    @model_validator(mode="after")
    def _at_least_one_enabled(self):
        if not any([self.price, self.volume, self.delta]):
            raise ValueError("pattern.feature_set must enable at least one of: price, volume, delta")
        return self


class Weights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price: float = Field(0.0, ge=0.0)
    volume: float = Field(0.0, ge=0.0)
    delta: float = Field(0.0, ge=0.0)


class DistanceCaps(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price: float = Field(..., gt=0.0)
    volume: float = Field(..., gt=0.0)
    delta: float = Field(..., gt=0.0)


NormalizationMode = Literal["pattern_mean_range", "first_bar_range", "atr"]
ExportFormat = Literal["parquet", "csv", "jsonl"]


class PatternBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    length_bars: int = Field(..., ge=2)
    reference_window: ReferenceWindow
    normalization_mode: NormalizationMode = "pattern_mean_range"
    feature_set: FeatureSet = Field(default_factory=FeatureSet)
    weights: Weights = Field(default_factory=Weights)

    # computed-only (non input / non user-facing)
    _normalized_weights: Optional[Weights] = PrivateAttr(default=None)
    _effective_weights: Optional[Weights] = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _validate_pattern_lengths(self):
        if self.reference_window.length_bars != self.length_bars:
            raise ValueError("pattern.length_bars must equal pattern.reference_window.length_bars")
        return self

    def compute_effective_and_normalized_weights(self) -> Tuple[Weights, Weights]:
        """
        Returns (effective_weights, normalized_weights), computed using feature_set.
        effective_weights: disabled channels forced to 0 (ignored).
        normalized_weights: renormalized across enabled channels, sum=1 over enabled.
        """
        fs = self.feature_set
        w = self.weights

        price_w = float(w.price or 0.0) if fs.price else 0.0
        volume_w = float(w.volume or 0.0) if fs.volume else 0.0
        delta_w = float(w.delta or 0.0) if fs.delta else 0.0

        enabled = []
        if fs.price:
            enabled.append(price_w)
        if fs.volume:
            enabled.append(volume_w)
        if fs.delta:
            enabled.append(delta_w)

        if _sum_positive(enabled) <= 0.0:
            raise ValueError("pattern.weights: at least one enabled feature weight must be > 0")

        s = float(sum(enabled))
        norm_price = (price_w / s) if fs.price else 0.0
        norm_volume = (volume_w / s) if fs.volume else 0.0
        norm_delta = (delta_w / s) if fs.delta else 0.0

        eff = Weights(price=price_w, volume=volume_w, delta=delta_w)
        norm = Weights(price=norm_price, volume=norm_volume, delta=norm_delta)

        self._effective_weights = eff
        self._normalized_weights = norm
        return eff, norm


class SimilarityBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tolerance: float = Field(..., gt=0.0, le=1.0)
    distance_caps: DistanceCaps

    @field_validator("tolerance")
    @classmethod
    def _tolerance_bounds(cls, v):
        v = float(v)
        if not (0.0 < v <= 1.0):
            raise ValueError("similarity.tolerance must be in (0, 1]")
        return v


class OutcomeBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    horizon_bars: int = Field(..., ge=1)
    targets_ticks: List[int] = Field(..., min_length=1)
    stops_ticks: List[int] = Field(..., min_length=1)
    compute_atr_multiples: bool = False

    @field_validator("targets_ticks", "stops_ticks")
    @classmethod
    def _ticks_positive(cls, v, info):
        vv = [int(x) for x in v]
        if any(x <= 0 for x in vv):
            raise ValueError(f"outcome.{info.field_name} must contain only positive integers")
        seen = set()
        out = []
        for x in vv:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out


class ExportBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_dir: str
    format: ExportFormat = "parquet"

    @field_validator("output_dir")
    @classmethod
    def _output_dir_nonempty(cls, v):
        s = str(v).strip()
        if not s:
            raise ValueError("export.output_dir cannot be empty")
        return s


class PatternConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern_engine: PatternEngineBlock
    universe: UniverseBlock
    pattern: PatternBlock
    similarity: SimilarityBlock
    outcome: OutcomeBlock
    export: ExportBlock

    @model_validator(mode="after")
    def _cross_checks(self):
        # vincolo MVP: timeframe coerenza engine vs reference window
        if self.pattern_engine.timeframe != self.pattern.reference_window.timeframe:
            raise ValueError(
                "pattern_engine.timeframe must match pattern.reference_window.timeframe (MVP constraint)"
            )

        # enforce weights logic now (but do NOT mutate input fields)
        self.pattern.compute_effective_and_normalized_weights()
        return self

    # -----------------------------
    # IO helpers (MVP compliant)
    # -----------------------------
    @classmethod
    def load_yaml(cls, path: str | Path) -> Tuple["PatternConfig", str]:
        """
        Returns (validated_config, raw_text).
        raw_text is the source-of-truth snapshot for audit/repro.
        """
        if yaml is None:
            raise RuntimeError("PyYAML is required to load YAML (pip install pyyaml).")
        p = Path(path)
        raw_text = p.read_text(encoding="utf-8")
        data = yaml.safe_load(raw_text)
        return cls.model_validate(data), raw_text

    @staticmethod
    def save_config_snapshot_raw(path: str | Path, raw_text: str) -> None:
        """
        Writes the original YAML exactly as provided (source-of-truth).
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(raw_text, encoding="utf-8")

    def to_resolved_dict(self) -> dict:
        """
        Runtime-friendly dict:
        - keeps original user fields
        - adds computed effective/normalized weights under pattern.resolved.*
        """
        base = self.model_dump()
        eff, norm = self.pattern.compute_effective_and_normalized_weights()

        base.setdefault("pattern", {})
        base["pattern"].setdefault("resolved", {})
        base["pattern"]["resolved"]["effective_weights"] = eff.model_dump()
        base["pattern"]["resolved"]["normalized_weights"] = norm.model_dump()
        return base

    def save_config_resolved(self, path: str | Path) -> None:
        """
        Writes a resolved YAML with deterministic datetime formatting (ISO strings).
        """
        if yaml is None:
            raise RuntimeError("PyYAML is required to dump YAML (pip install pyyaml).")
        resolved = _to_json_friendly(self.to_resolved_dict())

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            yaml.safe_dump(resolved, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    @classmethod
    def export_json_schema(cls, path: str | Path, indent: int = 2) -> None:
        """
        JSON schema for user-facing config (computed fields are excluded).
        """
        schema = cls.model_json_schema()
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(schema, indent=indent, ensure_ascii=False), encoding="utf-8")
