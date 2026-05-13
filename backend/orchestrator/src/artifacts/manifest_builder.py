from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Any

from ..adapters.storage.ports import OutputItem, Manifest
from .content_hash import sha256_hex


@dataclass(frozen=True)
class O1Producer:
    tool_id: str
    tool_version: str


def build_o1_manifest_v1(*, producer: O1Producer, outputs: Iterable[OutputItem]) -> Manifest:
    """
    Costruisce un manifest O1 (v1.0) strict-by-default.

    NOTA:
    - Qui usiamo relpath "outputs/<filename>" (come fa core_adapter.py),
      quindi è indipendente dal layout fisico O3.
    - O3 (filesystem_store) può riscrivere outputs per riflettere i path reali materializzati.
    """
    out_list: List[Dict[str, Any]] = []
    for it in outputs:
        relpath = f"outputs/{it.filename}"
        out_list.append(
            {
                "relpath": relpath,
                "bytes": len(it.data),
                "checksum": {"alg": "sha256", "value": sha256_hex(it.data)},
            }
        )

    m: Dict[str, Any] = {
        "manifest_version": "1.0",
        "producer": {"tool_id": producer.tool_id, "tool_version": producer.tool_version},
        "outputs": out_list,
    }
    return m
