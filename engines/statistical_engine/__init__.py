"""
market_analysis_engine.statistical_engine

Layer statistico / aggregativo.
Nessun side-effect all'import.
"""

from .statistical_pipeline import run_statistical_pipeline
from .v0_3_0_levels.build_df_master import (
    build_df_master_breakouts_levels_v0_3_0,
    build_df_master_from_config_v0_3_0,
)

__all__ = [
    "run_statistical_pipeline",
    "build_df_master_breakouts_levels_v0_3_0",
    "build_df_master_from_config_v0_3_0",
]