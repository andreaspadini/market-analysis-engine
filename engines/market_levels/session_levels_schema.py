from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from market_analysis_engine import ENGINE_VERSION


class SessionLevelsModel(BaseModel):
    """
    Riga di output per i livelli di mercato (sessione + contesto daily/weekly/monthly).
    Ogni riga = 1 giorno x 1 sessione.
    """

    # --- Chiavi di base ---
    date: date
    instrument: str = "unknown"
    symbol: Optional[str] = None

    # --- Info sessione ---
    session_name: str  # es: "asia", "eu", "us"
    session_start: datetime
    session_end: datetime

    session_high: Optional[float] = None
    session_low: Optional[float] = None
    session_open: Optional[float] = None
    session_close: Optional[float] = None
    session_midpoint: Optional[float] = None
    session_range: Optional[float] = None

    session_poc: Optional[float] = None
    session_vah: Optional[float] = None
    session_val: Optional[float] = None
    session_vwap: Optional[float] = None

    # --- Daily context (giorno corrente / precedente) ---
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    day_midpoint: Optional[float] = None
    day_range: Optional[float] = None

    day_poc: Optional[float] = None
    day_vah: Optional[float] = None
    day_val: Optional[float] = None
    day_vwap: Optional[float] = None

    prev_day_high: Optional[float] = None
    prev_day_low: Optional[float] = None
    prev_day_poc: Optional[float] = None
    prev_day_vah: Optional[float] = None
    prev_day_val: Optional[float] = None
    prev_day_vwap: Optional[float] = None

    # --- Weekly context (nuovo) ---
    weekly_high: Optional[float] = None
    weekly_low: Optional[float] = None
    weekly_vwap: Optional[float] = None
    # placeholder per future estensioni (per ora li lasciamo None)
    weekly_poc: Optional[float] = None
    weekly_vah: Optional[float] = None
    weekly_val: Optional[float] = None

    # --- Monthly context (nuovo) ---
    monthly_high: Optional[float] = None
    monthly_low: Optional[float] = None
    monthly_vwap: Optional[float] = None
    # placeholder per future estensioni
    monthly_poc: Optional[float] = None
    monthly_vah: Optional[float] = None
    monthly_val: Optional[float] = None

    # --- Metadati / vari ---
    computation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default=ENGINE_VERSION)
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


