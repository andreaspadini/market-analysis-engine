from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .pipeline_parameters_v1 import DatasetV1
from engines.pattern_engine.pattern_config import PatternConfig


# =========================================================
# Manual Template Mode
# =========================================================

class ManualPatternTolerance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    body_ticks_pct: float = Field(..., gt=0)
    wick_ticks_pct: float = Field(..., gt=0)
    volume_pct: float = Field(..., gt=0)
    delta_pct: float = Field(..., gt=0)


class ManualPatternCandle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(..., ge=1)

    direction: Literal[
        "bullish",
        "bearish",
        "neutral",
        "any",
    ]

    body_ticks: float = Field(..., ge=0)
    upper_wick_ticks: float = Field(..., ge=0)
    lower_wick_ticks: float = Field(..., ge=0)

    volume: Optional[float] = Field(default=None, ge=0)
    delta: Optional[float] = None

    close_position: Optional[
        Literal[
            "near_high",
            "near_low",
            "mid",
            "any",
        ]
    ] = None

class ManualPatternVisualization(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    context_before_bars: int = Field(default=20, ge=0)
    context_after_bars: int = Field(default=40, ge=0)


class ManualTemplatePatternConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["manual_template"]

    tick_size: float = Field(..., gt=0)
    length_bars: int = Field(..., ge=1)

    tolerance: ManualPatternTolerance

    candles: list[ManualPatternCandle] = Field(..., min_length=1)
    visualization: Optional[ManualPatternVisualization] = None


# =========================================================
# Legacy Historical Reference Mode
# =========================================================

class HistoricalReferencePatternConfig(PatternConfig):
    mode: Literal["historical_reference"]


# =========================================================
# Discriminated Union
# =========================================================

PatternRunConfig = Annotated[
    Union[
        ManualTemplatePatternConfig,
        HistoricalReferencePatternConfig,
    ],
    Field(discriminator="mode"),
]


# =========================================================
# Public API Contract
# =========================================================

class PatternRunParametersV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    api_version: str = Field(..., pattern=r"^1\.\d+$")

    dataset: DatasetV1

    config: PatternRunConfig