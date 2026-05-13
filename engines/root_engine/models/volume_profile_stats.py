from pydantic import BaseModel
from typing import List, Dict

class VolumeProfileStats(BaseModel):
    # POC / HVN / LVN
    poc_price: float = 0.0
    poc_volume: float = 0.0
    hvn_levels: List[float] = []
    lvn_levels: List[float] = []

    # distribuzione volume
    total_volume: float = 0.0
    volume_by_price: Dict[float, float] = {}

    skewness: float = 0.0
    kurtosis: float = 0.0
    concentration: float = 0.0
    asymmetry: float = 0.0
    density_around_mid: float = 0.0

    # volume ai boundary e struttura profilo
    volume_upper_boundary: float = 0.0
    volume_lower_boundary: float = 0.0
    profile_width: float = 0.0
    concentration_factor: float = 0.0
    overlapping_factor: float = 0.0
    volume_balance_upper_vs_lower: float = 0.0
