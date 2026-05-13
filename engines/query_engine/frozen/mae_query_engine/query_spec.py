
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Union, Tuple
import json
from datetime import datetime

@dataclass
class Filter:
    col: str
    op: str  # "==", "!=", "in", "notin", ">=", "<=", ">", "<", "between", "isnull", "notnull"
    value: Any = None

@dataclass
class Metric:
    """Supported metrics.
    kind:
      - "prob": P(col == 1) or P(condition) if col is boolean/int 0/1
      - "mean": mean(col)
      - "std": std(col)
      - "quantile": quantile(col, q)
      - "count": count rows
    """
    kind: str
    col: Optional[str] = None
    q: Optional[float] = None
    alias: Optional[str] = None

@dataclass
class QuerySpec:
    name: str
    dataset: str  # "df_master" | "levels_long" | "levels_distance" | "levels_flags" | "post_event"
    filters: List[Filter] = field(default_factory=list)
    groupby: List[str] = field(default_factory=list)
    metrics: List[Metric] = field(default_factory=list)
    order_by: Optional[List[Tuple[str, str]]] = None  # [(col, "asc|desc")]
    limit: Optional[int] = None
    # Output/view transforms (do not affect core logic)
    timezone: Optional[str] = None
    include_time_views: bool = False

    def to_json(self) -> str:
        payload = asdict(self)
        payload["_generated_at"] = datetime.utcnow().isoformat() + "Z"
        return json.dumps(payload, ensure_ascii=False, indent=2)
