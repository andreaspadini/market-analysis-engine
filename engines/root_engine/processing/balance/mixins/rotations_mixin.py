from datetime import datetime
from typing import Any, List

from engines.root_engine.processing.balance.schema import RotationInfo
from engines.root_engine.utils.logger import logger


class RotationsMixin:
    """
    Mixin per il calcolo delle rotazioni di mercato.

    Input:
        bars: List[dict] con campi:
            time
            open
            high
            low
            close
            volume
            delta

    Output:
        List[RotationInfo]
    """

    def _compute_rotations(self, bars: List[Any]) -> List[RotationInfo]:

        rotations: List[RotationInfo] = []
        self._rotation_bar_counts = {}

        if not bars or len(bars) < 2:
            logger.debug("ROTATIONS: meno di 2 barre — nessuna rotazione generata.")
            return rotations

        config_all = getattr(self, "config", {}) or {}
        cfg = config_all.get("rotations", config_all)

        merge_same_direction = bool(cfg.get("merge_same_direction", False))
        whipsaw_bars = int(cfg.get("whipsaw_bars", 0))

        min_rotation_amplitude = float(cfg.get("min_rotation_amplitude", 0.0))
        min_rotation_bars = int(cfg.get("min_rotation_bars", 0))
        rotation_volume_filter = float(cfg.get("rotation_volume_filter", 0.0))
        rotation_delta_filter = float(cfg.get("rotation_delta_filter", 0.0))

        def _get_attr(bar: Any, name: str):
            if isinstance(bar, dict):
                return bar[name]
            return getattr(bar, name)

        current_rotation = None
        last_direction = None

        for i in range(1, len(bars)):

            prev_bar = bars[i - 1]
            bar = bars[i]

            prev_high = _get_attr(prev_bar, "high")
            prev_low = _get_attr(prev_bar, "low")

            high = _get_attr(bar, "high")
            low = _get_attr(bar, "low")

            if high > prev_high:
                bar_direction = "up"
            elif low < prev_low:
                bar_direction = "down"
            else:
                bar_direction = last_direction

            if current_rotation is None:

                if bar_direction in ("up", "down"):
                    current_rotation = {
                        "index": len(rotations),
                        "direction": bar_direction,
                        "bars": [prev_bar, bar],
                    }

                    last_direction = bar_direction

                continue

            current_dir = current_rotation["direction"]

            if bar_direction is None or bar_direction == current_dir:

                current_rotation["bars"].append(bar)
                last_direction = current_dir

            else:

                finalized = self._finalize_rotation(current_rotation)
                rotations.append(finalized)

                if len(rotations) >= 2:

                    r1 = rotations[-1]
                    r0 = rotations[-2]

                    c0 = self._rotation_bar_counts.get(r0.index, 0)
                    c1 = self._rotation_bar_counts.get(r1.index, 0)

                    if c0 <= whipsaw_bars and c1 <= whipsaw_bars:
                        r0.validity_flag = False
                        r1.validity_flag = False

                current_rotation = {
                    "index": len(rotations),
                    "direction": bar_direction,
                    "bars": [prev_bar, bar],
                }

                last_direction = bar_direction

        if current_rotation is not None:

            finalized = self._finalize_rotation(current_rotation)
            rotations.append(finalized)

            if len(rotations) >= 2:

                r1 = rotations[-1]
                r0 = rotations[-2]

                c0 = self._rotation_bar_counts.get(r0.index, 0)
                c1 = self._rotation_bar_counts.get(r1.index, 0)

                if c0 <= whipsaw_bars and c1 <= whipsaw_bars:
                    r0.validity_flag = False
                    r1.validity_flag = False

        if merge_same_direction and rotations:

            merged = [rotations[0]]

            merged_counts = {
                rotations[0].index: self._rotation_bar_counts.get(rotations[0].index, 0)
            }

            for rot in rotations[1:]:

                last = merged[-1]

                if rot.direction == last.direction:

                    last.volume += rot.volume
                    last.delta += rot.delta
                    last.end_price = rot.end_price
                    last.end_time = rot.end_time
                    last.amplitude = abs(last.end_price - last.start_price)

                    merged_counts[last.index] = (
                        merged_counts.get(last.index, 0)
                        + self._rotation_bar_counts.get(rot.index, 0)
                    )

                    self._rotation_bar_counts[last.index] = merged_counts[last.index]

                    last.validity_flag = self._is_rotation_valid(last)

                else:

                    merged.append(rot)

                    merged_counts[rot.index] = self._rotation_bar_counts.get(rot.index, 0)

            rotations = merged

        for idx, rot in enumerate(rotations):
            rot.index = idx

        logger.info("Rotazioni finali calcolate: %d", len(rotations))

        try:
            cfg = self.config.get("rotations", {})
            min_bars_dbg = int(cfg.get("min_rotation_bars", 0))
            counts_dbg = list(getattr(self, "_rotation_bar_counts", {}).values())
            valid_dbg = sum(1 for r in rotations if getattr(r, "validity_flag", True))

            print(
                "[ROT DBG]",
                {
                    "min_rotation_bars": min_bars_dbg,
                    "total_rotations": len(rotations),
                    "valid_rotations": valid_dbg,
                    "bar_counts_sample": counts_dbg[:20],
                    "bar_count_min": min(counts_dbg) if counts_dbg else None,
                    "bar_count_max": max(counts_dbg) if counts_dbg else None,
                },
            )
        except Exception as e:
            print("[ROT DBG ERROR]", repr(e))

        return rotations


    def _finalize_rotation(self, current_rotation: dict) -> RotationInfo:

        bars = current_rotation["bars"]
        direction = current_rotation["direction"]
        index = current_rotation["index"]

        def _get_attr(bar: Any, name: str):
            if isinstance(bar, dict):
                return bar[name]
            return getattr(bar, name)

        start_bar = bars[0]
        end_bar = bars[-1]

        start_time = _get_attr(start_bar, "time")
        end_time = _get_attr(end_bar, "time")

        start_price = float(_get_attr(start_bar, "close"))
        end_price = float(_get_attr(end_bar, "close"))

        amplitude = abs(end_price - start_price)

        volume = sum(float(_get_attr(b, "volume")) for b in bars)
        delta = sum(float(_get_attr(b, "delta")) for b in bars)

        bar_count = len(bars)

        cfg = self.config.get("rotations", {})

        if amplitude >= cfg.get("min_rotation_amplitude_structural", 5):
            rotation_type = "structural"

        elif amplitude >= cfg.get("min_rotation_amplitude_standard", 3):
            rotation_type = "standard"

        elif amplitude >= cfg.get("min_rotation_amplitude_micro", 2):
            rotation_type = "micro"

        else:
            rotation_type = "invalid"

        rotation = RotationInfo(
            index=index,
            direction=direction,
            start_time=start_time,
            end_time=end_time,
            start_price=start_price,
            end_price=end_price,
            amplitude=amplitude,
            volume=volume,
            delta=delta,
            validity_flag=False,
            rotation_type=rotation_type,
        )

        if not hasattr(self, "_rotation_bar_counts"):
            self._rotation_bar_counts = {}

        self._rotation_bar_counts[rotation.index] = bar_count

        rotation.validity_flag = self._is_rotation_valid(rotation)

        return rotation


    def _is_rotation_valid(self, rotation: RotationInfo) -> bool:

        cfg = self.config.get("rotations", {})

        min_amp = float(cfg.get("min_rotation_amplitude", 0.0))
        min_bars = int(cfg.get("min_rotation_bars", 0))

        bar_count = 0
        if hasattr(self, "_rotation_bar_counts"):
            bar_count = int(self._rotation_bar_counts.get(rotation.index, 0))

        return rotation.amplitude >= min_amp and bar_count >= min_bars