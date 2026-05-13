from typing import List, Dict, Any

from .levels_engine_runner import compute_session_levels
from .levels_index import build_levels_index
from .breakout_context import extract_breakout_context
from .ml_features import compute_ml_features


def enrich_breakouts_with_levels(
    breakouts: List[Any],
    bars: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Arricchisce i breakout con le feature market_levels.
    """

    if not breakouts:
        return []

    instrument = breakouts[0].instrument
    if instrument in (None, "", "unknown"):
        instrument = "MNQ"

    # ----------------------------------
    # CALCOLO LEVELS
    # ----------------------------------
    levels = compute_session_levels(
        bars=bars,
        config=config,
        instrument=instrument,
    )

   

    levels_index = build_levels_index(levels)

    enriched_rows = []

    for breakout in breakouts:

        # context breakout
        ctx = extract_breakout_context(
            breakout,
            default_instrument=instrument,
        )


        key = (
            ctx["breakout_date"],
            ctx["session_name"],
            ctx["instrument"],
        )

        levels_row = levels_index.get(key)

        # compute features
        ml = compute_ml_features(breakout, levels_row)

        # convert breakout model → dict
        row = breakout.model_dump(mode="json", exclude_none=False)
        # append ml features
        row.update(ml)

        enriched_rows.append(row)

    return enriched_rows