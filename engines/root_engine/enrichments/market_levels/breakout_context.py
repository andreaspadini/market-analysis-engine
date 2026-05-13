from datetime import datetime
from typing import Dict, Any

from .session_utils import classify_session


def extract_breakout_context(
    breakout: Any,
    default_instrument: str | None = None,
) -> Dict[str, Any]:
    """
    Estrae il contesto minimo necessario per il mapping dei market levels.
    """

    breakout_time: datetime = breakout.breakout_time

    breakout_date = breakout_time.date()
    breakout_time_only = breakout_time.time()

    session_name = classify_session(breakout_time_only)

    instrument = breakout.instrument
    if instrument in (None, "", "unknown"):
        instrument = default_instrument

    return {
        "breakout_date": breakout_date,
        "session_name": session_name,
        "instrument": instrument,
    }