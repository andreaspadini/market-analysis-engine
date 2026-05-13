from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True, slots=True)
class CoreInvocation:
    """
    Data-only: rappresenta una singola invocazione al Core.

    Vincoli:
    - Nessuna semantica runtime.
    - Nessuna logica quantitativa.
    - JSON-serializzabile (valori in `inputs` e `parameters` devono esserlo).
    """
    tool_id: str
    inputs: Mapping[str, Any]
    parameters: Mapping[str, Any]
    resources: Optional[Mapping[str, Any]] = None
    metadata: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True, slots=True)
class CoreResult:
    """
    Data-only: risultato della computazione Core.

    `payload` è un oggetto JSON-serializzabile che O4B passerà a O3
    per materializzare un artifact (senza scrivere su filesystem).
    """
    payload: Any
    metrics: Optional[Mapping[str, Any]] = None


class CorePort(ABC):
    """
    Anti-corruption layer: contratto minimo verso Core.
    Orchestrator dipende da Core solo tramite questa porta.

    Vincoli:
    - Nessun import da packages/core/*
    - Nessun riferimento a Orchestrator dentro Core (Core è ignaro).
    """

    @abstractmethod
    def invoke(self, invocation: CoreInvocation) -> CoreResult:
        """
        Esegue una singola invocazione al Core (sincrona, sequenziale).
        """
        raise NotImplementedError
