from typing import Dict, Tuple
from datetime import date

from engines.market_levels.session_levels_schema import (
    SessionLevelsModel
)


def build_levels_index(levels) -> Dict[Tuple[date, str, str], SessionLevelsModel]:
    """
    Costruisce un indice dei livelli per accesso rapido.

    Chiave:
    (date, session_name, instrument)
    """

    index: Dict[Tuple[date, str, str], SessionLevelsModel] = {}

    for lvl in levels:
        key = (
            lvl.date,
            lvl.session_name,
            lvl.instrument
        )

        index[key] = lvl

    return index