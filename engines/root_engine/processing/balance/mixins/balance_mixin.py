from __future__ import annotations

from typing import List
from ..schema import RotationInfo

from engines.root_engine.models.balance_info import (
    BalanceInfo,
    BalanceClassification,
    PreBreakoutSignals,
)

from engines.root_engine.models.volume_profile_stats import VolumeProfileStats


import numpy as np

from engines.root_engine.utils.logger import logger
from ..schema import BalanceModel, VolatilityMetrics, EdgeCaseSignals
from datetime import datetime


class BalanceMixin:
    """
    Primo scaffolding del Balance Detector.
    La logica sarà implementata passo per passo.
    """

    def detect_balances(self, rotations: List[RotationInfo]) -> List[BalanceInfo]:
        logger.debug("Detecting balances: received %d rotations", len(rotations))

        if not rotations:
            logger.debug("No rotations provided -> returning empty balance list")
            self._balances_models = []
            return []
        
        valid_rotations = [r for r in rotations if getattr(r, "validity_flag", True)]
        logger.debug(
            "Detecting balances: valid rotations after filtering = %d / %d",
            len(valid_rotations),
            len(rotations),
        )

        if not valid_rotations:
            logger.debug("No valid rotations provided -> returning empty balance list")
            self._balances_models = []
            return []

        rotations = valid_rotations
        print(
            "[BAL DBG]",
            {
                "input_rotations": len(rotations),
                "valid_rotations": len(valid_rotations),
            },
        )

        cfg = self.config["balance"]
        logger.debug("Loaded balance config keys: %s", list(cfg.keys()))

        # ----- CLUSTERING -----
        clusters = self._cluster_rotations_into_balances(rotations, cfg)
        logger.info("Cluster trovati: %d", len(clusters))

        balances: List[BalanceInfo] = []
        balances_models: List[BalanceModel] = []

        for i, cluster in enumerate(clusters):
            logger.debug("Processing cluster %d con %d rotazioni", i, len(cluster))

            if not cluster:
                continue

            start_time = min(rot.start_time for rot in cluster)
            end_time   = max(rot.end_time for rot in cluster)

            bars = self._get_bars_for_cluster(cluster)
            if not bars:
                continue

            highs = [b["high"] for b in bars]
            lows  = [b["low"]  for b in bars]
            if not highs or not lows:
                continue

            width = max(highs) - min(lows)

            # ----- FILTRI BASE -----
            if not self._passes_basic_filters(bars, cluster, cfg):
                continue

            # ============================
            # ✅ VOLUME PROFILE (COMPATIBILE CON BalanceModel)
            # ============================

            vp_cfg = cfg.get("volume_profile", {})
            volume_stats = self._compute_volume_profile(bars, vp_cfg)

            if volume_stats is None:
                vp_profile = []
                vp_vpoc = 0.0
                vp_hvn = []
                vp_lvn = []
                vp_total_vol = 0.0
                vp_total_delta = 0.0
            else:
                raw_vp = volume_stats.volume_by_price

                vp_profile = []

                # ✅ CASO 1: dict {price: volume}
                if isinstance(raw_vp, dict):
                    for price, volume in raw_vp.items():
                        vp_profile.append({
                            "price": float(price),
                            "volume": float(volume),
                            "bid": 0.0,
                            "ask": 0.0,
                            "delta": 0.0,
                        })

                # ✅ CASO 2: list di tuple [(price, volume)]
                elif isinstance(raw_vp, list):
                    for item in raw_vp:
                        if len(item) >= 2:
                            vp_profile.append({
                                "price": float(item[0]),
                                "volume": float(item[1]),
                                "bid": 0.0,
                                "ask": 0.0,
                                "delta": 0.0,
                            })

                vp_vpoc = float(getattr(volume_stats, "poc_price", 0.0))
                vp_hvn = list(getattr(volume_stats, "hvn_levels", []))
                vp_lvn = list(getattr(volume_stats, "lvn_levels", []))
                vp_total_vol = float(getattr(volume_stats, "total_volume", 0.0))

                # ✅ Delta coerente dai bar
                vp_total_delta = sum(float(b.get("delta", 0.0)) for b in bars)



            # ----- CLASSIFICAZIONE -----
            cls_cfg = cfg.get("classification", {})
            classification = self._classify_balance(width, volume_stats, cls_cfg)

            # ----- BUILD BALANCE INFO (LEGACY) -----
            balance = BalanceInfo(
                high=max(highs),
                low=min(lows),
                mid_price=(max(highs) + min(lows)) / 2,
                width=width,

                start_time=start_time,
                end_time=end_time,
                duration_bars=len(bars),

                num_rotations=len(cluster),
                rotation_ids=[rot.index for rot in cluster],

                symmetry=0.0,
                internal_whipsaw=0.0,
                residual_directionality=0.0,
                internal_momentum=0.0,
                up_down_rotation_ratio=0.0,
                range_compression=0.0,

                volume_stats=volume_stats,
                classification=classification,
                equilibrium_score=0.0,
                pre_breakout_signals=PreBreakoutSignals(),
            )

            balances.append(balance)

            # ============================
            # ✅ VOLATILITÀ
            # ============================
            vol_dict = self._compute_volatility_metrics(bars)

            # ============================
            # ✅ BUILD BALANCE MODEL (FULL)
            # ============================
            balance_model = BalanceModel(
                balance_id=f"bal_{i}",
                instrument=bars[0].get("instrument", "unknown"),
                symbol=bars[0].get("symbol"),
                session_id=bars[0].get("session_id", "unknown"),
                timeframe=bars[0].get("timeframe", "unknown"),

                start_time=start_time,
                end_time=end_time,
                duration_seconds=len(bars),

                high=max(highs),
                low=min(lows),
                midpoint=(max(highs) + min(lows)) / 2,
                range_size=width,
                effective_range_size=None,

                rotations=cluster,
                total_rotations=len(cluster),
                valid_rotations=sum(1 for r in cluster if r.validity_flag),
                rotation_quality_score=0.0,

                bars_count=len(bars),

                volatility=VolatilityMetrics(
                    internal_volatility=vol_dict["std"],
                    volatility_spikes=[],
                    compression_ratio=vol_dict["compression_ratio"],
                    stability_score=vol_dict["stability_score"],
                ),

                avg_candle_range=width / max(1, len(bars)),
                relative_volatility_rank=0.0,

                volume_profile=list(vp_profile) if vp_profile is not None else [],

                total_volume=vp_total_vol,
                total_delta=vp_total_delta,
                vpoc=vp_vpoc,
                hvn=vp_hvn,
                lvn=vp_lvn,
                volume_symmetry_score=0.0,

                session_gap=0.0,
                contextual_gap=0.0,
                session_interruption_windows=[],

                structural_integrity_score=0.0,

                compression_validity_flag=True,
                balance_validity_flag=True,

                edge_cases=EdgeCaseSignals(),
                config_snapshot=cfg,
                computation_timestamp=datetime.utcnow(),
                version="1.0"
            )

            balances_models.append(balance_model)

        logger.info("Cluster validi: %d", len(balances))

        # ✅ ESPONE I MODELLI COMPLETI AL detect_balances_full
        self._balances_models = balances_models

        return balances






        # -------------------------------------------------------------------------
    # Step 3: clustering rotazioni → balance candidates
    # -------------------------------------------------------------------------

    def _cluster_rotations_into_balances(self, rotations, cfg):
        logger.debug("Starting clustering: %d rotations received", len(rotations))

        clusters = []
        current = []

        for rot in rotations:

            # primo elemento del cluster
            if not current:
                logger.debug("Starting new cluster with rotation %d", rot.index)
                current.append(rot)
                continue

            prev = current[-1]

            gap_seconds = (rot.start_time - prev.end_time).total_seconds()
            max_gap_seconds = cfg["max_gap_bars"] * 60

            logger.debug(
                "Rotation %d -> gap=%.2f sec (max allowed %.2f)",
                rot.index, gap_seconds, max_gap_seconds
            )

            # se gap eccessivo chiudiamo il cluster
            if gap_seconds > max_gap_seconds:
                logger.debug(
                    "Gap exceeded -> closing cluster of size %d", len(current)
                )
                if self._cluster_valid(current, cfg):
                    clusters.append(current)
                else:
                    logger.debug("Cluster REJECTED: too small")
                current = [rot]
                continue

            # calcolo width temporaneo del cluster
            temp_cluster = current + [rot]
            highs = [max(r.start_price, r.end_price) for r in temp_cluster]
            lows = [min(r.start_price, r.end_price) for r in temp_cluster]
            width = max(highs) - min(lows)

            logger.debug(
                "Cluster width check: width=%.4f (max allowed=%.4f)",
                width, cfg["max_width"]
            )

            if cfg["max_width"] is not None and width > cfg["max_width"]:
                logger.debug(
                    "Width exceeded -> closing cluster of size %d", len(current)
                )
                if self._cluster_valid(current, cfg):
                    clusters.append(current)
                else:
                    logger.debug("Cluster REJECTED: too small")
                current = [rot]
            else:
                current.append(rot)

        # fine rotazioni: chiudiamo cluster finale
        if current:
            if self._cluster_valid(current, cfg):
                logger.debug("Final cluster accepted (size %d)", len(current))
                clusters.append(current)
            else:
                logger.debug("Final cluster REJECTED: too small")

        logger.info("Clustering complete -> %d valid clusters", len(clusters))
        return clusters


    def _cluster_valid(self, cluster, cfg):
        is_valid = len(cluster) >= cfg["min_rotations"]
        logger.debug(
            "Cluster validation: size=%d -> valid=%s",
            len(cluster), is_valid
        )
        return is_valid




        # -------------------------------------------------------------------------
    # Step 5: estrazione delle barre di un cluster di rotazioni
    # -------------------------------------------------------------------------

    def _get_bars_for_cluster(self, cluster):
        """
        Estrae le barre appartenenti al cluster in base a start_time / end_time.
        Usa i timestamp, non gli indici (perché RotationInfo non li ha).
        """

        if not cluster:
            logger.debug("get_bars_for_cluster: empty cluster -> returning []")
            return []

        cluster_start = min(rot.start_time for rot in cluster)
        cluster_end = max(rot.end_time for rot in cluster)

        logger.debug(
            "Extracting bars for cluster (size=%d) -> time range %s -> %s",
            len(cluster), cluster_start, cluster_end
        )

        # estrazione effettiva
        bars = [
            b for b in self.bars
            if b["time"] >= cluster_start and b["time"] <= cluster_end
        ]

        logger.debug(
            "Bars extracted: %d bars found within time window",
            len(bars)
        )

        return bars




  
        # -------------------------------------------------------------------------
    # Step 6: filtri base su ampiezza, durata, volume
    # -------------------------------------------------------------------------

    def _passes_basic_filters(self, bars, cluster, cfg):
        """
        Filtri base di validazione cluster - VERSIONE SOFT
        Agiscono PRIMA della creazione del BalanceModel.
        """

        # 1️⃣ MIN ROTATIONS
        min_rot = cfg.get("min_rotations")
        if min_rot is not None and len(cluster) < min_rot:
            logger.debug(
                "Cluster rejected: len=%d < min_rotations=%d",
                len(cluster), min_rot
            )
            return False

        # 2️⃣ MIN BARS (stimiamo dai tempi)
        min_bars = cfg.get("min_bars")
        if min_bars is not None:
            start = cluster[0].start_time
            end = cluster[-1].end_time
            duration_minutes = (end - start).total_seconds() / 60

            if duration_minutes < min_bars:
                logger.debug(
                    "Cluster rejected: duration=%.2f < min_bars=%d",
                    duration_minutes, min_bars
                )
                return False

        # 3️⃣ MIN WIDTH
        min_width = cfg.get("min_width")
        if min_width is not None:
            highs = [max(r.start_price, r.end_price) for r in cluster]
            lows = [min(r.start_price, r.end_price) for r in cluster]
            width = max(highs) - min(lows)

            if width < min_width:
                logger.debug(
                    "Cluster rejected: width=%.4f < min_width=%.4f",
                    width, min_width
                )
                return False

        # 4️⃣ MAX WIDTH
        max_width = cfg.get("max_width")
        if max_width is not None:
            highs = [max(r.start_price, r.end_price) for r in cluster]
            lows = [min(r.start_price, r.end_price) for r in cluster]
            width = max(highs) - min(lows)

            if width > max_width:
                logger.debug(
                    "Cluster rejected: width=%.4f > max_width=%.4f",
                    width, max_width
                )
                return False
        
        return True



        # -------------------------------------------------------------------------
    # Volume profile locale (POC / HVN / LVN + statistiche base)
    # -------------------------------------------------------------------------

    def _compute_volume_profile(self, bars, cfg_vp) -> VolumeProfileStats:
        """
        Costruisce un volume profile semplice usando i prezzi di close
        e calcola POC, HVN, LVN e alcune statistiche.
        """

        logger.debug(
            "_compute_volume_profile: start | bars=%d | cfg=%s",
            len(bars), cfg_vp
        )

        # ------------------------------------------------------------------
        # Caso no-bars
        # ------------------------------------------------------------------
        if not bars:
            logger.debug("_compute_volume_profile: no bars -> returning empty profile")
            return VolumeProfileStats(
                poc_price=0.0,
                poc_volume=0.0,
                hvn_levels=[],
                lvn_levels=[],
                total_volume=0.0,
                volume_by_price={},
                skewness=0.0,
                kurtosis=0.0,
                concentration=0.0,
                asymmetry=0.0,
                density_around_mid=0.0,
                volume_upper_boundary=0.0,
                volume_lower_boundary=0.0,
                profile_width=0.0,
                concentration_factor=0.0,
                overlapping_factor=0.0,
                volume_balance_upper_vs_lower=0.0,
            )

        prices = np.array([b["close"] for b in bars], dtype=float)
        volumes = np.array([b["volume"] for b in bars], dtype=float)

        total_volume = float(volumes.sum())
        min_p = float(prices.min())
        max_p = float(prices.max())

        logger.debug(
            "Price range: min=%.4f max=%.4f | total_volume=%.2f",
            min_p, max_p, total_volume
        )

        bin_size = float(cfg_vp["bin_size"])

        # ------------------------------------------------------------------
        # Costruzione bin edges
        # ------------------------------------------------------------------
        if max_p == min_p:
            max_p = min_p + bin_size

        bin_edges = np.arange(min_p, max_p + bin_size, bin_size)
        if len(bin_edges) < 2:
            bin_edges = np.array([min_p, min_p + bin_size])

        vol_by_bin, _ = np.histogram(prices, bins=bin_edges, weights=volumes)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

        logger.debug(
            "Computed %d bins | bin_size=%.4f",
            len(vol_by_bin), bin_size
        )

        volume_by_price = {float(p): float(v) for p, v in zip(bin_centers, vol_by_bin)}

        # ------------------------------------------------------------------
        # POC
        # ------------------------------------------------------------------
        poc_idx = int(np.argmax(vol_by_bin))
        poc_price = float(bin_centers[poc_idx])
        poc_volume = float(vol_by_bin[poc_idx])

        logger.debug(
            "POC detected at price %.4f with volume %.2f",
            poc_price, poc_volume
        )

        mean_vol = float(vol_by_bin.mean()) if len(vol_by_bin) > 0 else 0.0

        # ------------------------------------------------------------------
        # HVN / LVN detection
        # ------------------------------------------------------------------
        hvn_levels = []
        lvn_levels = []

        if mean_vol > 0:
            hvn_thr = cfg_vp["hvn_threshold_factor"] * mean_vol
            lvn_thr = cfg_vp["lvn_threshold_factor"] * mean_vol

            hvn_levels = [
                float(bin_centers[i])
                for i, v in enumerate(vol_by_bin)
                if v > hvn_thr
            ]
            lvn_levels = [
                float(bin_centers[i])
                for i, v in enumerate(vol_by_bin)
                if v < lvn_thr
            ]

        logger.debug(
            "HVN count=%d | LVN count=%d",
            len(hvn_levels), len(lvn_levels)
        )

        # ------------------------------------------------------------------
        # Skewness & kurtosis
        # ------------------------------------------------------------------
        if total_volume > 0:
            probs = vol_by_bin / total_volume
            mean_price = float((bin_centers * probs).sum())
            diffs = bin_centers - mean_price
            var = float((diffs**2 * probs).sum())
            std = float(np.sqrt(max(var, 1e-9)))

            skewness = float((diffs**3 * probs).sum() / (std**3))
            kurtosis = float((diffs**4 * probs).sum() / (std**4))

            logger.debug(
                "Distribution stats -> mean_price=%.4f | skew=%.4f | kurt=%.4f",
                mean_price, skewness, kurtosis
            )
        else:
            skewness = 0.0
            kurtosis = 0.0

        # ------------------------------------------------------------------
        # Concentrazione attorno al POC
        # ------------------------------------------------------------------
        window_poc = float(cfg_vp["window_around_poc"])
        mask_poc = np.abs(bin_centers - poc_price) <= window_poc
        concentration = float(vol_by_bin[mask_poc].sum() / max(total_volume, 1e-9))

        # ------------------------------------------------------------------
        # Asimmetria rispetto al mid-price
        # ------------------------------------------------------------------
        mid_price = (min_p + max_p) / 2.0
        vol_above = float(vol_by_bin[bin_centers > mid_price].sum())
        vol_below = float(vol_by_bin[bin_centers <= mid_price].sum())

        asymmetry = float((vol_above - vol_below) / max(total_volume, 1e-9)) if total_volume > 0 else 0.0

        # ------------------------------------------------------------------
        # Densità attorno al mid-price
        # ------------------------------------------------------------------
        window_mid = float(cfg_vp["window_around_mid"])
        mask_mid = np.abs(bin_centers - mid_price) <= window_mid
        density_around_mid = float(vol_by_bin[mask_mid].sum() / max(total_volume, 1e-9))

        # ------------------------------------------------------------------
        # Boundary volumes
        # ------------------------------------------------------------------
        volume_lower_boundary = float(vol_by_bin[0]) if len(vol_by_bin) > 0 else 0.0
        volume_upper_boundary = float(vol_by_bin[-1]) if len(vol_by_bin) > 0 else 0.0

        profile_width = float(max_p - min_p)

        if vol_below > 0:
            volume_balance_upper_vs_lower = float(vol_above / vol_below)
        else:
            volume_balance_upper_vs_lower = float("inf") if vol_above > 0 else 1.0

        logger.debug(
            "Profile summary: width=%.4f | concentration=%.4f | asymmetry=%.4f | upper/lower=%.4f",
            profile_width, concentration, asymmetry, volume_balance_upper_vs_lower
        )

        return VolumeProfileStats(
            poc_price=poc_price,
            poc_volume=poc_volume,
            hvn_levels=hvn_levels,
            lvn_levels=lvn_levels,
            total_volume=total_volume,
            volume_by_price=volume_by_price,
            skewness=skewness,
            kurtosis=kurtosis,
            concentration=concentration,
            asymmetry=asymmetry,
            density_around_mid=density_around_mid,
            volume_upper_boundary=volume_upper_boundary,
            volume_lower_boundary=volume_lower_boundary,
            profile_width=profile_width,
            concentration_factor=concentration,
            overlapping_factor=0.0,
            volume_balance_upper_vs_lower=volume_balance_upper_vs_lower,
        )


    def _classify_balance(
    self,
    width: float,
    profile: VolumeProfileStats,
    cfg: dict,
) -> BalanceClassification:
        """
        Classificazione base della balance usando width e volume profile.
        Tutte le soglie sono configurabili in config.yaml sotto balance.classification.
        """

        logger.debug(
            "_classify_balance: start | width=%.4f | profile_width=%.4f | cfg=%s",
            width, profile.profile_width, cfg
        )

        # valori di default se qualcosa manca nel YAML
        compressed_factor = cfg.get("compressed_width_factor", 0.25)
        wide_factor = cfg.get("wide_width_factor", 1.75)
        asym_thr = cfg.get("asymmetry_threshold", 0.25)
        center_vol_thr = cfg.get("center_volume_threshold", 0.35)
        edge_vol_thr = cfg.get("edge_volume_threshold", 0.20)
        hvn_density_thr = cfg.get("hvn_density_threshold", 0.20)
        lvn_density_thr = cfg.get("lvn_density_threshold", 0.10)

        cls = BalanceClassification(
            balance_standard=False,
            balance_wide=False,
            balance_compressed=False,
            balance_asymmetric=False,
            balance_high_volume_center=False,
            balance_edge_volume_concentrated=False,
        )

        # -----------------------------
        # 1) WIDTH classification
        # -----------------------------
        pw = max(profile.profile_width, 1e-9)
        ratio = width / pw

        logger.debug(
            "Width analysis: width=%.4f | profile_width=%.4f | ratio=%.4f | compressed<=%.2f | wide>=%.2f",
            width, pw, ratio, compressed_factor, wide_factor
        )

        if ratio <= compressed_factor:
            cls.balance_compressed = True
            logger.debug("Width classification -> COMPRESSED")
        elif ratio >= wide_factor:
            cls.balance_wide = True
            logger.debug("Width classification -> WIDE")
        else:
            cls.balance_standard = True
            logger.debug("Width classification -> STANDARD")

        # -----------------------------
        # 2) ASIMMETRIA
        # -----------------------------
        logger.debug("Asymmetry check: asym=%.4f | threshold=%.4f",
                    profile.asymmetry, asym_thr)

        if abs(profile.asymmetry) >= asym_thr:
            cls.balance_asymmetric = True
            logger.debug("Asymmetry classification -> ASYMMETRIC")

        # -----------------------------
        # 3) HIGH VOLUME CENTER
        # -----------------------------
        logger.debug(
            "Center density: %.4f | threshold=%.4f",
            profile.density_around_mid, center_vol_thr
        )

        if profile.density_around_mid >= center_vol_thr:
            cls.balance_high_volume_center = True
            logger.debug("Volume center classification -> HIGH_VOLUME_CENTER")

        # -----------------------------
        # 4) EDGE VOLUME CONCENTRATED
        # -----------------------------
        edge_volume_ratio = (
            (profile.volume_upper_boundary + profile.volume_lower_boundary)
            / max(profile.total_volume, 1e-9)
        )

        logger.debug(
            "Edge volume: upper=%.2f lower=%.2f total=%.2f | ratio=%.4f | threshold=%.4f",
            profile.volume_upper_boundary,
            profile.volume_lower_boundary,
            profile.total_volume,
            edge_volume_ratio,
            edge_vol_thr
        )

        if edge_volume_ratio >= edge_vol_thr:
            cls.balance_edge_volume_concentrated = True
            logger.debug("Edge volume -> EDGE_CONCENTRATED")

        # -----------------------------
        # 5) HVN / LVN densities (solo log informativo)
        # -----------------------------
        num_price_levels = max(len(profile.volume_by_price), 1)
        hvn_density = len(profile.hvn_levels) / num_price_levels
        lvn_density = len(profile.lvn_levels) / num_price_levels

        logger.debug(
            "HVN density=%.4f | LVN density=%.4f | hvn_thr=%.4f | lvn_thr=%.4f",
            hvn_density, lvn_density, hvn_density_thr, lvn_density_thr
        )

        logger.debug("_classify_balance: result=%s", cls.dict()
)

        return cls



    def _compute_equilibrium_score(self, balance: BalanceInfo, cfg: dict) -> float:
        """
        Versione 1.0: score tra 0 e 1 che misura la "pulizia" della balance.
        Usa metriche semplici e stabili.
        """

        profile = balance.volume_stats

        logger.debug(
            "_compute_equilibrium_score: start | width=%.4f | profile_width=%.4f",
            balance.width,
            profile.profile_width,
        )

        # ---- parametri da config con default di sicurezza ----
        w_width = cfg.get("w_width", 0.20)
        w_asym = cfg.get("w_asymmetry", 0.20)
        w_center = cfg.get("w_center_volume", 0.25)
        w_hvn = cfg.get("w_hvn_density", 0.15)
        w_lvn = cfg.get("w_lvn_density", 0.10)
        w_edge = cfg.get("w_edge_volume", 0.10)

        asym_ref = cfg.get("asymmetry_ref", 0.5)
        center_ref = cfg.get("center_volume_ref", 0.4)
        hvn_ref = cfg.get("hvn_density_ref", 0.25)
        lvn_ref = cfg.get("lvn_density_ref", 0.15)
        edge_ref = cfg.get("edge_volume_ref", 0.1)

        weight_sum = max(
            w_width + w_asym + w_center + w_hvn + w_lvn + w_edge,
            1e-9,
        )

        # ---- 1) WIDTH score ----
        pw = max(profile.profile_width, 1e-9)
        width_ratio = balance.width / pw
        width_score = max(0.0, 1.0 - abs(width_ratio - 1.0))

        logger.debug(
            "Width score: width_ratio=%.4f -> %.4f (w=%.2f)",
            width_ratio, width_score, w_width
        )

        # ---- 2) ASYMMETRY score ----
        asym = abs(profile.asymmetry)
        asym_score = max(0.0, 1.0 - asym / max(asym_ref, 1e-9))

        logger.debug(
            "Asymmetry score: asym=%.4f ref=%.4f -> %.4f (w=%.2f)",
            asym, asym_ref, asym_score, w_asym
        )

        # ---- 3) CENTER VOLUME ----
        center_vol = profile.density_around_mid
        center_score = min(center_vol / max(center_ref, 1e-9), 1.0)

        logger.debug(
            "Center volume score: center=%.4f ref=%.4f -> %.4f (w=%.2f)",
            center_vol, center_ref, center_score, w_center
        )

        # ---- 4) HVN density ----
        num_levels = max(len(profile.volume_by_price), 1)
        hvn_density = len(profile.hvn_levels) / num_levels
        hvn_score = max(0.0, 1.0 - abs(hvn_density - hvn_ref) / max(hvn_ref, 1e-9))

        logger.debug(
            "HVN score: hvn_density=%.4f ref=%.4f -> %.4f (w=%.2f)",
            hvn_density, hvn_ref, hvn_score, w_hvn
        )

        # ---- 5) LVN density ----
        lvn_density = len(profile.lvn_levels) / num_levels
        lvn_score = max(0.0, 1.0 - abs(lvn_density - lvn_ref) / max(lvn_ref, 1e-9))

        logger.debug(
            "LVN score: lvn_density=%.4f ref=%.4f -> %.4f (w=%.2f)",
            lvn_density, lvn_ref, lvn_score, w_lvn
        )

        # ---- 6) Edge volume ----
        edge_ratio = (
            (profile.volume_upper_boundary + profile.volume_lower_boundary)
            / max(profile.total_volume, 1e-9)
        )

        if edge_ratio <= edge_ref:
            edge_score = 1.0
        else:
            edge_score = max(0.0, 1.0 - (edge_ratio - edge_ref) / max(edge_ref, 1e-9))

        logger.debug(
            "Edge score: edge_ratio=%.4f ref=%.4f -> %.4f (w=%.2f)",
            edge_ratio, edge_ref, edge_score, w_edge
        )

        # ---- combinazione pesata ----
        raw_score = (
            w_width * width_score
            + w_asym * asym_score
            + w_center * center_score
            + w_hvn * hvn_score
            + w_lvn * lvn_score
            + w_edge * edge_score
        ) / weight_sum

        final = float(max(0.0, min(1.0, raw_score)))

        logger.debug(
            "Equilibrium final score -> %.4f (normalized)", final
        )

        return final



    # ============================================================
    #   PRE BREAKOUT SIGNALS
    # ============================================================

    def _compute_volatility(self, bars):
        closes = [b["close"] for b in bars]
        if len(closes) < 2:
            return 0.0
        return float(np.std(closes))

    import math

    def _compute_volatility_metrics(self, bars: list, window: int = 14):
        if len(bars) < 2:
            return {
                "atr": 0.0,
                "std": 0.0,
                "compression_ratio": 0.0,
                "stability_score": 0.0,
            }

        highs = [b["high"] for b in bars]
        lows = [b["low"] for b in bars]
        closes = [b["close"] for b in bars]

        # --- TRUE RANGE ---
        tr_values = []
        for i in range(1, len(bars)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            tr_values.append(tr)

        atr = sum(tr_values[-window:]) / max(1, min(window, len(tr_values)))

        # --- USA LA TUA STD ESISTENTE ---
        std = self._compute_volatility(bars)

        # --- COMPRESSION ---
        total_range = max(highs) - min(lows)
        compression_ratio = atr / total_range if total_range > 0 else 0.0

        # --- STABILITY SCORE ---
        stability_score = 1 / (1 + compression_ratio)

        return {
            "atr": atr,
            "std": std,
            "compression_ratio": compression_ratio,
            "stability_score": stability_score,
        }


    def _compute_pre_breakout_signals(self, bars, volume_stats, cfg_pb):
        """
        Ritorna un PreBreakoutSignals con:
        - volatility_pickup
        - boundary_volume_drop
        - lvns_near_boundaries
        - directional_bias
        - is_pre_breakout (>= 2 segnali)
        """

        logger.debug("_compute_pre_breakout_signals: start")

        width = max(b["high"] for b in bars) - min(b["low"] for b in bars)
        min_p = min(b["low"] for b in bars)
        max_p = max(b["high"] for b in bars)

        # --------------------------------------------
        # 1) VOLATILITY PICKUP
        # --------------------------------------------
        window = int(cfg_pb["volatility_window"])
        recent_bars = bars[-window:] if len(bars) >= window else bars

        vol_recent = self._compute_volatility(recent_bars)
        vol_total = self._compute_volatility(bars)

        volatility_pickup = (
            vol_total > 0
            and vol_recent > cfg_pb["volatility_increase_factor"] * vol_total
        )

        logger.debug(
            "Volatility: recent=%.4f total=%.4f factor=%.2f -> pickup=%s",
            vol_recent,
            vol_total,
            cfg_pb["volatility_increase_factor"],
            volatility_pickup,
        )

        # --------------------------------------------
        # 2) BOUNDARY VOLUME DROP
        # --------------------------------------------
        boundary_volume = volume_stats.volume_upper_boundary + volume_stats.volume_lower_boundary
        mean_vol = volume_stats.total_volume / max(len(volume_stats.volume_by_price), 1)

        boundary_volume_drop = (
            mean_vol > 0
            and boundary_volume < cfg_pb["boundary_volume_factor"] * mean_vol
        )

        logger.debug(
            "Boundary volume: lower=%.1f upper=%.1f boundary=%.1f mean=%.1f factor=%.2f -> drop=%s",
            volume_stats.volume_lower_boundary,
            volume_stats.volume_upper_boundary,
            boundary_volume,
            mean_vol,
            cfg_pb["boundary_volume_factor"],
            boundary_volume_drop,
        )

        # --------------------------------------------
        # 3) LVN NEAR BOUNDARIES
        # --------------------------------------------
        thr = cfg_pb["lvn_distance_threshold"] * width
        lvns = volume_stats.lvn_levels

        lvns_near_boundaries = any(
            (abs(lvn - min_p) <= thr) or (abs(lvn - max_p) <= thr)
            for lvn in lvns
        )

        logger.debug(
            "LVN check: lvns=%d threshold=%.4f -> near_boundaries=%s",
            len(lvns),
            thr,
            lvns_near_boundaries,
        )

        # --------------------------------------------
        # 4) DIRECTIONAL BIAS
        # --------------------------------------------
        ratio = volume_stats.volume_balance_upper_vs_lower
        thr_db = cfg_pb["directional_bias_threshold"]

        if ratio > thr_db:
            directional_bias = "up"
        elif ratio < 1 / thr_db:
            directional_bias = "down"
        else:
            directional_bias = "neutral"

        logger.debug(
            "Directional bias: ratio=%.4f threshold=%.2f -> %s",
            ratio,
            thr_db,
            directional_bias,
        )

        # --------------------------------------------
        # 5) PRE-BREAKOUT FLAG
        # --------------------------------------------
        signals = [
            volatility_pickup,
            boundary_volume_drop,
            lvns_near_boundaries,
            directional_bias != "neutral",
        ]
        is_pre_breakout = sum(1 for s in signals if s) >= 2

        logger.debug(
            "Pre-breakout result: signals=%s active=%d -> is_pre_breakout=%s",
            signals,
            sum(1 for s in signals if s),
            is_pre_breakout,
        )

        return PreBreakoutSignals(
            is_pre_breakout=is_pre_breakout,
            volatility_pickup=volatility_pickup,
            boundary_volume_drop=boundary_volume_drop,
            lvns_near_boundaries=lvns_near_boundaries,
            directional_bias=directional_bias,
            comment=None,
        )

