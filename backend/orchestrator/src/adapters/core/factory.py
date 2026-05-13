from __future__ import annotations

from typing import Type

from .base_adapter import BaseAdapter
from .breakout_cli_adapter import BreakoutCliAdapter
from .statistical_cli_adapter import StatisticalCliAdapter
from .query_cli_adapter import QueryCliAdapter
from .pattern_cli_adapter import PatternCliAdapter


_ADAPTERS: dict[str, Type[BaseAdapter]] = {
    "breakout_engine_cli": BreakoutCliAdapter,
    "statistical_engine_cli": StatisticalCliAdapter,
    "query_engine_cli": QueryCliAdapter,
    "pattern_engine_cli": PatternCliAdapter,
}


class AdapterFactory:
    @staticmethod
    def create(adapter_id: str) -> BaseAdapter:
        if adapter_id not in _ADAPTERS:
            raise ValueError(f"Unknown adapter_id: {adapter_id}")
        return _ADAPTERS[adapter_id]()
