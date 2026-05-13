from __future__ import annotations

import ast
import pandas as pd


def _parse_payload(value: object) -> object:
    if pd.isna(value):
        return None

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return None

    return None


def append_side_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["side"] = out["direction"].map({
        "up": "long",
        "down": "short",
    })
    return out


def append_range_atr_ratio_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    balance_range = pd.to_numeric(out["balance_range_size"], errors="coerce")
    atr_before = pd.to_numeric(out["atr_before"], errors="coerce")

    ratio = balance_range / atr_before
    ratio = ratio.where(atr_before > 0)

    out["range_atr_ratio"] = ratio

    return out


def append_balance_pressure_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    balance_range = pd.to_numeric(out["balance_range_size"], errors="coerce")
    atr_before = pd.to_numeric(out["atr_before"], errors="coerce")

    pressure = atr_before / balance_range
    pressure = pressure.where(balance_range > 0)

    out["balance_pressure"] = pressure

    return out


def append_breakout_location_ratio_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    breakout_price = pd.to_numeric(out["breakout_price"], errors="coerce")
    midpoint = pd.to_numeric(out["balance_midpoint"], errors="coerce")
    balance_range = pd.to_numeric(out["balance_range_size"], errors="coerce")

    ratio = (breakout_price - midpoint) / balance_range
    ratio = ratio.where(balance_range > 0)

    out["breakout_location_ratio"] = ratio

    return out


def append_abs_initial_delta_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    delta = pd.to_numeric(out["initial_delta"], errors="coerce")
    out["abs_initial_delta"] = delta.abs()

    return out


def append_initial_volume_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    volume = pd.to_numeric(out["initial_volume"], errors="coerce")
    out["initial_volume_feature"] = volume

    return out


def append_volume_atr_ratio_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    volume = pd.to_numeric(out["initial_volume"], errors="coerce")
    atr = pd.to_numeric(out["atr_before"], errors="coerce")

    ratio = volume / atr
    ratio = ratio.where(atr > 0)

    out["volume_atr_ratio"] = ratio

    return out


def append_volume_range_ratio_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    volume = pd.to_numeric(out["initial_volume"], errors="coerce")
    balance_range = pd.to_numeric(out["balance_range_size"], errors="coerce")

    ratio = volume / balance_range
    ratio = ratio.where(balance_range > 0)

    out["volume_range_ratio"] = ratio

    return out

def append_ml_distance_atr_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    distance = pd.to_numeric(out["ml_distance_to_level"], errors="coerce")
    atr_before = pd.to_numeric(out["atr_before"], errors="coerce")

    ratio = distance / atr_before
    ratio = ratio.where(atr_before > 0)

    out["ml_distance_atr"] = ratio

    return out


def append_max_excursion_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    def _extract(value: object) -> object:
        payload = _parse_payload(value)
        if not isinstance(payload, dict):
            return pd.NA
        return pd.to_numeric(payload.get("max_excursion"), errors="coerce")

    out["max_excursion"] = out["follow_through"].apply(_extract)

    return out


def append_breakout_efficiency_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    max_excursion = pd.to_numeric(out["max_excursion"], errors="coerce")
    atr_before = pd.to_numeric(out["atr_before"], errors="coerce")

    ratio = max_excursion / atr_before
    ratio = ratio.where(atr_before > 0)

    out["breakout_efficiency"] = ratio

    return out


def append_pre_total_score_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    def _extract(value: object) -> object:
        payload = _parse_payload(value)
        if not isinstance(payload, dict):
            return pd.NA
        return pd.to_numeric(payload.get("total_score"), errors="coerce")

    out["pre_total_score"] = out["pre_breakout_signal"].apply(_extract)

    return out


def append_hour_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    ts = pd.to_datetime(out["breakout_time"], errors="coerce")

    hour = (
        ts.dt.hour +
        ts.dt.minute / 60 +
        ts.dt.second / 3600
    )

    out["hour"] = hour

    return out


def append_session_calc_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    hour = pd.to_numeric(out["hour"], errors="coerce")

    session = pd.Series(index=out.index, dtype="object")

    session.loc[(hour >= 0.0) & (hour < 8.0)] = "asia"
    session.loc[(hour >= 8.0) & (hour < 13.0)] = "europe"
    session.loc[(hour >= 13.0) & (hour < 21.0)] = "ny"
    session.loc[(hour >= 21.0) & (hour < 24.0)] = "off"

    out["session_calc"] = session

    return out


def append_weekday_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    ts = pd.to_datetime(out["breakout_time"], errors="coerce")

    mapping = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday",
        6: "sunday",
    }

    out["weekday"] = ts.dt.dayofweek.map(mapping)

    return out


def append_day_of_month_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    ts = pd.to_datetime(out["breakout_time"], errors="coerce")

    out["day_of_month"] = ts.dt.day

    return out
def append_week_of_month_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    day = pd.to_numeric(out["day_of_month"], errors="coerce")

    out["week_of_month"] = ((day - 1) // 7) + 1

    return out
def append_year_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    ts = pd.to_datetime(out["breakout_time"], errors="coerce")

    out["year"] = ts.dt.year

    return out
