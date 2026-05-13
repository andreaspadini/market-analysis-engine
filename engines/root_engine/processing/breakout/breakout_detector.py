from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from engines.root_engine.processing.breakout.schema import (
    BreakoutModel,
    BreakoutStrengthComponents,
    FollowThroughMetrics,
    PostBreakoutVolumeProfile,
    PreBreakoutSignal,
)
from engines.root_engine.processing.balance.schema import BalanceModel, RotationInfo

from engines.root_engine.processing.breakout.pre_breakout_detector import PreBreakoutDetector

import math


class BreakoutDetector:
    """
    Motore di breakout sopra le balances.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        bars: Optional[List[Dict]] = None,
        lower_tf_bars: Optional[List[Dict]] = None,
        rotations: Optional[List[RotationInfo]] = None,
        balances: Optional[List[BalanceModel]] = None,
    ):
        self.raw_config = config
        self.config = config.get("breakout", {}) or {}

        self.bars = bars or []
        self.lower_tf_bars = lower_tf_bars or []
        self.rotations = rotations or []
        self.balances = balances or []

        # nuovo modulo di pre-breakout
                # nuovo modulo di pre-breakout
        pre_cfg = self.raw_config.get("breakout", {}).get("pre_breakout", {})
        if pre_cfg.get("enabled", False):
            self.pre_breakout_detector = PreBreakoutDetector(config)
        else:
            self.pre_breakout_detector = None

        print(
            f"[BreakoutDetector:init] bars={len(self.bars)} | "
            f"lower_tf_bars={len(self.lower_tf_bars)} | "
            f"rotations={len(self.rotations)} | "
            f"balances={len(self.balances)}"
        )

        #self._validate_inputs()


    # ------------------------------------------------------------------
    # VALIDAZIONE INPUT
    # ------------------------------------------------------------------
    def _validate_inputs(self):
        if not isinstance(self.config, dict):
            raise ValueError("Config breakout non valida â€” deve essere un dict (sezione 'breakout' del config.yaml).")

        if len(self.bars) == 0:
            raise ValueError("BreakoutDetector richiede almeno 1 barra.")

        if len(self.balances) == 0:
            print("[BreakoutDetector] Nessuna balance trovata â€” nessun breakout possibile.")

    def detect_from_balances(
        self,
        balances: List[BalanceModel],
        bars: List[Dict],
        lower_tf_bars: Optional[List[Dict]] = None,
    ) -> List[BreakoutModel]:
        """
        API â€œpulitaâ€: balances + barre -> lista di BreakoutModel.
        """
        self.balances = balances
        self.bars = bars
        self.lower_tf_bars = lower_tf_bars or []

        return self.run()


        # ------------------------------------------------------------------
    # ENTRY POINT PRINCIPALE
    # ------------------------------------------------------------------
    def run(self) -> List[BreakoutModel]:
        self._validate_inputs()


        """
        PIPELINE COMPLETA:
        1) breakout strutturale
        2) conferma (opzionale)
        3) classificazione finale
        """

        print("[BreakoutDetector] Avvio esecuzione Breakout Engineâ€¦")

        breakouts: List[BreakoutModel] = []

        for balance_index, balance in enumerate(self.balances):

            # -------------------------
            # PRE-BREAKOUT SIGNAL
            # -------------------------
            pre_signal: Optional[PreBreakoutSignal] = None
            pre_cfg = self.raw_config.get("breakout", {}).get("pre_breakout", {})
            if pre_cfg.get("enabled", False):
                try:
                    pre_signal = self.pre_breakout_detector.evaluate(balance)
                except Exception as e:
                    print(f"[BreakoutDetector] Errore PreBreakout balance #{balance_index}: {e}")
                    pre_signal = None

            # -------------------------
            # STEP 1 â€” STRUTTURALE
            # -------------------------
            candidate = self._detect_structural_breakout_for_balance(balance_index, balance)

            if candidate is None:
                print(f"[BreakoutDetector] Nessun breakout strutturale per balance #{balance_index}")
                continue

            # portiamo il segnale dentro il candidate dict (serve per la conferma)
            candidate["pre_breakout_signal"] = pre_signal

            structural = self._build_breakout_model(
                balance_index=balance_index,
                balance=balance,
                bar_index=candidate["bar_index"],
                bar=candidate["bar"],
                direction=candidate["direction"],
                boundary_type=candidate["boundary_type"],
                boundary_price=candidate["boundary_price"],
                pre_breakout_signal=pre_signal,
            )

            # --- ROTATION CONTEXT ---
            rotation_ctx = self._build_rotation_context_from_balance(
                balance=balance,
                breakout_bar_index=structural.breakout_bar_index,
                breakout_direction=structural.direction,
            )


            structural.tags.append(
                f"rot_bias={rotation_ctx.get('directional_bias', 0.0):.2f}"
            )

            structural.rotation_context = rotation_ctx   # <-- opzionale ma consigliato
            
            # --- ROTATION FILTER (SOFT, SOLO TAG) ---
            filt = self.config.get("rotations_filter", {})

            min_rot = filt.get("min_rotations", 0)
            min_bias = filt.get("min_directional_bias", 0.0)

            if rotation_ctx["total_rotations"] < min_rot:
                structural.tags.append("rot_filter_low_count")

            if abs(rotation_ctx["directional_bias"]) < min_bias:
                structural.tags.append("rot_filter_low_bias")

       
            # -------------------------
            # STEP 2 â€” CONFIRMATION
            # -------------------------
            if self.config.get("confirmation", {}).get("enabled", False):

                confirmed = self._apply_confirmation_logic(candidate)

                if confirmed is None:
                    print(f"[BreakoutDetector] Breakout NON confermato per balance #{balance_index}")
                    continue  # <<< QUI ERA IL PROBLEMA

                breakout_final = confirmed

            else:
                breakout_final = structural

            # -------------------------
            # STEP 3 â€” CLASSIFICAZIONE
            # -------------------------
            breakout_final = self._classify_breakout(breakout_final)

            breakouts.append(breakout_final)

        # ------------------------------------------------------
        # EXPORT ANALITICO BREAKOUTS (CSV / DATASET ML)
        # ------------------------------------------------------
        try:
            from engines.root_engine.processing.breakout.breakout_export import export_breakouts_csv
            export_breakouts_csv(
                breakouts,
                self.raw_config,
                bars=self.bars
            )
        except Exception as e:
            print("[EXPORT ERROR]", str(e))



        print(f"[BreakoutDetector] STEP completato: breakouts trovati = {len(breakouts)}")
        return breakouts




    # ------------------------------------------------------------------
    # STEP 1: RICERCA BREAKOUT STRUTTURALE PER UNA BALANCE
    # ------------------------------------------------------------------
    def _detect_structural_breakout_for_balance(
        self,
        balance_index: int,
        balance: BalanceModel,
    ):
        """
        STEP 1 â€” Ricerca breakout strutturale coerente con il config.yaml.
        Supporta 3 modalitÃ :
            - strict
            - close_only
            - hybrid (body_50)
        """

        # ----------------------------------------------------------
        # 1) Trova indici della balance
        # ----------------------------------------------------------
        start_idx, end_idx = self._find_bar_indices_for_balance(balance)

        post_start = end_idx + 1
        if post_start >= len(self.bars):
            print(
                f"[BreakoutDetector] Nessuna barra disponibile dopo balance #{balance_index}."
            )
            return None

        # ----------------------------------------------------------
        # 2) Finestra di ricerca post-balance (configurabile)
        # ----------------------------------------------------------
        post_bars = self.config.get("post_balance_bars", 60)
        post_end = min(post_start + post_bars, len(self.bars) - 1)

        # ----------------------------------------------------------
        # 3) Boundaries della balance + modalitÃ  breakout
        # ----------------------------------------------------------
        b_high = balance.high
        b_low = balance.low

        mode = self.config.get("mode", "strict")

        # (opzionale) debug: forza il primo bar post-balance come breakout
        if self.config.get("debug_force_first_breakout", False):
            bar = self.bars[post_start]
            return {
                "bar_index": post_start,
                "bar": bar,
                "direction": "up",
                "boundary_type": "upper",
                "boundary_price": b_high,
                "balance_index": balance_index,
                "balance": balance,
            }

    

        # ----------------------------------------------------------
        # 4) Loop sulle barre post-balance
        # ----------------------------------------------------------
        previous_close = self.bars[end_idx]["close"]   # chiusura ultima barra della balance

        for i in range(post_start, post_end + 1):
            bar = self.bars[i]

            # 1) riconoscimento breakout strutturale
            result = self._is_structural_breakout_bar(
                bar=bar,
                previous_close=previous_close,
                balance_high=b_high,
                balance_low=b_low,
                mode=mode,
            )

            # aggiorno per la prossima iterazione
            previous_close = bar["close"]

            # Nessun breakout su questa barra â†’ passo alla successiva
            if result is None:
                continue

            # ------------------------------------------------------
            # 5) CONTESO ROTAZIONI pre-breakout (usiamo la funzione
            #    giÃ  esistente _extract_pre_breakout_rotations)
            # ------------------------------------------------------
            
            rot_ctx = self._build_rotation_context_from_balance(
                balance=balance,
                breakout_bar_index=i,
                breakout_direction=result["direction"],
            )



            
            # Filtro reale ma *non* blocchiamo il breakout nel dataset
            # sintetico: se vuoi che blocchi davvero, metti a True nel config:
            # breakout.rotations.require_structural_rotation: true
            rotations_cfg = self.config.get("rotations", {})
            require_struct = rotations_cfg.get("require_structural_rotation", False)

            if require_struct and rot_ctx["structural_count"] == 0:
                print(
                    "[BreakoutDetector] Breakout scartato: nessuna rotazione strutturale valida"
                )
                continue  # salta questo candidato e continua a cercare

            # Allego il contesto rotazioni al risultato
            result["rotation_context"] = rot_ctx

            # Completo il candidate con le info mancanti
            result.update(
                {
                    "bar_index": i,
                    "bar": bar,
                    "balance_index": balance_index,
                    "balance": balance,
                }
            )

            # Primo breakout valido trovato â†’ lo ritorno
            return result

        # ----------------------------------------------------------
        # Nessun breakout trovato nell'intera finestra
        # ----------------------------------------------------------
        print(
            f"[BreakoutDetector] Nessun breakout strutturale trovato per balance #{balance_index}"
        )
        return None



    # ------------------------------------------------------------------
    # COSTRUZIONE CONTESTO ROTAZIONI PER UN BREAKOUT
    # ------------------------------------------------------------------
    
    def _build_rotation_context_from_balance(
    self,
    balance: BalanceModel,
    breakout_bar_index: int,
    breakout_direction: str,
):
        """
        Costruisce il contesto rotazionale PRE-BREAKOUT
        usando ESCLUSIVAMENTE balance.rotations.
        """

        if not balance.rotations:
            return {
                "total_rotations": 0,
                "valid_rotations": 0,
                "micro_count": 0,
                "standard_count": 0,
                "structural_count": 0,
                "up_count": 0,
                "down_count": 0,
                "directional_bias": 0.0,
                "total_delta": 0.0,
                "total_volume": 0.0,
                "last_rotation_direction": None,
                "last_rotation_delta": 0.0,
                "last_rotation_volume": 0.0,
                "last_rotation_type": None,
                "last_rotation_valid": False,
                "validity_ratio": 0.0,
                "structural_ratio": 0.0,
                "rotation_alignment_score": 0.0,
            }

        breakout_time = self.bars[breakout_bar_index]["time"]

        pre_rotations = [
            r for r in balance.rotations
            if r.end_time <= breakout_time
        ]

        if not pre_rotations:
            return {
                "total_rotations": 0,
                "valid_rotations": 0,
                "micro_count": 0,
                "standard_count": 0,
                "structural_count": 0,
                "up_count": 0,
                "down_count": 0,
                "directional_bias": 0.0,
                "total_delta": 0.0,
                "total_volume": 0.0,
                "last_rotation_direction": None,
                "last_rotation_delta": 0.0,
                "last_rotation_volume": 0.0,
                "last_rotation_type": None,
                "last_rotation_valid": False,
                "validity_ratio": 0.0,
                "structural_ratio": 0.0,
                "rotation_alignment_score": 0.0,
            }

        total = len(pre_rotations)
        valid = sum(1 for r in pre_rotations if r.validity_flag)

        micro = sum(1 for r in pre_rotations if r.rotation_type == "micro")
        standard = sum(1 for r in pre_rotations if r.rotation_type == "standard")
        structural = sum(1 for r in pre_rotations if r.rotation_type == "structural")

        up = sum(1 for r in pre_rotations if r.direction == "up")
        down = sum(1 for r in pre_rotations if r.direction == "down")

        total_delta = sum(r.delta for r in pre_rotations)
        total_volume = sum(r.volume for r in pre_rotations)

        last = pre_rotations[-1]

        # --- Directional Bias ---
        directional_bias = (up - down) / max(1, total)

        # --- Rotation Alignment Score (pesato per tipo) ---
        type_weight = {
            "micro": 0.5,
            "standard": 1.0,
            "structural": 1.5,
        }

        aligned = [
            r for r in pre_rotations
            if r.direction == breakout_direction and r.validity_flag
        ]

        weighted_aligned = sum(
            abs(r.delta) * type_weight.get(r.rotation_type, 1.0)
            for r in aligned
        )

        weighted_total = sum(
            abs(r.delta) * type_weight.get(r.rotation_type, 1.0)
            for r in pre_rotations
        )

        rotation_alignment_score = (
            weighted_aligned / weighted_total
            if weighted_total > 0 else 0.0
        )

        return {
            "total_rotations": total,
            "valid_rotations": valid,
            "micro_count": micro,
            "standard_count": standard,
            "structural_count": structural,
            "up_count": up,
            "down_count": down,
            "directional_bias": directional_bias,
            "total_delta": total_delta,
            "total_volume": total_volume,
            "last_rotation_direction": last.direction,
            "last_rotation_delta": last.delta,
            "last_rotation_volume": last.volume,
            "last_rotation_type": last.rotation_type,
            "last_rotation_valid": last.validity_flag,
            "validity_ratio": valid / max(1, total),
            "structural_ratio": structural / max(1, total),
            "rotation_alignment_score": rotation_alignment_score,
        }


    # ----------------------------------------------------------------------
# MAPPATURA TEMPO -> INDICI BARRE (VERSIONE CORRETTA)
# ----------------------------------------------------------------------
    def _find_bar_indices_for_balance(self, balance: BalanceModel):
        """
        Trova gli indici (start_idx, end_idx) delle barre che appartengono
        alla finestra temporale della balance, usando start_time / end_time
        giÃ  presenti in BalanceModel.
        """

        start_dt = balance.start_time
        end_dt = balance.end_time

        start_idx = None
        end_idx = None

        for idx, bar in enumerate(self.bars):
            t = bar.get("time") or bar.get("timestamp")
            if t is None:
                continue

            # primo indice che entra nella balance
            if start_idx is None and t >= start_dt:
                start_idx = idx

            # finchÃ© la barra Ã¨ <= end_time, aggiorniamo end_idx
            if t <= end_dt:
                end_idx = idx

        if start_idx is None or end_idx is None:
            raise ValueError(
                f"[BreakoutDetector] Impossibile trovare indici per balance "
                f"(start_time={start_dt}, end_time={end_dt})"
            )

        return start_idx, end_idx



    # ------------------------------------------------------------------
# COSTRUZIONE DEL BreakoutModel (VERSIONE MINIMALE MA COERENTE)
# ------------------------------------------------------------------
    
    def _build_breakout_model(
        self,
        balance_index: int,
        balance: BalanceModel,
        bar_index: int,
        bar: Dict,
        direction: str,
        boundary_type: str,
        boundary_price: float,
        pre_breakout_signal: Optional[PreBreakoutSignal] = None,
    ) -> BreakoutModel:

        # --------------------------------------------------------------
        # Timestamp robusto
        # --------------------------------------------------------------
        breakout_time = bar.get("time") or bar.get("timestamp")

        breakout_price = bar["close"]
        volume = bar["volume"]
        delta = bar.get("delta", 0.0)

        # --------------------------------------------------------------
        # Strength calcolato realmente (STEP 2)
        # --------------------------------------------------------------
        strength = self._compute_strength_components(
            balance=balance,
            breakout_bar_index=bar_index,
            direction=direction,
            boundary_price=boundary_price,
        )
     

        early = self._detect_early_breakout(
            balance=balance,
            boundary_price=boundary_price,
            direction=direction,
            breakout_bar_index=bar_index,
        )

        if early:
            early_time = early["early_time"]
            early_price = early["early_price"]
            early_bar_index = early["early_bar_index"]
            early_timeframe = early["early_timeframe"]
            minutes_of_anticipation = early["lead_minutes"]

            early_tags = [
                "early_detected",
                f"early_{early['lead_minutes']:.1f}m"
            ]
        else:
            early_time = None
            early_price = None
            early_bar_index = None
            early_timeframe = None
            minutes_of_anticipation = None
            early_tags = []



        # --------------------------------------------------------------
        # Follow-through reale
        # --------------------------------------------------------------
        follow = self._compute_follow_through_metrics(
            breakout_index=bar_index,
            boundary_price=boundary_price,
            direction=direction,
        )

        post_profile = None

        # --------------------------------------------------------------
        # Info dal BalanceModel
        # --------------------------------------------------------------
        vpoc = balance.vpoc
        hvn = balance.hvn or []
        lvn = balance.lvn or []

        equilibrium_score = getattr(balance, "equilibrium_score", None)

        # -------------------------------------------------
        # ATR CALCULATION (FIX EXPORT)
        # -------------------------------------------------
        atr_cfg = self.config.get("atr", {})
        atr_period = atr_cfg.get("period", 14)

        atr_before = self._compute_atr(
            end_index=bar_index,
            period=atr_period,
        )

        # uso 5 barre dopo il breakout per lâ€™ATR post
        post_index = min(bar_index + 5, len(self.bars) - 1)

        atr_after = self._compute_atr(
            end_index=post_index,
            period=atr_period,
        )


        # --------------------------------------------------------------
        # Costruzione BreakoutModel
        # --------------------------------------------------------------
        instrument = ""
        timeframe = ""

        if isinstance(self.raw_config.get("dataset"), dict):
            instrument = self.raw_config["dataset"].get("instruments", [""])[0]
            timeframe = self.raw_config["dataset"].get("timeframe", "")

        if instrument in (None, "", "unknown"):
            instrument = "unknown"

        if timeframe in (None, "", "unknown"):
            timeframe = "unknown"

        breakout = BreakoutModel(
            breakout_id=f"bo_{balance_index}_{bar_index}",
            parent_balance_id=f"balance_{balance_index}",

            instrument=instrument,
            symbol=None,
            session_id="unknown",
            timeframe=timeframe,

            breakout_time=breakout_time,
            breakout_bar_index=bar_index,
            confirmation_time=None,
            confirmation_bar_index=None,
            computation_timestamp=datetime.utcnow(),
            version="0.2.0",

            direction=direction,
            breakout_type="clean",
            confirmation_status="pending",

            breakout_price=breakout_price,
            confirmation_price=None,

            boundary_price=boundary_price,
            boundary_type=boundary_type,

            balance_high=balance.high,
            balance_low=balance.low,
            balance_midpoint=balance.midpoint,
            balance_range_size=balance.range_size,
            balance_vpoc=vpoc,
            balance_hvn=hvn,
            balance_lvn=lvn,
            balance_equilibrium_score=equilibrium_score,
            balance_rotation_quality_score=None,
            balance_structural_integrity_score=None,

            initial_volume=volume,
            initial_volume_zscore=None,
            initial_delta=delta,
            delta_peak=None,
            delta_mean_post_breakout=None,

            atr_before=atr_before,
            atr_after=atr_after,

            strength_components=strength,
            follow_through=follow,
            post_breakout_volume_profile=post_profile,

            bar_count_initial_move=1,
            bars_observed=0,
            is_failed=False,
            is_retest_occurred=False,

            early_time=early_time,
            early_price=early_price,
            early_bar_index=early_bar_index,
            early_timeframe=early_timeframe,
            minutes_of_anticipation=minutes_of_anticipation,
            pre_breakout_signal=pre_breakout_signal,

            config_snapshot=self.config,
            tags=["step1_structural_only"] + early_tags,
            notes=None,
        )



        # --------------------------------------------------------------
        # âœ… TAG AUTOMATICO VOLATILITY FILTER (SOFT - INFORMATIVO)
        # --------------------------------------------------------------
        if getattr(strength, "volatility_filter_pass", True):
            if "volatility_confirmed" not in breakout.tags:
                breakout.tags.append("volatility_confirmed")
        else:
            if "volatility_rejected" not in breakout.tags:
                breakout.tags.append("volatility_rejected")

       
        return breakout


        # ------------------------------------------------------------------
    # REGOLA DI IDENTIFICAZIONE BREAKOUT STRUTTURALE
    # ------------------------------------------------------------------
    def _is_structural_breakout_bar(
        self,
        bar: Dict,
        previous_close: float,
        balance_high: float,
        balance_low: float,
        mode: str = "strict",
    ) -> Optional[Dict]:
        """
        Riconosce se una barra Ã¨ potenzialmente un breakout strutturale.

        ModalitÃ  supportate:
            - "strict":     breakout solo se TUTTA la barra Ã¨ fuori dal range
            - "close_only": breakout se la CHIUSURA rompe il range
            - "body_50":    breakout se il 50% del corpo Ã¨ fuori dal range
        """

        high = bar["high"]
        low = bar["low"]
        close = bar["close"]
        open_ = bar["open"]

        # --------------------------------------------------------
        # 1) STRICT MODE â†’ tutta la barra deve stare fuori dal range
        # --------------------------------------------------------
        if mode == "strict":
            if low > balance_high:
                return {"direction": "up", "boundary_price": balance_high, "boundary_type": "upper"}
            if high < balance_low:
                return {"direction": "down", "boundary_price": balance_low, "boundary_type": "lower"}
            return None

        # --------------------------------------------------------
        # 2) CLOSE ONLY MODE â†’ conta solo la chiusura
        # --------------------------------------------------------
        if mode == "close_only":
            if close > balance_high:
                return {"direction": "up", "boundary_price": balance_high, "boundary_type": "upper"}
            if close < balance_low:
                return {"direction": "down", "boundary_price": balance_low, "boundary_type": "lower"}
            return None

        # --------------------------------------------------------
        # 3) BODY_50 MODE â†’ almeno il 50% del corpo fuori dal range
        # --------------------------------------------------------
        if mode == "body_50":
            body_high = max(open_, close)
            body_low = min(open_, close)
            body_range = body_high - body_low

            # Nessun corpo â†’ no breakout
            if body_range <= 0:
                return None

            # Parte del corpo che Ã¨ fuori dal range
            portion_above = max(0.0, body_high - balance_high)
            portion_below = max(0.0, balance_low - body_low)

            # Porzione fuori rispetto al totale del corpo
            portion_outside = max(portion_above, portion_below)
            outside_fraction = portion_outside / body_range

            if outside_fraction >= 0.50:
                if portion_above > portion_below:
                    return {"direction": "up", "boundary_price": balance_high, "boundary_type": "upper"}
                else:
                    return {"direction": "down", "boundary_price": balance_low, "boundary_type": "lower"}

            return None

        # --------------------------------------------------------
        # default â†’ nessuna modalitÃ  riconosciuta
        # --------------------------------------------------------
        return None

    def _compute_atr(self, end_index: int, period: int = 14):
        """
        Calcola ATR classico sulle barre OHLC.
        """
        if end_index < 1:
            return 0.0

        start = max(1, end_index - period + 1)
        trs = []

        for i in range(start, end_index + 1):
            curr = self.bars[i]
            prev = self.bars[i - 1]

            high = curr["high"]
            low = curr["low"]
            prev_close = prev["close"]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            trs.append(tr)

        return sum(trs) / len(trs) if trs else 0.0


    def _compute_strength_components(
        self,
        balance: BalanceModel,
        breakout_bar_index: int,
        direction: str,
        boundary_price: float,
    ) -> BreakoutStrengthComponents:
        """
        Calcola i componenti di strength del breakout usando:
        - momentum normalizzato sul range della balance
        - delta vs media recente
        - volume spike (ratio vs media, con cap)
        - volatilitÃ  tramite ATR (se abilitato)
        - distanza dal VPOC normalizzata
        - relazione con LVN/HVN
        Tutto pesato secondo i parametri in config['breakout']['strength'].
        """

        strength_cfg = self.config.get("strength", {})
        atr_cfg = self.config.get("atr", {})

        # Pesi (giÃ  presenti nel tuo YAML)
        momentum_weight = strength_cfg.get("momentum_weight", 1.0)
        delta_weight = strength_cfg.get("delta_weight", 1.0)
        volume_weight = strength_cfg.get("volume_spike_weight", 1.0)
        volatility_weight = strength_cfg.get("volatility_weight", 1.0)
        vpoc_weight = strength_cfg.get("distance_from_vpoc_weight", 0.7)
        hvn_lvn_weight = strength_cfg.get("hvn_lvn_break_weight", 0.7)

        bar = self.bars[breakout_bar_index]
        close = bar["close"]
        open_ = bar["open"]
        volume = bar["volume"]
        delta = bar.get("delta", 0.0)

        brange = max(1e-6, balance.high - balance.low)

        # ---------------------------------------------------
        # 1) MOMENTUM (price change vs barra precedente)
        # ---------------------------------------------------
        prev_close = (
            self.bars[breakout_bar_index - 1]["close"]
            if breakout_bar_index > 0
            else open_
        )
        raw_momentum = abs(close - prev_close)
        # normalizzato sul range della balance, clamp a 1
        momentum_score = min(raw_momentum / brange, 1.0)

        # ---------------------------------------------------
        # 2) DELTA IMBALANCE (vs media recente)
        # ---------------------------------------------------
        delta_lookback = strength_cfg.get("delta_lookback_bars", 20)
        delta_cap = strength_cfg.get("delta_cap", 3.0)

        start_delta = max(0, breakout_bar_index - delta_lookback)
        deltas = [
            abs(self.bars[i].get("delta", 0.0))
            for i in range(start_delta, breakout_bar_index + 1)
        ]
        mean_delta = sum(deltas) / len(deltas) if deltas else 1.0

        delta_ratio = abs(delta) / mean_delta if mean_delta > 0 else 0.0
        # clamp a delta_cap e normalizza 0â€“1
        delta_score = min(delta_ratio, delta_cap) / max(delta_cap, 1e-6)

        # ---------------------------------------------------
        # 3) VOLUME SPIKE (ratio vs media, con cap)
        # ---------------------------------------------------
        vol_lookback = strength_cfg.get("volume_lookback_bars", 30)
        vol_cap = strength_cfg.get("volume_spike_cap", 3.0)

        start_vol = max(0, breakout_bar_index - vol_lookback)
        vols = [self.bars[i]["volume"] for i in range(start_vol, breakout_bar_index + 1)]
        avg_vol = sum(vols) / len(vols) if vols else 1.0

        vol_ratio = volume / avg_vol if avg_vol > 0 else 0.0
        volume_spike_score = min(vol_ratio, vol_cap) / max(vol_cap, 1e-6)

        # ---------------------------------------------------
        # 4) VOLATILITÃ€ via ATR (se abilitato)
        # ---------------------------------------------------
        if atr_cfg.get("enabled", False):
            atr_value = self._compute_atr(breakout_bar_index)
            # normalizza sul range balance per non avere valori enormi
            atr_norm = atr_value / brange if brange > 0 else 0.0
            atr_cap = atr_cfg.get("normalization_factor", 1.0)
            volatility_score = min(atr_norm / max(atr_cap, 1e-6), 1.0)
        else:
            # fallback: usa il momentum come proxy
            volatility_score = momentum_score

        # ============================================================
        # âœ… VOLATILITY FILTER (CONFIGURABILE)
        # ============================================================

        vol_cfg = self.config.get("volatility_filter", {})

        enable_filter = vol_cfg.get("enable_filter", True)

        if enable_filter and balance.volatility is not None:

            comp = balance.volatility.compression_ratio
            stab = balance.volatility.stability_score

            min_comp = vol_cfg.get("min_compression_ratio", 0.5)
            max_comp = vol_cfg.get("max_compression_ratio", 1.0)
            min_stab = vol_cfg.get("min_stability_score", 0.4)

            soft_penalty = vol_cfg.get("soft_penalty", 0.3)

            volatility_filter_pass = True

            # HARD REJECTION
            if comp < min_comp or comp > max_comp or stab < min_stab:
                volatility_filter_pass = False

            # SOFT PENALTY SE BORDERLINE
            if volatility_filter_pass:
                if comp < min_comp * 1.1 or stab < min_stab * 1.1:
                    volatility_score *= (1.0 - soft_penalty)

        else:
            volatility_filter_pass = True


        # ---------------------------------------------------
        # 5) DISTANZA DAL VPOC (piÃ¹ lontano â†’ piÃ¹ "escape")
        # ---------------------------------------------------
        vpoc = balance.vpoc
        dist_from_vpoc = abs(close - vpoc)
        # se ti allontani di metÃ  range ottieni scoreâ‰ˆ1
        vpoc_ref = strength_cfg.get("vpoc_ref_fraction", 0.5) * brange
        if vpoc_ref <= 0:
            distance_from_vpoc_score = 0.0
        else:
            distance_from_vpoc_score = min(dist_from_vpoc / vpoc_ref, 1.0)

        # ---------------------------------------------------
        # 6) HVN / LVN BREAK (molto grezzo ma utile)
        #    idea: meglio se rompi attraverso LVN vicini al boundary
        # ---------------------------------------------------
        hvn_levels = balance.hvn or []
        lvn_levels = balance.lvn or []

        hvn_lvn_break_score = 0.0
        tolerance = strength_cfg.get("hvn_lvn_tolerance_fraction", 0.1) * brange

        if direction == "up" and lvn_levels:
            # cerchiamo LVN sopra il mid / verso l'upper boundary
            lvn_relevant = [p for p in lvn_levels if p >= balance.midpoint]
            if lvn_relevant:
                nearest_lvn = min(lvn_relevant, key=lambda p: abs(p - close))
                if abs(close - nearest_lvn) <= tolerance:
                    hvn_lvn_break_score = 1.0

        elif direction == "down" and lvn_levels:
            lvn_relevant = [p for p in lvn_levels if p <= balance.midpoint]
            if lvn_relevant:
                nearest_lvn = min(lvn_relevant, key=lambda p: abs(p - close))
                if abs(close - nearest_lvn) <= tolerance:
                    hvn_lvn_break_score = 1.0

        # (in futuro potremo rifinire anche con HVN, per ora LVN-focus va bene)

        # --------------------------------------------------
        # 7) OVERALL SCORE PESATO (RAW)
        # --------------------------------------------------
        w_cfg = self.config.get("strength", {})

        momentum_weight = w_cfg.get("momentum_weight", 1.0)
        delta_weight = w_cfg.get("delta_weight", 1.0)
        volume_weight = w_cfg.get("volume_spike_weight", 1.0)
        volatility_weight = w_cfg.get("volatility_weight", 1.0)
        vpoc_weight = w_cfg.get("distance_from_vpoc_weight", 0.7)
        hvn_lvn_weight = w_cfg.get("hvn_lvn_break_weight", 0.7)

        total_weight = (
            momentum_weight
            + delta_weight
            + volume_weight
            + volatility_weight
            + vpoc_weight
            + hvn_lvn_weight
        )
        if total_weight <= 0:
            total_weight = 1.0

        raw_strength = (
            momentum_score * momentum_weight +
            delta_score * delta_weight +
            volume_spike_score * volume_weight +
            volatility_score * volatility_weight +
            distance_from_vpoc_score * vpoc_weight +
            hvn_lvn_break_score * hvn_lvn_weight
        )
            
        

                # --------------------------------------------------
        # 8) NORMALIZZAZIONE DELLO STRENGTH
        # --------------------------------------------------
        # raw_strength Ã¨ giÃ  calcolato sopra
        raw_strength_score = raw_strength          # <- lo teniamo come valore â€œgrezzoâ€
        overall_strength_score = raw_strength_score  # <- punto di partenza per la normalizzazione

        norm_cfg = self.config.get("strength_normalization", {})
        norm_enabled = norm_cfg.get("enabled", True)
        method = norm_cfg.get("method", "minmax")

        if norm_enabled:
            if method == "minmax":
                min_raw = norm_cfg.get("min_raw", 0.0)
                max_raw = norm_cfg.get("max_raw", 5.0)
                if max_raw > min_raw:
                    overall_strength_score = (raw_strength_score - min_raw) / (max_raw - min_raw)
                else:
                    overall_strength_score = 0.0

            elif method == "sigmoid":
                import math
                k = norm_cfg.get("sigmoid_k", 1.0)
                overall_strength_score = 1.0 / (1.0 + math.exp(-k * raw_strength_score))

            elif method == "tanh":
                import math
                overall_strength_score = 0.5 * (math.tanh(raw_strength_score) + 1.0)
            # else: lasciamo il raw cosÃ¬ com'Ã¨

        # clamp di sicurezza 0â€“1
        overall_strength_score = max(0.0, min(1.0, overall_strength_score))

        # (opzionale) semplice filtro di volatilitÃ , per ora sempre True
        volatility_filter_pass = True

        return BreakoutStrengthComponents(
            momentum_score=momentum_score,
            delta_imbalance_score=delta_score,
            volume_spike_score=volume_spike_score,
            volatility_score=volatility_score,
            distance_from_vpoc_score=distance_from_vpoc_score,
            hvn_lvn_break_score=hvn_lvn_break_score,

            # âœ… RAW + NORMALIZZATO (ENTRAMBI RICHIESTI DAL MODEL)
            overall_strength_score=raw_strength_score,
            overall_strength_normalized=overall_strength_score,

            volatility_filter_pass=volatility_filter_pass,
        )




    def _normalize_overall_strength(self, raw_score: float) -> float:
        """
        Normalizza overall_strength_score usando i parametri di config:
        strength_normalization:
        enabled: true/false
        method: "minmax" | "sigmoid" | "tanh"
        min_raw, max_raw, sigmoid_k
        """
        cfg = self.config.get("strength_normalization", {})
        if not cfg.get("enabled", False):
            return raw_score

        method = cfg.get("method", "minmax")
        min_raw = cfg.get("min_raw", 0.0)
        max_raw = cfg.get("max_raw", 5.0)
        k = cfg.get("sigmoid_k", 1.0)

        # sicurezza
        if max_raw <= min_raw:
            max_raw = min_raw + 1.0

        if method == "minmax":
            # scala lineare tra min_raw e max_raw, clamp 0â€“1
            norm = (raw_score - min_raw) / (max_raw - min_raw)
            return max(0.0, min(1.0, norm))

        mid = (min_raw + max_raw) / 2.0
        x = raw_score - mid

        if method == "sigmoid":
            # logistic centrata sul mid
            # valore tra ~0 e ~1
            norm = 1.0 / (1.0 + math.exp(-k * x))
            return norm

        if method == "tanh":
            # tanh centrata sul mid, rimappata in [0,1]
            norm = math.tanh(k * x)
            return 0.5 * (norm + 1.0)

        # fallback: nessuna trasformazione
        return raw_score



    def _apply_confirmation_logic(self, candidate: Dict) -> Optional[BreakoutModel]:
        """
        STEP 2 â€” Logica di conferma breakout basata su config.yaml.

        - Se confirmation.enabled = False â†’ ritorna direttamente il BreakoutModel strutturale
        (nessuna vera conferma, solo classificazione/strength/follow-through).
        - Se True â†’ richiede N chiusure oltre il boundary, opzionalmente
        con conferma di delta (directional).
        """

        cfg = self.config.get("confirmation", {})

        # Se la conferma Ã¨ disabilitata, ritorniamo None e lo step di classificazione
        # userÃ  comunque il breakout strutturale.
        if not cfg.get("enabled", False):
            print("[BreakoutDetector] Conferma disabilitata: uso solo breakout strutturale.")
            return None

        max_bars = cfg.get("max_bars", 10)
        closes_required = cfg.get("closes_required", 2)

        delta_confirm_enabled = cfg.get("delta_confirmation", False)
        delta_min_abs = cfg.get("delta_min_abs", 0.0)

        start_idx = candidate["bar_index"]
        direction = candidate["direction"]
        boundary = candidate["boundary_price"]

        confirm_count = 0
        delta_sum = 0.0  # cumulo delta sulle barre di conferma

        for i in range(start_idx + 1, min(start_idx + 1 + max_bars, len(self.bars))):
            bar_i = self.bars[i]
            close = bar_i["close"]
            bar_delta = bar_i.get("delta", 0.0)

            # --------------------------
            # 1) Condizione prezzo
            # --------------------------
            if direction == "up" and close > boundary:
                confirm_count += 1
                delta_sum += bar_delta
            elif direction == "down" and close < boundary:
                confirm_count += 1
                delta_sum += bar_delta
            else:
                # rientra nel range â†’ azzera la sequenza di conferme
                confirm_count = 0
                delta_sum = 0.0

            # --------------------------
            # 2) Controllo soglia
            # --------------------------
            if confirm_count >= closes_required:
                # Se non vogliamo conferma delta â†’ OK subito
                if not delta_confirm_enabled:
                    break

                # Se vogliamo conferma delta: il segno deve essere coerente
                if direction == "up":
                    if delta_sum < delta_min_abs:
                        # delta non abbastanza forte â†’ continuo a cercare
                        continue
                else:  # direction == "down"
                    if delta_sum > -delta_min_abs:
                        continue

                # Se arrivo qui: prezzo + delta OK
                break
        else:
            # il for Ã¨ terminato senza break â†’ nessuna conferma
            print(f"[BreakoutDetector] Breakout NON confermato per balance #{candidate['balance_index']}")
            return None

        # --------------------------
        # Costruiamo il BreakoutModel â€œconfermatoâ€
        # --------------------------
        breakout = self._build_breakout_model(
            balance_index=candidate["balance_index"],
            balance=candidate["balance"],
            bar_index=start_idx,              # barra di breakout originale
            bar=candidate["bar"],
            direction=direction,
            boundary_type=candidate["boundary_type"],
            boundary_price=boundary,
            pre_breakout_signal=candidate.get("pre_breakout_signal"),
        )

        breakout.confirmation_bar_index = i
        breakout.confirmation_price = self.bars[i]["close"]
        breakout.confirmation_status = "confirmed"

        breakout.tags.append("confirmed_step2_delta" if delta_confirm_enabled else "confirmed_step2")

        print(
            f"[BreakoutDetector] Breakout CONFERMATO per balance #{candidate['balance_index']} "
            f"al bar {i} (delta_sum={delta_sum:.1f})"
        )

        return breakout



    def _classify_breakout(self, breakout: BreakoutModel) -> BreakoutModel:
        """
        STEP 3 â€” Classificazione del breakout (configurabile via config.yaml)
        """

        cfg = self.config.get("classification", {})

        failure_retrace = cfg.get("failure_retrace_factor", 0.8)
        retest_window = cfg.get("retest_window", 20)
        accumulation_bars = cfg.get("accumulation_bars", 15)
        min_progress_factor = cfg.get("min_progress_factor", 0.3)

        ft = breakout.follow_through

        retr_ratio = 0.0
        if ft.max_excursion > 0:
            retr_ratio = ft.retracement_depth / ft.max_excursion

        progress_ratio = 0.0
        if breakout.balance_range_size and breakout.balance_range_size > 0:
            progress_ratio = ft.max_excursion / breakout.balance_range_size

        # --- 1) FAILED FOLLOW-THROUGH ---
        if ft.max_excursion <= 0 or progress_ratio < min_progress_factor:
            breakout.breakout_type = "failed_follow_through"
            breakout.is_failed = True
            breakout.tags.append("failed_follow_through")
            return breakout

        # --- 2) FALSE BREAKOUT (rientro oltre boundary osservato) ---
        if ft.failure_bars_from_breakout is not None:
            breakout.breakout_type = "false_breakout"
            breakout.is_failed = True
            breakout.tags.append("false_breakout")
            return breakout

        # --- 3) FALSE BREAKOUT (retracement ratio) ---
        if retr_ratio >= failure_retrace:
            breakout.breakout_type = "false_breakout"
            breakout.is_failed = True
            breakout.tags.append("false_breakout")
            return breakout

        # --- 4) RETEST ---
        if ft.time_to_retest_boundary is not None and ft.time_to_retest_boundary <= retest_window:
            breakout.breakout_type = "with_retest"
            breakout.is_retest_occurred = True
            breakout.tags.append("with_retest")
            return breakout

        # --- 5) ACCUMULATION ---
        if ft.max_excursion_bars >= accumulation_bars:
            breakout.breakout_type = "accumulation"
            breakout.tags.append("accumulation")
            return breakout

        # --- 6) CLEAN ---
        breakout.breakout_type = "clean"
        breakout.tags.append("clean")

        return breakout




    # ------------------------------------------------------------------
    # FOLLOW-THROUGH ENGINE (STEP 2)
    # ------------------------------------------------------------------

    def _compute_follow_through_metrics(
        self,
        breakout_index: int,
        boundary_price: float,
        direction: str,
    ):
        """
        STEP 3 â€” Calcolo follow-through statistico post-breakout.
        """

        cfg = self.config.get("follow_through", {})
        obs_bars = cfg.get("observation_bars", 40)
        retr_factor = cfg.get("retracement_factor", 0.5)

        start = breakout_index + 1
        end = min(start + obs_bars, len(self.bars))

        prices: list[float] = []
        volumes: list[float] = []

        for i in range(start, end):
            prices.append(self.bars[i]["close"])
            volumes.append(self.bars[i]["volume"])

        # =========================
        # CASO EDGE: nessuna barra dopo il breakout
        # =========================
        if not prices:
            breakout_price = self.bars[breakout_index]["close"]
            return FollowThroughMetrics(
                max_excursion=0.0,
                max_excursion_bars=0,
                close_after_n_bars=breakout_price,
                retracement_depth=0.0,
                retracement_bars=0,
                time_to_retest_boundary=None,
                boundary_hold_bars=None,
                failure_price=None,
                failure_bars_from_breakout=None,
                post_breakout_volatility=0.0,
                post_breakout_volume_mean=0.0,
            )

        # =========================
        # MAX EXCURSION
        # =========================
        if direction == "up":
            max_price = max(prices)
            max_excursion = max_price - boundary_price
            max_excursion_bars = prices.index(max_price)
        else:
            min_price = min(prices)
            max_excursion = boundary_price - min_price
            max_excursion_bars = prices.index(min_price)

        # =========================
        # RETRACEMENT
        # =========================
        if direction == "up":
            retracement_price = min(prices)
            retracement_depth = max_price - retracement_price
            retracement_bars = prices.index(retracement_price)
        else:
            retracement_price = max(prices)
            retracement_depth = retracement_price - min_price
            retracement_bars = prices.index(retracement_price)

        # =========================
        # RETEST / FALLIMENTO RISPETTO AL BOUNDARY
        # =========================
        time_to_retest_boundary = None
        failure_price = None
        failure_bars = None

        for j, p in enumerate(prices):
            if direction == "up":
                if time_to_retest_boundary is None and p <= boundary_price:
                    time_to_retest_boundary = j
                if p < boundary_price:
                    failure_price = p
                    failure_bars = j
                    break
            else:
                if time_to_retest_boundary is None and p >= boundary_price:
                    time_to_retest_boundary = j
                if p > boundary_price:
                    failure_price = p
                    failure_bars = j
                    break

        # =========================
        # VOLATILITÀ E VOLUME POST
        # =========================
        post_volatility = (
            sum(abs(prices[i] - prices[i - 1]) for i in range(1, len(prices)))
            / len(prices)
        )

        post_volume_mean = sum(volumes) / len(volumes)

        # =========================
        # OUTPUT FINALE
        # =========================
        return FollowThroughMetrics(
            max_excursion=max_excursion,
            max_excursion_bars=max_excursion_bars,
            close_after_n_bars=prices[-1],
            retracement_depth=retracement_depth,
            retracement_bars=retracement_bars,
            time_to_retest_boundary=time_to_retest_boundary,
            boundary_hold_bars=None,
            failure_price=failure_price,
            failure_bars_from_breakout=failure_bars,
            post_breakout_volatility=post_volatility,
            post_breakout_volume_mean=post_volume_mean,
        )


    def _detect_early_breakout(
        self,
        balance,
        boundary_price,
        direction,
        breakout_bar_index,
    ):
        cfg = self.config.get("early_detection", {}) or {}
        if not cfg.get("enabled", False):
            return None

        lower_tf = cfg.get("lower_timeframe", "1m")

        trigger_cfg = cfg.get("trigger", {}) or {}
        trigger_type = trigger_cfg.get("type", "close")
        min_consecutive = int(trigger_cfg.get("min_consecutive", 1))
        min_penetration = float(trigger_cfg.get("min_penetration", 0.0))

        max_lead_min = float(cfg.get("max_lead_minutes", 10))

        if not self.lower_tf_bars:
            return None

        if breakout_bar_index is None or breakout_bar_index >= len(self.bars):
            return None

        struct_bar_time = self.bars[breakout_bar_index]["time"]

        early_bars = [
            b for b in self.lower_tf_bars
            if balance.start_time <= b["time"] < struct_bar_time
        ]

        if not early_bars:
            return None

        valid_closes = []
        for b in early_bars:
            if trigger_type == "close":
                price = b.get("close")
            elif direction == "up":
                price = b.get("high")
            else:
                price = b.get("low")

            if price is None:
                valid_closes.clear()
                continue

            if direction == "up" and price > boundary_price + min_penetration:
                valid_closes.append(b)
            elif direction == "down" and price < boundary_price - min_penetration:
                valid_closes.append(b)
            else:
                valid_closes.clear()

            if len(valid_closes) >= min_consecutive:
                early_bar = valid_closes[0]

                delta_minutes = (struct_bar_time - early_bar["time"]).total_seconds() / 60
                if delta_minutes > max_lead_min:
                    return None

                return {
                    "early_time": early_bar["time"],
                    "early_price": early_bar.get("close"),
                    "early_bar_index": early_bar.get("index"),
                    "early_timeframe": lower_tf,
                    "lead_minutes": delta_minutes,
                }

        return None

