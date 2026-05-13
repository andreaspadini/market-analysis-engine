from __future__ import annotations

from typing import Any, Dict, List, Optional

from engines.root_engine.processing.balance.mixins.balance_mixin import BalanceMixin
from engines.root_engine.processing.balance.mixins.rotations_mixin import RotationsMixin
from engines.root_engine.processing.balance.schema import BalanceModel, RotationInfo
from engines.root_engine.utils.logger import logger


class BalanceDetector(RotationsMixin, BalanceMixin):
    """
    Orchestratore interno della pipeline:

        bars -> rotations -> balances

    EDI-2B:
    - non cambia l'algoritmica esistente
    - si limita a comporre i mixin già presenti nel package attivo
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        bars: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.raw_config: Dict[str, Any] = config or {}
        self.config: Dict[str, Any] = config or {}
        self.bars: List[Dict[str, Any]] = bars or []

        self.rotations: List[RotationInfo] = []
        self._balances_models: List[BalanceModel] = []
        self._rotation_bar_counts: Dict[int, int] = {}

    def detect_from_bars(
        self,
        bars: Optional[List[Dict[str, Any]]] = None,
    ) -> List[BalanceModel]:
        """
        API principale EDI-2B:
        riceve bars engine-ready e restituisce BalanceModel.
        """
        if bars is not None:
            self.bars = bars

        logger.info("BalanceDetector: avvio pipeline bars -> rotations -> balances")
        logger.info("BalanceDetector: bars ricevute = %d", len(self.bars))

        self.rotations = self._compute_rotations(self.bars)
        logger.info("BalanceDetector: rotations calcolate = %d", len(self.rotations))

        # detect_balances restituisce i BalanceInfo legacy,
        # mentre i BalanceModel completi vengono esposti in self._balances_models
        self.detect_balances(self.rotations)

        logger.info(
            "BalanceDetector: balances models calcolati = %d",
            len(self._balances_models),
        )

        return list(self._balances_models)

    def run(
        self,
        bars: Optional[List[Dict[str, Any]]] = None,
    ) -> List[BalanceModel]:
        """
        Alias comodo per integrazione bootstrap.
        """
        return self.detect_from_bars(bars)

    def get_rotations(self) -> List[RotationInfo]:
        return list(self.rotations)

    def get_balance_models(self) -> List[BalanceModel]:
        return list(self._balances_models)