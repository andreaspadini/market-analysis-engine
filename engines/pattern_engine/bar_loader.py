from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, Type

import pandas as pd


# =============================================================================
# Exceptions
# =============================================================================

class BarLoaderError(RuntimeError):
    """Base error for bar loading failures."""


class UnsupportedTimeframeError(BarLoaderError):
    """Unsupported or invalid timeframe format."""
    pass


class UnsupportedInstrumentError(BarLoaderError):
    """Instrument not supported by the data source."""
    pass


class NoDataError(BarLoaderError):
    """No data available for the requested range/instrument."""
    pass


class DataSchemaError(BarLoaderError):
    """Invalid or inconsistent bar data schema."""
    pass


# -----------------------------------------------------------------------------
# Backward-compatibility aliases (required by tests)
# -----------------------------------------------------------------------------
BarDataError = BarLoaderError
BarDataNotFoundError = NoDataError


# =============================================================================
# Contracts / constants
# =============================================================================
REQUIRED_COLS = ["timestamp", "open", "high", "low", "close", "volume"]
OPTIONAL_COLS = ["delta"]


def _require_tz_aware_timestamp(df: pd.DataFrame) -> None:
    if "timestamp" not in df.columns:
        raise DataSchemaError("missing required column: timestamp")

    ts = df["timestamp"]
    if not pd.api.types.is_datetime64_any_dtype(ts):
        raise DataSchemaError("timestamp is not a datetime dtype")

    # tz-aware check (works for pandas datetime64[ns, tz])
    if getattr(ts.dt, "tz", None) is None:
        raise DataSchemaError("timestamp is not timezone-aware (tz missing)")


def _validate_required_columns(df: pd.DataFrame) -> None:
    for c in REQUIRED_COLS:
        if c not in df.columns:
            raise DataSchemaError(f"missing required column: {c}")


def _validate_no_nan_ohlcv(df: pd.DataFrame) -> None:
    if df[["open", "high", "low", "close", "volume"]].isna().any().any():
        raise DataSchemaError("NaN detected in OHLCV columns")


def _validate_sorted_unique_timestamp(df: pd.DataFrame) -> None:
    if not df["timestamp"].is_monotonic_increasing:
        raise DataSchemaError("timestamp is not sorted ascending")
    if df["timestamp"].duplicated().any():
        raise DataSchemaError("timestamp has duplicates")


def _validate_ohlc_sanity(df: pd.DataFrame) -> None:
    max_oc = df[["open", "close"]].max(axis=1)
    min_oc = df[["open", "close"]].min(axis=1)

    if (df["high"] < max_oc).any():
        raise DataSchemaError("OHLC sanity failed: high < max(open, close) on some rows")
    if (df["low"] > min_oc).any():
        raise DataSchemaError("OHLC sanity failed: low > min(open, close) on some rows")


def _validate_timeframe_format(timeframe: str) -> None:
    """
    Minimal "support check" without hardcoding instruments/timeframes lists.
    Accepts formats like: 1m, 5m, 15m, 1h, 4h, 1d, 30s.
    """
    if not isinstance(timeframe, str) or not timeframe:
        raise UnsupportedTimeframeError("timeframe must be a non-empty string")

    # Very small validator: <int><unit>
    unit = timeframe[-1]
    num = timeframe[:-1]
    if unit not in ("s", "m", "h", "d"):
        raise UnsupportedTimeframeError(f"unsupported timeframe unit: {timeframe!r}")
    if not num.isdigit() or int(num) <= 0:
        raise UnsupportedTimeframeError(f"invalid timeframe value: {timeframe!r}")


# =============================================================================
# Data source protocol
# =============================================================================
class BarsSource(Protocol):
    def fetch(
        self,
        instrument: str,
        timeframe: str,
        start_ts: datetime,
        end_ts: datetime,
    ) -> pd.DataFrame:
        ...


