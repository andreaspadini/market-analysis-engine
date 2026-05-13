from typing import Dict, Any, List


def compute_ml_features(
    breakout: Any,
    levels: Any,
) -> Dict[str, Any]:
    """
    Calcola le feature market_levels per un breakout.
    """

    breakout_price = breakout.breakout_price

    if levels is None:
        return {
            "ml_nearest_support": None,
            "ml_nearest_resistance": None,
            "ml_distance_to_level": None,
            "ml_cluster_strength": None,
            "ml_density": None,
            "ml_alignment_score": None,
        }

    # -------------------------------
    # SUPPORT LEVELS
    # -------------------------------
    support_levels: List[float] = [
        levels.session_low,
        levels.day_low,
        levels.prev_day_low,
        levels.weekly_low,
        levels.monthly_low,
        levels.session_val,
        levels.day_val,
        levels.prev_day_val,
        levels.weekly_val,
        levels.monthly_val,
    ]

    support_levels = [x for x in support_levels if x is not None and x <= breakout_price]

    # -------------------------------
    # RESISTANCE LEVELS
    # -------------------------------
    resistance_levels: List[float] = [
        levels.session_high,
        levels.day_high,
        levels.prev_day_high,
        levels.weekly_high,
        levels.monthly_high,
        levels.session_vah,
        levels.day_vah,
        levels.prev_day_vah,
        levels.weekly_vah,
        levels.monthly_vah,
    ]

    resistance_levels = [x for x in resistance_levels if x is not None and x >= breakout_price]

    # -------------------------------
    # NEAREST SUPPORT
    # -------------------------------
    nearest_support = None
    if support_levels:
        nearest_support = max(support_levels)

    # -------------------------------
    # NEAREST RESISTANCE
    # -------------------------------
    nearest_resistance = None
    if resistance_levels:
        nearest_resistance = min(resistance_levels)

    # -------------------------------
    # DISTANCE
    # -------------------------------
    distances = []

    if nearest_support is not None:
        distances.append(abs(breakout_price - nearest_support))

    if nearest_resistance is not None:
        distances.append(abs(nearest_resistance - breakout_price))

    distance_to_level = min(distances) if distances else None

    # -------------------------------
    # ALL LEVELS FOR CLUSTER / DENSITY
    # -------------------------------
    all_levels: List[float | None] = [
        levels.session_low,
        levels.day_low,
        levels.prev_day_low,
        levels.weekly_low,
        levels.monthly_low,
        levels.session_val,
        levels.day_val,
        levels.prev_day_val,
        levels.weekly_val,
        levels.monthly_val,
        levels.session_high,
        levels.day_high,
        levels.prev_day_high,
        levels.weekly_high,
        levels.monthly_high,
        levels.session_vah,
        levels.day_vah,
        levels.prev_day_vah,
        levels.weekly_vah,
        levels.monthly_vah,
    ]

    cluster_strength = compute_cluster_strength(
        breakout_price=breakout_price,
        level_values=all_levels,
    )

    density = compute_density(
        breakout_price=breakout_price,
        level_values=all_levels,
    )

    alignment_score = compute_alignment_score(
        direction=breakout.direction,
        breakout_price=breakout_price,
        nearest_support=nearest_support,
        nearest_resistance=nearest_resistance,
    )

    return {
        "ml_nearest_support": nearest_support,
        "ml_nearest_resistance": nearest_resistance,
        "ml_distance_to_level": distance_to_level,
        "ml_cluster_strength": cluster_strength,
        "ml_density": density,
        "ml_alignment_score": alignment_score,
    }

def compute_cluster_strength(
    breakout_price: float,
    level_values: list[float | None],
    window: float = 50.0,
) -> float:
    """
    Conta quanti livelli cadono nella finestra attorno al breakout_price.
    """

    count = 0

    for lvl in level_values:
        if lvl is None:
            continue

        if abs(breakout_price - lvl) <= window:
            count += 1

    return float(count)

def compute_density(
    breakout_price: float,
    level_values: list[float | None],
    window: float = 50.0,
) -> float:
    """
    Misura la densità dei livelli nella finestra attorno al breakout.
    """

    nearby = [
        lvl for lvl in level_values
        if lvl is not None and abs(breakout_price - lvl) <= window
    ]

    if not nearby:
        return 0.0

    return float(len(nearby) / window)

def compute_alignment_score(
    direction: str,
    breakout_price: float,
    nearest_support: float | None,
    nearest_resistance: float | None,
) -> float | None:
    """
    Misura quanto la direzione del breakout è allineata
    con lo spazio disponibile tra supporto e resistenza.
    """

    if nearest_support is None or nearest_resistance is None:
        return None

    d_support = abs(breakout_price - nearest_support)
    d_resistance = abs(nearest_resistance - breakout_price)

    total = d_support + d_resistance
    if total == 0:
        return 0.5

    if direction == "up":
        return float(d_resistance / total)

    return float(d_support / total)