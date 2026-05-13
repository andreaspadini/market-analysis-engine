from typing import List, Dict, Any

from engines.market_levels.session_levels_engine import (
    SessionLevelsEngine
)

from engines.market_levels.session_levels_schema import (
    SessionLevelsModel
)


def compute_session_levels(
    bars: List[Dict[str, Any]],
    config: Dict[str, Any],
    instrument: str,
    symbol: str = "",
    timeframe: str = "5m",
) -> List[SessionLevelsModel]:
    """
    Esegue il SessionLevelsEngine e restituisce i livelli di mercato
    calcolati per sessione/giorno.
    """

    engine = SessionLevelsEngine(
        bars_5m=bars,
        config=config,
        instrument=instrument,
        symbol=symbol,
        timeframe=timeframe,
    )

    levels = engine.run()

    return levels