# =============================================================================
# Central project data layer source (DataPipeline)
# =============================================================================
@dataclass(frozen=True)
class CentralPipelineBarsSource:
    """
    Adapter over the central data layer (market_analysis_engine.market_data.pipeline.DataPipeline).

    IMPORTANT: Pattern Engine does not create new formats/pipelines.
    This class only *wraps* the existing DataPipeline and normalizes output.
    """
   
    config: Dict[str, Any]
    pipeline_cls: Optional[Type[Any]] = None

    def _get_pipeline_cls(self) -> Type[Any]:
        if self.pipeline_cls is not None:
            return self.pipeline_cls

        # Import lazily to avoid import cycles at module import time
        from market_analysis_engine.market_data.pipeline import DataPipeline  # type: ignore
        return DataPipeline

    def fetch(
        self,
        instrument: str,
        timeframe: str,
        start_ts: datetime,
        end_ts: datetime,
    ) -> pd.DataFrame:
        # --- hard fail early if config is not the full project config ---
        if not isinstance(self.config, dict):
            raise ValueError("Invalid config: expected a dict.")

        if "market_data" not in self.config:
            raise ValueError(
                "Invalid config: missing required key 'market_data' for central DataPipeline. "
                "Pass a full project config including market_data."
            )

        md_cfg = self.config.get("market_data")
        if not isinstance(md_cfg, dict):
            raise ValueError("Invalid config: config['market_data'] must be a dict.")

        if "instruments" not in md_cfg or not isinstance(md_cfg.get("instruments"), dict):
            raise ValueError("Invalid config: config['market_data']['instruments'] missing or invalid.")

        # (optional but helpful) fail fast if instrument not declared
        if instrument not in md_cfg["instruments"]:
            raise UnsupportedInstrumentError(f"instrument not supported: {instrument}")

        pipeline_cls = self._get_pipeline_cls()

        # DataPipeline requires config â†’ we always pass it
        try:
            pipe = pipeline_cls(self.config)
        except TypeError as e:
            raise BarLoaderError(
                "central DataPipeline init failed (expected DataPipeline(config))."
            ) from e

        # Central pipeline API: load_raw_data(symbol, timeframe)
        try:
            df = pipe.load_raw_data(symbol=instrument, timeframe=timeframe)
        except FileNotFoundError as e:
            raise UnsupportedInstrumentError(f"instrument not supported: {instrument}") from e
        except KeyError as e:
            # normalize central KeyError into clearer config error
            raise ValueError(
                f"Invalid config: missing key {e!s} required by central DataPipeline."
            ) from e
        except Exception as e:
            msg = str(e).lower()
            if "not found" in msg or "unknown" in msg or "missing" in msg or "symbol" in msg:
                raise UnsupportedInstrumentError(f"instrument not supported: {instrument}") from e
            raise

        if not isinstance(df, pd.DataFrame):
            raise DataSchemaError("central data layer did not return a pandas DataFrame")

        return df
# ---------------------------------------------------------------------
# Backward compatibility alias (used by tests)
# ---------------------------------------------------------------------
CentralMarketDataSource = CentralPipelineBarsSource


from pathlib import Path

