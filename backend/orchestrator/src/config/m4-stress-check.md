# O2 — M4 Stress Check (freeze note)

Questo documento riassume le verifiche M4 per O2 (Config Schema v1 + Fingerprint).

## Obiettivi M4
- Scalabilità su config con molti `parameters` e `pipeline.steps`.
- Fingerprint deterministico e puro (nessuna mutazione dell'input).
- Verifica che il fingerprint esegua un singolo passaggio di serializzazione canonical.
- Nessun coupling implicito con O3 (no I/O, no filesystem, no storage).

## Risultato
Le verifiche sono codificate come test unitari:
- `tests/unit/test_config_stress.py`

Note sulla complessità:
- Il fingerprint calcola una rappresentazione JSON canonical tramite **una singola** chiamata a `json.dumps(...)`
  con `sort_keys=True` e `separators=(",", ":")`, quindi la parte di serializzazione è lineare rispetto
  alla dimensione dell'output; l'ordinamento delle chiavi (necessario per canonical) introduce il costo di sorting
  per i dict, ma non ci sono passaggi ripetuti o cicli annidati dipendenti dalla dimensione della config.
