from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Any, Dict, List, Tuple, Optional
from market_analysis_engine import ENGINE_VERSION
from pydantic import BaseModel
from engines.market_levels.session_levels_schema import (
    SessionLevelsModel
)



class SessionConfig(BaseModel):
    name: str
    region: str
    open_time: time
    close_time: time
    enabled: bool = True


class SessionLevelsEngine:
    def __init__(
        self,
        bars_5m: List[Dict[str, Any]],
        config: Dict[str, Any],
        instrument: str = "unknown",
        symbol: str = "",
        timeframe: str = "5m",
    ) -> None:
        # 1️⃣ Dati base
        self.bars = bars_5m
        self.instrument = instrument
        self.symbol = symbol
        self.timeframe = timeframe

        # 2️⃣ Config principale per i livelli di sessione
        # (tutta la parte sotto "session_levels" nel config.yaml)
        self.config: Dict[str, Any] = config.get("session_levels", {}) or {}

        # 3️⃣ Sottoconfig: volume profile e vwap
        self.vp_cfg: Dict[str, Any] = self.config.get("volume_profile", {}) or {}

        # 🔹 QUESTA RIGA MANCA ORA → LA AGGIUNGIAMO
        self.vwap_cfg: Dict[str, Any] = self.config.get("vwap", {}) or {}

        # 4️⃣ Versione engine
        self.engine_version = ENGINE_VERSION

        # 5️⃣ Sessioni (asia / eu / us)
        self.sessions: Dict[str, SessionConfig] = self._build_sessions()



    def _build_sessions(self) -> Dict[str, SessionConfig]:
        """
        Costruisce i SessionConfig a partire da config.yaml:
        config["session_levels"]["sessions"][<nome>] = {
            "open_time": "HH:MM",
            "close_time": "HH:MM",
            "region": "...",
            "enabled": true/false,
        }
        """
        sessions_cfg = self.config.get("sessions", {})
        sessions: Dict[str, SessionConfig] = {}

        for name, cfg in sessions_cfg.items():
            if not cfg.get("enabled", True):
                continue

            open_str = cfg.get("open_time", "00:00")
            close_str = cfg.get("close_time", "23:59")

            open_t = datetime.strptime(open_str, "%H:%M").time()
            close_t = datetime.strptime(close_str, "%H:%M").time()

            sessions[name] = SessionConfig(
                name=name,
                open_time=open_t,
                close_time=close_t,
                region=cfg.get("region", name),
                enabled=cfg.get("enabled", True),
                timezone=cfg.get("timezone", "UTC"),
            )
        return sessions


    # ------------------------------------------------------
    # CONFIG
    # ------------------------------------------------------
    def _load_session_configs(self) -> List[SessionConfig]:
        sessions_raw = self.config.get("sessions", {})
        result: List[SessionConfig] = []

        for name, scfg in sessions_raw.items():
            open_h, open_m = map(int, scfg["open"].split(":"))
            close_h, close_m = map(int, scfg["close"].split(":"))
            tz = scfg.get("timezone", "Europe/Rome")

            result.append(
                SessionConfig(
                    name=name,
                    open_time=time(open_h, open_m),
                    close_time=time(close_h, close_m),
                    timezone=tz,
                )
            )

        return result

    # ------------------------------------------------------
    # ENTRYPOINT
    # ------------------------------------------------------
    def run(self) -> List[SessionLevelsModel]:
        rows: List[SessionLevelsModel] = []

        # --- Raggruppa barre per giorno ---
        grouped_by_date = self._group_bars_by_date()

        # --- Weekly / Monthly grouping ---
        weekly_groups = self._group_bars_by_week()
        monthly_groups = self._group_bars_by_month()

        weekly_context_by_date: Dict[date, Dict[str, float]] = {}
        for (year, week), bars in weekly_groups.items():
            if not bars:
                continue
            w_high = max(b["high"] for b in bars)
            w_low = min(b["low"] for b in bars)
            w_vwap = self._compute_vwap_for_bars(bars)

            for d in {b["time"].date() for b in bars}:
                weekly_context_by_date[d] = {
                    "weekly_high": w_high,
                    "weekly_low": w_low,
                    "weekly_vwap": w_vwap,
                }

        monthly_context_by_date: Dict[date, Dict[str, float]] = {}
        for (year, month), bars in monthly_groups.items():
            if not bars:
                continue
            m_high = max(b["high"] for b in bars)
            m_low = min(b["low"] for b in bars)
            m_vwap = self._compute_vwap_for_bars(bars)

            for d in {b["time"].date() for b in bars}:
                monthly_context_by_date[d] = {
                    "monthly_high": m_high,
                    "monthly_low": m_low,
                    "monthly_vwap": m_vwap,
                }

        # --- Per ogni giorno ---
        for d, day_bars in grouped_by_date.items():

            prev_day_bars = self._get_previous_day_bars(d, grouped_by_date)
            prev_day_profile = self._build_prev_profile(prev_day_bars)

            # --- Per ogni sessione ---
            for sess_name, sess_cfg in self.sessions.items():

                sess_bars = self._slice_session(day_bars, sess_cfg)
                if not sess_bars:
                    continue

                row = self._build_session_row(
                    date=d,
                    session_name=sess_name,
                    session_cfg=sess_cfg,   # <---- AGGIUNTO
                    session_bars=sess_bars,
                    day_bars=day_bars,
                    prev_day_bars=prev_day_bars,
                    prev_day_profile=prev_day_profile,
                    weekly_ctx=weekly_context_by_date.get(d),
                    monthly_ctx=monthly_context_by_date.get(d),
                )


                rows.append(row)

        return rows





    # ------------------------------------------------------
    # SESSION SLICING
    # ------------------------------------------------------
    def _slice_session(self, day_bars: List[Dict[str, Any]], sess_cfg: SessionConfig):
        """
        Restituisce solo le barre appartenenti alla sessione indicata.
        Supporta anche sessioni che passano la mezzanotte.
        """
        start = sess_cfg.open_time      # datetime.time
        end = sess_cfg.close_time       # datetime.time

        sliced = []

        for b in day_bars:
            t = b["time"].time()

            # Caso 1: sessione normale nello stesso giorno (es. 09:00 → 17:30)
            if start < end:
                if start <= t < end:
                    sliced.append(b)

            # Caso 2: sessione che attraversa la mezzanotte (es. 22:00 → 05:00)
            else:
                if t >= start or t < end:
                    sliced.append(b)

        return sliced



    # ------------------------------------------------------
    # DAILY PROFILE (prev_day_* )
    # ------------------------------------------------------
    def _compute_daily_profile(self, day_bars: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
        if not day_bars:
            return {
                "poc": None,
                "vah": None,
                "val": None,
                "vwap": None,
            }

        vp = self._build_volume_profile(day_bars)
        poc, vah, val = self._compute_poc_vah_val(vp)
        vwap = self._compute_vwap(day_bars)

        return {
            "poc": poc,
            "vah": vah,
            "val": val,
            "vwap": vwap,
        }

    # ------------------------------------------------------
    # VOLUME PROFILE & VWAP
    # ------------------------------------------------------
    def _build_volume_profile(self, bars: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
        """
        Volume profile semplificato:
        - prezzo rappresentativo = (high + low + close) / 3
        - volume aggregato per bin di prezzo (bin_size di config)
        """
        bin_size = float(self.vp_cfg.get("bin_size", 1.0))
        vols: Dict[float, float] = {}

        for b in bars:
            typical_price = (b["high"] + b["low"] + b["close"]) / 3.0
            bin_price = round(typical_price / bin_size) * bin_size
            vols[bin_price] = vols.get(bin_price, 0.0) + float(b.get("volume", 0.0))

        vp = sorted(vols.items(), key=lambda x: x[0])  # [(price, vol), ...]
        return vp

    def _compute_poc_vah_val(
        self,
        vp: List[Tuple[float, float]],
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        if not vp:
            return None, None, None

        total_vol = sum(v for _, v in vp)
        if total_vol <= 0:
            poc_price = vp[0][0]
            return poc_price, poc_price, poc_price

        # POC = livello di prezzo con volume massimo
        poc_price, _ = max(vp, key=lambda x: x[1])

        value_area_pct = float(self.vp_cfg.get("value_area_pct", 0.70))

        # troviamo index del POC
        prices = [p for p, _ in vp]
        vols = [v for _, v in vp]
        poc_idx = prices.index(poc_price)

        # espandiamo attorno al POC finché non copriamo value_area_pct del volume
        included = {poc_idx}
        cum_vol = vols[poc_idx]

        left = poc_idx - 1
        right = poc_idx + 1

        while cum_vol / total_vol < value_area_pct:
            left_vol = vols[left] if left >= 0 else -1.0
            right_vol = vols[right] if right < len(vp) else -1.0

            if left_vol < 0 and right_vol < 0:
                break

            if right_vol >= left_vol:
                included.add(right)
                cum_vol += right_vol
                right += 1
            else:
                included.add(left)
                cum_vol += left_vol
                left -= 1

        included_prices = [prices[i] for i in sorted(included)]
        val = min(included_prices)
        vah = max(included_prices)

        return poc_price, vah, val

    def _compute_vwap(self, bars: List[Dict[str, Any]]) -> Optional[float]:
        if not bars or not self.vwap_cfg.get("enabled", True):
            return None

        num = 0.0
        den = 0.0
        for b in bars:
            typical_price = (b["high"] + b["low"] + b["close"]) / 3.0
            vol = float(b.get("volume", 0.0))
            num += typical_price * vol
            den += vol

        if den <= 0:
            return None

        return num / den

    # ------------------------------------------------------
    # SESSION ROW
    # ------------------------------------------------------
    def _build_session_row(
        self,
        date: date,
        session_name: str,
        session_cfg: SessionConfig,   # <---- AGGIUNGI QUESTO
        session_bars: List[Dict[str, Any]],
        day_bars: List[Dict[str, Any]],
        prev_day_bars: Optional[List[Dict[str, Any]]],
        prev_day_profile: Optional[Dict[str, Optional[float]]],
        weekly_ctx: Optional[Dict[str, float]],
        monthly_ctx: Optional[Dict[str, float]],
    ) -> SessionLevelsModel:



        # ======================
        # SESSION BASIC METRICS
        # ======================
        o = session_bars[0]["open"]
        c = session_bars[-1]["close"]
        h = max(b["high"] for b in session_bars)
        l = min(b["low"] for b in session_bars)
        r = h - l

        # volume profile
        vp = self._build_volume_profile(session_bars)
        poc, vah, val = self._compute_poc_vah_val(vp)
        vwap = self._compute_vwap(session_bars)
        total_vol = sum(float(b.get("volume", 0.0)) for b in session_bars)

        # ======================
        # PREVIOUS DAY PROFILE
        # ======================
        prev_poc = prev_day_profile.get("poc") if prev_day_profile else None
        prev_vah = prev_day_profile.get("vah") if prev_day_profile else None
        prev_val = prev_day_profile.get("val") if prev_day_profile else None
        prev_vwap = prev_day_profile.get("vwap") if prev_day_profile else None

        # touch/break functions
        def _touched(level):
            if level is None:
                return None
            return l <= level <= h

        def _broke(level):
            if level is None:
                return None
            was_above = o > level
            was_below = o < level
            went_above = h >= level
            went_below = l <= level
            return (was_above and went_below) or (was_below and went_above)

        touched_poc = _touched(prev_poc)
        touched_vah = _touched(prev_vah)
        touched_val = _touched(prev_val)
        touched_vwap = _touched(prev_vwap)

        broke_poc = _broke(prev_poc)
        broke_vah = _broke(prev_vah)
        broke_val = _broke(prev_val)
        broke_vwap = _broke(prev_vwap)

        # ======================
        # DAILY CONTEXT (CURRENT DAY)
        # ======================
        day_high = max(b["high"] for b in day_bars)
        day_low = min(b["low"] for b in day_bars)
        day_range = day_high - day_low
        day_mid = (day_high + day_low) / 2

        day_vp = self._build_volume_profile(day_bars)
        day_poc, day_vah, day_val = self._compute_poc_vah_val(day_vp)
        day_vwap = self._compute_vwap(day_bars)

        # ======================
        # WEEKLY + MONTHLY CONTEXT
        # ======================
        weekly_high = weekly_ctx["weekly_high"] if weekly_ctx else None
        weekly_low = weekly_ctx["weekly_low"] if weekly_ctx else None
        weekly_vwap = weekly_ctx["weekly_vwap"] if weekly_ctx else None

        monthly_high = monthly_ctx["monthly_high"] if monthly_ctx else None
        monthly_low = monthly_ctx["monthly_low"] if monthly_ctx else None
        monthly_vwap = monthly_ctx["monthly_vwap"] if monthly_ctx else None

        # ======================
        # RETURN MODEL
        # ======================
        return SessionLevelsModel(
            date=date,
            session_name=session_name,
            instrument="MNQ",
            symbol=None,
            session_start=datetime.combine(date, session_cfg.open_time),
            session_end=datetime.combine(date, session_cfg.close_time),

            session_high=h,
            session_low=l,
            session_open=o,
            session_close=c,
            session_midpoint=(h + l) / 2,
            session_range=r,
            session_poc=poc,
            session_vah=vah,
            session_val=val,
            session_vwap=vwap,
            session_volume_total=total_vol,

            day_high=day_high,
            day_low=day_low,
            day_range=day_range,
            day_midpoint=day_mid,
            day_poc=day_poc,
            day_vah=day_vah,
            day_val=day_val,
            day_vwap=day_vwap,

            prev_day_high=prev_day_profile.get("high") if prev_day_profile else None,
            prev_day_low=prev_day_profile.get("low") if prev_day_profile else None,
            prev_day_poc=prev_poc,
            prev_day_vah=prev_vah,
            prev_day_val=prev_val,
            prev_day_vwap=prev_vwap,

            touched_prev_day_poc=touched_poc,
            touched_prev_day_vah=touched_vah,
            touched_prev_day_val=touched_val,
            touched_prev_day_vwap=touched_vwap,
            broke_prev_day_poc=broke_poc,
            broke_prev_day_vah=broke_vah,
            broke_prev_day_val=broke_val,
            broke_prev_day_vwap=broke_vwap,

            weekly_high=weekly_high,
            weekly_low=weekly_low,
            weekly_vwap=weekly_vwap,

            monthly_high=monthly_high,
            monthly_low=monthly_low,
            monthly_vwap=monthly_vwap,

            computation_timestamp=datetime.utcnow(),
            version=self.engine_version,
            config_snapshot={"session_levels": self.config},
            notes=None,
        )


        # ------------------------------------------------------------
    #  WEEKLY / MONTHLY GROUPING HELPERS
    # ------------------------------------------------------------

    def _group_bars_by_date(self):
        """
        Raggruppa le barre per data (YYYY-MM-DD).
        Restituisce un dict: {date: [bars]}
        """
        grouped = {}
        for b in self.bars:
            dt = b["time"].date()
            if dt not in grouped:
                grouped[dt] = []
            grouped[dt].append(b)
        return grouped


    def _group_bars_by_week(self) -> Dict[tuple[int, int], List[dict]]:
        """
        Raggruppa tutte le barre per settimana (anno, settimana ISO).
        """
        groups: Dict[tuple[int, int], List[dict]] = defaultdict(list)
        for bar in self.bars:
            dt: datetime = bar["time"]
            iso_year, iso_week, _ = dt.isocalendar()
            groups[(iso_year, iso_week)].append(bar)
        return groups

    def _group_bars_by_month(self) -> Dict[tuple[int, int], List[dict]]:
        """
        Raggruppa tutte le barre per mese (anno, mese).
        """
        groups: Dict[tuple[int, int], List[dict]] = defaultdict(list)
        for bar in self.bars:
            dt: datetime = bar["time"]
            groups[(dt.year, dt.month)].append(bar)
        return groups

    def _build_prev_profile(self, bars: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, float]]:
        """
        Costruisce un profilo sintetico (POC / VAH / VAL / VWAP) 
        da un insieme di barre (giorno precedente, settimana precedente, mese precedente).
        Se bars è None o vuoto, ritorna None.
        """
        if not bars:
            return None

        # Profilo volume
        vp = self._build_volume_profile(bars)
        poc, vah, val = self._compute_poc_vah_val(vp)

        # VWAP
        vwap = self._compute_vwap_for_bars(bars)

        return {
            "poc": poc,
            "vah": vah,
            "val": val,
            "vwap": vwap,
        }


    def _compute_vwap_for_bars(self, bars: List[dict]) -> Optional[float]:
        """
        VWAP semplice: sum(price*volume) / sum(volume) usando il close.
        """
        vol_sum = 0.0
        pv_sum = 0.0
        for b in bars:
            v = float(b.get("volume", 0.0) or 0.0)
            c = float(b.get("close", 0.0) or 0.0)
            vol_sum += v
            pv_sum += c * v

        if vol_sum <= 0:
            return None
        return pv_sum / vol_sum

    def _get_previous_day_bars(
        self,
        current_date: date,
        grouped_by_date: Dict[date, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Restituisce le barre del giorno precedente rispetto a current_date.
        Se non ci sono (es. weekend), restituisce lista vuota.
        """
        prev_date = current_date - timedelta(days=1)
        return grouped_by_date.get(prev_date, [])

    def _get_previous_week_bars(
        self,
        current_date: date,
        grouped_by_week: Dict[Tuple[int, int], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Restituisce le barre della settimana precedente (ISO week).
        Chiave: (anno, week).
        """
        year, week, _ = current_date.isocalendar()

        if week > 1:
            prev_key = (year, week - 1)
        else:
            # settimana 1 -> vado all'ultima settimana dell'anno precedente
            prev_key = (year - 1, 52)  # basta come approssimazione qui

        return grouped_by_week.get(prev_key, [])

    def _get_previous_month_bars(
        self,
        current_date: date,
        grouped_by_month: Dict[Tuple[int, int], List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Restituisce le barre del mese precedente.
        Chiave: (anno, mese).
        """
        year, month = current_date.year, current_date.month

        if month > 1:
            prev_key = (year, month - 1)
        else:
            prev_key = (year - 1, 12)

        return grouped_by_month.get(prev_key, [])

    