@dataclass(frozen=True)
class RawTxtBarsSource:
    """
    Minimal raw-file source:
    Reads from market_analysis_engine/data/raw/<timeframe>/<INSTRUMENT>_30D.txt
    where .txt is CSV-formatted (pd.read_csv).
    """
    root_dir: Optional[str] = None  # allow override; default resolves repo-relative

    def _resolve_root(self) -> Path:
        if self.root_dir:
            return Path(self.root_dir).resolve()

        # repo_root = pattern_engine/.. (one level up)
        repo_root = Path(__file__).resolve().parents[1]
        return (repo_root / "market_analysis_engine" / "data" / "raw").resolve()

    def _candidate_files(
        self,
        instrument: str,
        timeframe: str,
        start_ts: datetime,
        end_ts: datetime,
    ) -> list[Path]:
        root = self._resolve_root()
        base_dir = root / instrument / timeframe

        if not base_dir.exists():
            raise DataSchemaError(f"dataset path not found: {base_dir}")
        if not base_dir.is_dir():
            raise DataSchemaError(f"dataset path is not a directory: {base_dir}")

        files: list[Path] = []
        for year in range(start_ts.year, end_ts.year + 1):
            path = base_dir / f"data_{year}.txt"
            if path.exists():
                files.append(path)

        if not files:
            raise DataSchemaError(
                f"no yearly txt files found for instrument={instrument!r}, "
                f"timeframe={timeframe!r}, years={start_ts.year}-{end_ts.year}"
            )

        return files


    def _read_one_file(self, path: Path) -> pd.DataFrame:
        try:
            df = pd.read_csv(
                path,
                sep=";",
                decimal=",",
                parse_dates=["DateTime"],
                dayfirst=True,
                engine="python",
            )
        except Exception as e:
            raise DataSchemaError(f"cannot parse raw bars file: {path}") from e

        required = ["DateTime", "Open", "High", "Low", "Close", "BidVolume", "AskVolume"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise DataSchemaError(f"missing columns in raw file {path}: {missing}")

        out = pd.DataFrame()
        out["timestamp"] = pd.to_datetime(df["DateTime"], errors="coerce")

        if getattr(out["timestamp"].dt, "tz", None) is None:
            out["timestamp"] = out["timestamp"].dt.tz_localize("UTC")

        out["open"] = pd.to_numeric(df["Open"], errors="coerce")
        out["high"] = pd.to_numeric(df["High"], errors="coerce")
        out["low"] = pd.to_numeric(df["Low"], errors="coerce")
        out["close"] = pd.to_numeric(df["Close"], errors="coerce")

        bid = pd.to_numeric(df["BidVolume"], errors="coerce").fillna(0.0)
        ask = pd.to_numeric(df["AskVolume"], errors="coerce").fillna(0.0)
        out["volume"] = bid + ask
        out["delta"] = ask - bid

        return out

    def fetch(
        self,
        instrument: str,
        timeframe: str,
        start_ts: datetime,
        end_ts: datetime,
    ) -> pd.DataFrame:
        files = self._candidate_files(
            instrument=instrument,
            timeframe=timeframe,
            start_ts=start_ts,
            end_ts=end_ts,
        )

        chunks: list[pd.DataFrame] = []
        for path in files:
            chunks.append(self._read_one_file(path))

        out = pd.concat(chunks, ignore_index=True)

        mask = (out["timestamp"] >= start_ts) & (out["timestamp"] <= end_ts)
        out = out.loc[mask].sort_values("timestamp").reset_index(drop=True)

        return out

# =============================================================================
# Public Loader
# =============================================================================
class BarDataLoader:
    """
    Pattern Engine Bar Data Loader (Chapter 4)

    Usage patterns:
      1) Explicit:
         loader = BarDataLoader(config=your_config_dict)
         df = loader.load(...)

      2) Module default:
         init_default_loader(your_config_dict)
         df = load_bars(...)
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        source: Optional[BarsSource] = None,
    ) -> None:
        # config is required only when we use the central pipeline source
        if config is None:
            config = {}

        if not isinstance(config, dict):
            raise ValueError("config must be a dict")

        self._config = config

        # If a custom source is provided (tests do this), we don't require any config.
        if source is not None:
            self._source = source
            return

        # Default source selection:
        # - If full project config includes market_data -> use central DataPipeline
        # - Otherwise -> use raw TXT source (existing dataset in market_analysis_engine/data/raw)
        if "market_data" in config:
            self._source = CentralPipelineBarsSource(config=config)
        else:
            # Raw TXT is DEV / fixture mode only.
            # Official runtime source outside repo is the central market_data pipeline.
            import os

            raw_root = os.getenv("PATTERN_ENGINE_RAW_ROOT")
            if raw_root:
                self._source = RawTxtBarsSource(root_dir=raw_root)
                
            else:
                raise ValueError(
                    "No supported bars source configured: provide config['market_data'] "
                    "or set PATTERN_ENGINE_RAW_ROOT for dev raw-txt mode."
                )


    def load(
        self,
        instrument: str,
        timeframe: str,
        start_ts: datetime,
        end_ts: datetime,
        include_delta: bool = False,
    ) -> pd.DataFrame:
        # --- basic input validation ---
        if start_ts is None or end_ts is None:
            raise ValueError("start_ts and end_ts are required")
        if start_ts >= end_ts:
            raise NoDataError("no data: empty/invalid time range (start_ts >= end_ts)")
        if start_ts.tzinfo is None or end_ts.tzinfo is None:
            raise DataSchemaError("start_ts/end_ts must be timezone-aware datetimes")

        _validate_timeframe_format(timeframe)

        # --- fetch from source ---
        df_raw = self._source.fetch(instrument, timeframe, start_ts, end_ts)

        if df_raw is None or len(df_raw) == 0:
            raise NoDataError(
                f"no data: central source returned empty dataframe for {instrument} {timeframe}"
            )

        # --- normalize column names (support both 'time' and 'timestamp') ---
        df = df_raw.copy()

        if "timestamp" not in df.columns and "time" in df.columns:
            df = df.rename(columns={"time": "timestamp"})

        # If include_delta=False we *prefer* to drop delta if present.
        if not include_delta and "delta" in df.columns:
            df = df.drop(columns=["delta"])

        # Convert timestamp to datetime (keep tz if present)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # --- validate required columns + tz awareness before slicing ---
        _validate_required_columns(df)
        _require_tz_aware_timestamp(df)

        # --- slice time range (inclusive bounds) ---
        df = df[(df["timestamp"] >= start_ts) & (df["timestamp"] <= end_ts)].copy()

        if df.empty:
            raise NoDataError(
                f"no data: empty range after slicing ({instrument} {timeframe}) "
                f"start={start_ts.isoformat()} end={end_ts.isoformat()}"
            )

        # --- sort (DO NOT drop duplicates: tests expect an error) ---
        df = df.sort_values("timestamp").reset_index(drop=True)

        # --- numeric coercions for OHLCV (+delta if present) ---
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if "delta" in df.columns:
            df["delta"] = pd.to_numeric(df["delta"], errors="coerce")

        # --- validations ---
        _validate_required_columns(df)
        _require_tz_aware_timestamp(df)
        _validate_no_nan_ohlcv(df)
        _validate_sorted_unique_timestamp(df)  # <-- this now catches duplicates
        _validate_ohlc_sanity(df)

        # include_delta contract: if requested, require it
        if include_delta and "delta" not in df.columns:
            raise DataSchemaError("include_delta=True but delta column missing")

        return df
   



def _ensure_market_data_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    DataPipeline in market_analysis_engine.market_data.pipeline expects cfg["market_data"].
    Pattern Engine accepts a config.yaml that might be "pattern-only".
    For MVP we inject a minimal market_data section if missing.
    """
    if not isinstance(cfg, dict):
        raise ValueError("config must be a dict")

    if "market_data" not in cfg:
        # minimal safe defaults: adjust paths if your pipeline expects different keys
        cfg = dict(cfg)  # shallow copy
        cfg["market_data"] = {
            # the central pipeline typically reads paths/symbol map from here
            # keep it minimal; user config.yaml should normally provide it
            "enabled": True,
        }
    return cfg


# =============================================================================
# Module-level convenience API
# =============================================================================
_DEFAULT_LOADER: Optional[BarDataLoader] = None


def init_default_loader(config: Dict[str, Any]) -> BarDataLoader:
    global _DEFAULT_LOADER
    config = _ensure_market_data_config(config)
    _DEFAULT_LOADER = BarDataLoader(config=config)
    return _DEFAULT_LOADER


def load_bars(
    instrument: str,
    timeframe: str,
    start_ts: datetime,
    end_ts: datetime,
    include_delta: bool = False,
    config: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    # If config is provided, use it directly (no global state required)
    if config is not None:
        return BarDataLoader(config=config).load(
            instrument, timeframe, start_ts, end_ts, include_delta=include_delta
        )

    if _DEFAULT_LOADER is None:
        raise ValueError(
            "Default loader not initialized. Call init_default_loader(config) or pass config=... to load_bars()."
        )

    return _DEFAULT_LOADER.load(
        instrument, timeframe, start_ts, end_ts, include_delta=include_delta
    )
