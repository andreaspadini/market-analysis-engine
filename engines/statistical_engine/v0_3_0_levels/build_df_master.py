from __future__ import annotations

from dataclasses import dataclass
from datetime import time as dtime
from pathlib import Path
from typing import Any, Mapping, Optional

import ast

import numpy as np
import pandas as pd
import yaml
import pyarrow.parquet as pq


# ================================
# SESSION CLASSIFICATION FUNCTION
# (identica alla versione script)
# ================================
def classify_session(t: dtime) -> str:
    asia_open = dtime(1, 0)
    asia_close = dtime(10, 0)

    europe_open = dtime(9, 0)
    europe_close = dtime(17, 30)

    usa_open = dtime(15, 30)
    usa_close = dtime(22, 0)

    # PRIORITY: USA > Europe > Asia
    if usa_open <= t < usa_close:
        return "usa"
    if europe_open <= t < europe_close:
        return "europe"
    if asia_open <= t < asia_close:
        return "asia"

    return "off"

def extract_max_excursion(x):
    if pd.isna(x):
        return np.nan

    # Caso: stringa Python con None → usare ast
    if isinstance(x, str):
        try:
            d = ast.literal_eval(x)
            return float(d.get("max_excursion", np.nan))
        except:
            return np.nan

    # Caso: già dict
    if isinstance(x, dict):
        return float(x.get("max_excursion", np.nan))

    return np.nan



def load_yaml_config(config_path: Path) -> dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass(frozen=True)
class DFMasterPaths:
    breakouts_dir: Path
    levels_dir: Path
    output_file: Path
    summary_file: Optional[Path] = None


def build_df_master_breakouts_levels_v0_3_0(
    *,
    breakouts_dir: Path,
    levels_dir: Path,
    instrument: str,
    atr_multiplier: float | None = None,
    strict_schema: bool = True,
    baseline_parquet_path: Path | None = None,
    write_parquet_to: Optional[Path] = None,
    write_summary_to: Optional[Path] = None,
    debug_print: bool = False,
) -> pd.DataFrame:
    """
    Build df_master (breakouts + levels join).

    NOTE: Questo è un refactor strutturale dello script originale:
    - nessun side-effect all'import
    - stessa logica di trasformazione e join
    - stesso schema atteso (baseline: df_master_breakouts_levels_v0.3.0.parquet)
    """

    # ================================
    # LOAD BREAKOUTS
    # ================================
    breakout_files = list(Path(breakouts_dir).glob("*.csv"))
    df_breakouts = pd.concat([pd.read_csv(f) for f in breakout_files], ignore_index=True)

    df_breakouts["breakout_time"] = pd.to_datetime(df_breakouts["breakout_time"])
    df_breakouts["breakout_date"] = df_breakouts["breakout_time"].dt.date
    df_breakouts["breakout_time_only"] = df_breakouts["breakout_time"].dt.time

    df_breakouts["session_name"] = df_breakouts["breakout_time_only"].apply(classify_session)
    df_breakouts = df_breakouts[df_breakouts["session_name"] != "off"]

    if debug_print:
        print("Breakouts columns:")
        print(df_breakouts.columns.tolist())

    # --- STATISTICAL ASSUMPTION: instrument universe ---
    df_breakouts["instrument"] = instrument

    # ================================
    # DERIVED FIELDS (copiati dal research engine v0.2.1)
    # ================================
    df_breakouts["max_excursion"] = df_breakouts["follow_through"].apply(extract_max_excursion)

    if atr_multiplier is None:
        if strict_schema:
            raise ValueError("atr_multiplier is required to compute success_1ATR (strict_schema=True)")
        # se non strict, lasciamo la colonna fuori
    else:
        df_breakouts["success_1ATR"] = (
            df_breakouts["max_excursion"] >= (atr_multiplier * df_breakouts["atr_before"])
        ).astype(int)

    # ================================
    # LOAD LEVELS
    # ================================
    levels_files = list(Path(levels_dir).glob("*.csv"))
    df_levels = pd.concat([pd.read_csv(f) for f in levels_files], ignore_index=True)

    df_levels["date"] = pd.to_datetime(df_levels["date"]).dt.date

    # normalize instrument naming
    df_levels["instrument"] = df_levels["instrument"].str.upper()

    # ================================
    # JOIN LOGIC
    # ================================
    df_master = df_breakouts.merge(
        df_levels,
        left_on=["breakout_date", "session_name", "instrument"],
        right_on=["date", "session_name", "instrument"],
        how="left",
    )

    # ================================
    # SCHEMA PRESERVATION (v0.3.0 baseline)
    # ================================
    if "max_excursion" not in df_master.columns:
        df_master["max_excursion"] = pd.NA
    if "success_1ATR" not in df_master.columns:
        if strict_schema:
            raise ValueError("success_1ATR missing: pass atr_multiplier or set strict_schema=False")
        df_master["success_1ATR"] = pd.NA

    if debug_print:
        print("DF MASTER columns AFTER join:")
        print(df_master.columns.tolist())
        print(
            df_master[
                [
                    "breakout_date",
                    "session_name",
                    "instrument",
                    "session_high",
                    "day_high",
                    "weekly_high",
                    "monthly_high",
                ]
            ].head(10)
        )

    # SESSION FIELDS TO CLEAR WHEN breakout_session == "off"
    # (nel codice originale è calcolato ma non usato: lo manteniamo per non cambiare semantica)
    _session_cols = [c for c in df_master.columns if c.startswith("session_")]

    # ================================
    # COLUMN ORDER (baseline parquet)
    # Mantiene ordine colonne identico al baseline quando richiesto.
    # ================================
    if baseline_parquet_path is not None:
        baseline_cols = pd.read_parquet(Path(baseline_parquet_path)).columns.tolist()
        if baseline_cols:
            df_master = df_master.reindex(columns=baseline_cols)

    # ================================
    # EXPORT (opzionale)
    # ================================
    if write_parquet_to is not None:
        Path(write_parquet_to).parent.mkdir(parents=True, exist_ok=True)
        df_master.to_parquet(Path(write_parquet_to), index=False)

    if write_summary_to is not None:
        Path(write_summary_to).parent.mkdir(parents=True, exist_ok=True)
        with open(Path(write_summary_to), "w", encoding="utf-8") as f:
            f.write("DF MASTER SUMMARY\n")
            f.write("=================\n")
            f.write(f"Breakouts originali: {len(df_breakouts)}\n")
            f.write(f"Righe df_master:     {len(df_master)}\n")
            f.write(f"\nSession counts:\n")
            f.write(str(df_master["session_name"].value_counts()))
            f.write("\n")

    return df_master


def build_df_master_from_config_v0_3_0(
    *,
    config_path: Path,
    breakouts_dir: Path,
    levels_dir: Path,
    atr_multiplier: float | None = None,
    strict_schema: bool = True,
    baseline_parquet_path: Path | None = None,
    write_parquet_to: Optional[Path] = None,
    write_summary_to: Optional[Path] = None,
    debug_print: bool = False,
) -> pd.DataFrame:
    cfg = load_yaml_config(Path(config_path))
    instrument = cfg["universe"]["instruments"][0]  # identico allo script

    return build_df_master_breakouts_levels_v0_3_0(
        breakouts_dir=Path(breakouts_dir),
        levels_dir=Path(levels_dir),
        instrument=instrument,
        atr_multiplier=atr_multiplier,
        strict_schema=strict_schema,
        baseline_parquet_path=baseline_parquet_path,
        write_parquet_to=write_parquet_to,
        write_summary_to=write_summary_to,
        debug_print=debug_print,
    )
