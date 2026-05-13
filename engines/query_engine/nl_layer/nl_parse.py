# nl_layer/nl_parse.py
import re
import json
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Mapping, cast


try:
    import yaml
except ImportError:
    raise RuntimeError("Missing dependency: pyyaml. Install with: pip install pyyaml")


ONTOLOGY_PATH = Path("nl_layer/grammar/ontology.yaml")
RULES_PATH = Path("nl_layer/grammar/rules.yaml")
INVENTORY_PATH = Path("nl_layer/tools/intent_inventory.json")


# ----------------------------
# Loading helpers
# ----------------------------
def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_inventory() -> Dict[str, dict]:
    items = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    return {it["intent_id"]: it for it in items}


# ----------------------------
# Normalization
# ----------------------------
def _normalize_text(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t

# ----------------------------
# Enum extraction
# ----------------------------
def _build_enum_index(enums: dict) -> Dict[str, Dict[str, str]]:
    """
    { slot_name: { synonym -> canonical } }
    """
    idx: Dict[str, Dict[str, str]] = {}
    for slot_name, mapping in enums.items():
        slot_idx: Dict[str, str] = {}
        for canonical, synonyms in mapping.items():
            # canonical itself
            slot_idx[canonical.lower()] = canonical
            for s in synonyms:
                slot_idx[str(s).lower()] = canonical
        idx[slot_name] = slot_idx
    return idx


def _extract_enum_slots(text: str, enum_index: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    found: Dict[str, Any] = {}

    for slot, synmap in enum_index.items():
        hits: List[str] = []
        for syn, canonical in synmap.items():
            if not syn:
                continue
            # match parola intera / token boundary
            if re.search(rf"(?<!\w){re.escape(syn)}(?!\w)", text):
                hits.append(canonical)

        if hits:
            uniq = sorted(set(hits))
            if len(uniq) == 1:
                found[slot] = uniq[0]
            else:
                found[slot] = {"_ambiguous": uniq}

    return found

def _internal_error(
    message: str,
    *,
    rule_id: Optional[str] = None,
    slots: Optional[Dict[str, Any]] = None,
    intent_id: Optional[str] = None,
    debug: Optional[Dict[str, Any]] = None,
):
    payload = {
        "ok": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": message,
        },
    }

    dbg = {}
    if rule_id is not None:
        dbg["rule_id"] = rule_id
    if slots is not None:
        dbg["slots"] = slots
    if intent_id is not None:
        dbg["intent_id"] = intent_id
    if debug is not None:
        dbg.update(debug)

    if dbg:
        payload["error"]["debug"] = dbg

    return payload


# ----------------------------
# Regex extraction
# ----------------------------

def _rule_patterns_regex(rule: Dict[str, Any]) -> List[str]:
    return [str(x) for x in (rule.get("patterns_regex") or []) if str(x).strip()]

def _rule_forbidden_terms(rule: Dict[str, Any]) -> List[str]:
    return [str(x).strip().lower() for x in (rule.get("forbidden_terms") or []) if str(x).strip()]

def _extract_minutes(text: str, pattern: str) -> Optional[int]:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    gd = m.groupdict()
    if "minutes" in gd and gd["minutes"] is not None:
        return int(gd["minutes"])
    # fallback: first number
    m2 = re.search(r"\d{1,3}", m.group(0))
    return int(m2.group(0)) if m2 else None


def _extract_wbucket(text: str, pattern: str) -> Optional[str]:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return m.group(1).lower() if m else None


def _extract_qbuckets_all(text: str) -> List[str]:
    # returns ['q4_high','q3_midhigh', ...] in appearance order
    m = re.findall(r"\b(q[1-4]_(?:low|midlow|midhigh|high))\b", text, flags=re.IGNORECASE)
    return [x.lower() for x in m]


def _required_slots_from_rule(rule: dict) -> List[str]:
    req = []
    for k, spec in (rule.get("slots") or {}).items():
        if isinstance(spec, dict) and spec.get("required"):
            req.append(k)
    return req

def _rule_patterns(rule: Dict[str, Any]) -> List[str]:
    """Ritorna pattern string validi da una rule."""
    pats = rule.get("patterns") or []
    return [p for p in pats if isinstance(p, str) and p.strip()]

def _build_dynamic_suggestions(
    rules: List[Dict[str, Any]],
    *,
    limit: int = 6,
    only_rule_ids: Optional[List[str]] = None,
) -> List[str]:
    """
    Genera suggestions automaticamente dai patterns delle rules.
    - Ordina per priority DESC
    - Preferisce pattern “umani” (con minuti / parole chiave / mode)
    - Evita pattern troppo generici (es. "success")
    - Se only_rule_ids è dato, filtra a quelle regole (utile per AMBIGUOUS_QUERY)
    """
    if only_rule_ids:
        wanted = set(only_rule_ids)
        rules = [r for r in rules if (r.get("id") in wanted)]

    rules_sorted = sorted(
        rules,
        key=lambda r: int(r.get("priority", 0) or 0),
        reverse=True,
    )

    # Pattern da scartare se troppo generici
    GENERIC_EXACT = {
        "success", "retest", "lv01", "lv04", "win03",
        "acceptance", "timing",
    }

    # Preferenze: più alto = scelto prima
    def score_pattern(p: str) -> int:
        s = p.strip().lower()
        score = 0

        # base: più lungo = spesso più “esempio reale”
        score += min(len(s), 80) // 10  # 0..8

        # contiene minuti (10m / 60m / "minuti") -> utile
        if "m" in s and any(ch.isdigit() for ch in s):
            score += 6
        if " min" in s or " minuti" in s:
            score += 6

        # parole chiave “umane”
        if "accettazione" in s or "acceptance" in s:
            score += 8
        if "primo close" in s or "first close" in s:
            score += 8
        if "tempo" in s or "time" in s or "timing" in s:
            score += 5
        if "retest" in s:
            score += 7
        if "win03" in s:
            score += 7
        if "mode" in s:
            score += 4
        if "session" in s or "usa" in s or "europe" in s or "asia" in s:
            score += 3

        # penalità se troppo “comando secco”
        if s in GENERIC_EXACT:
            score -= 100

        # penalità se troppo corto
        if len(s) < 8:
            score -= 50

        return score

    def is_good(p: str) -> bool:
        s = p.strip()
        if not s:
            return False
        sl = s.lower()
        if sl in GENERIC_EXACT:
            return False
        if len(sl) < 8:
            return False
        return True

    out: List[str] = []
    seen = set()

    # 1) Prima passata: per ogni rule scegli il MIGLIOR pattern (non il primo)
    candidates: List[str] = []
    for r in rules_sorted:
        pats = _rule_patterns(r)
        if not pats:
            continue

        cleaned = [p.strip() for p in pats if p and p.strip()]
        if not cleaned:
            continue

        # scegli il best pattern per questa rule
        best = max(cleaned, key=score_pattern)
        candidates.append(best)

    # 2) Aggiungi i candidati migliori (ordinati per score globale)
    candidates_sorted = sorted(candidates, key=score_pattern, reverse=True)
    for ex in candidates_sorted:
        ex = ex.strip()
        if not is_good(ex):
            continue
        if ex not in seen:
            seen.add(ex)
            out.append(ex)
        if len(out) >= limit:
            return out

    # 3) Fallback: se non basta, pesca altri pattern dalle rules (sempre filtrando)
    for r in rules_sorted:
        pats = _rule_patterns(r)
        for p in sorted([x.strip() for x in pats if x and x.strip()], key=score_pattern, reverse=True):
            if not is_good(p):
                continue
            if p not in seen:
                seen.add(p)
                out.append(p)
            if len(out) >= limit:
                return out

    return out

def _rule_patterns_regex(rule: dict) -> List[str]:
    """
    Ritorna una lista di regex per la rule.
    Supporta sia formato corretto:
      patterns_regex: ["...","..."]
    sia formato "sporco" (capitato in YAML):
      patterns_regex: { "patterns_regex": ["..."] }
    """
    pr = rule.get("patterns_regex")

    if pr is None:
        return []

    # formato corretto
    if isinstance(pr, list):
        return [str(x) for x in pr if str(x).strip()]

    # formato sporco: {"patterns_regex":[...]}
    if isinstance(pr, dict):
        pr2 = pr.get("patterns_regex")
        if isinstance(pr2, list):
            return [str(x) for x in pr2 if str(x).strip()]
        return []

    # fallback: string singola
    if isinstance(pr, str) and pr.strip():
        return [pr.strip()]

    return []


_SLOT_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

def _expand_pattern(p: str, slots: dict) -> str:
    """
    Trasforma 'successo alle {hour}' in 'successo alle 15' usando slots.
    Se manca uno slot richiesto dal pattern, ritorna stringa vuota.
    """
    if not p:
        return ""
    out = p
    for name in _SLOT_RE.findall(p):
        v = slots.get(name)
        # se lo slot è ambiguo o mancante -> non posso espandere
        if v is None or (isinstance(v, dict) and v.get("_ambiguous")):
            return ""
        out = out.replace("{" + name + "}", str(v))
    return out


def _match_rule(text: str, rules: List[dict], slots: Dict[str, Any]) -> Tuple[Optional[dict], int, List[str]]:
    """
    returns (best_rule, best_hits, tied_rule_ids)

    Ranking:
    1) meno required slots mancanti
    2) priority più alta
    3) più hits sulle patterns
    """
    t = (text or "").lower()

    best: Optional[dict] = None
    best_missing = 10**9
    best_priority = -10**9
    best_hits = -1
    ties: List[dict] = []

    for r in rules:
        # ---- 0) prepara patterns "normali" ----
        pats = r.get("patterns")
        if pats is None:
            pats = r.get("triggers_any", [])
        pats = [str(p).lower().strip() for p in pats if str(p).strip()]

        matched = False
        regex_groups: Dict[str, Any] = {}  # SEMPRE definita, anche se vuota

        # 1) normal patterns (+ expand se contiene {slot})
        expanded: List[str] = []
        for p in pats:
            p2 = _expand_pattern(p, slots) if ("{" in p and "}" in p) else p
            p2 = (p2 or "").lower().strip()
            if p2:
                expanded.append(p2)

        hits = sum(1 for p in expanded if p and p in t)
        if hits > 0:
            matched = True

        # 2) forbidden terms (se matcha una forbidden → scarta la rule)
        forbidden_hit = False
        for term in _rule_forbidden_terms(r):
            term = (term or "").lower().strip()
            if term and term in t:
                forbidden_hit = True
                break
        if forbidden_hit:
            continue

        # 3) regex patterns:
        # - fallback se non matched
        # - OR "always-on" se la rule dichiara params_from_regex (serve per compare a/b)
        needs_regex_groups = False
        maps_to = r.get("maps_to") or {}
        pfr = r.get("params_from_regex") or maps_to.get("params_from_regex")
        if isinstance(pfr, dict) and pfr:
            needs_regex_groups = True

        if (not matched) or needs_regex_groups:
            regex_pats = _rule_patterns_regex(r)
            for rp in regex_pats:
                m = re.search(rp, t)
                if m:
                    # se non era matched, ora lo diventa e conta come hit
                    if not matched:
                        matched = True
                        hits += 1
                    regex_groups = m.groupdict() or {}
                    break


        if not matched:
            continue

        # ---- scoring ----
        pr = int(r.get("priority", 0))
        req = _required_slots_from_rule(r)
        missing = sum(1 for k in req if k not in slots)

        better = False
        if missing < best_missing:
            better = True
        elif missing == best_missing:
            if pr > best_priority:
                better = True
            elif pr == best_priority and hits > best_hits:
                better = True

        # IMPORTANT: se abbiamo regex_groups, NON mutiamo r: facciamo copy e attacchiamo gruppi
        candidate = r
        if regex_groups:
            candidate = dict(r)
            candidate["_regex_groups"] = regex_groups

        if better:
            best = candidate
            best_missing = missing
            best_priority = pr
            best_hits = hits
            ties = [candidate]
        else:
            if missing == best_missing and pr == best_priority and hits == best_hits:
                ties.append(candidate)

    # ---- output ----
    if best is None:
        return None, -1, []

    if len(ties) > 1:
        return None, best_hits, [x.get("id") for x in ties]

    return best, best_hits, []



# ----------------------------
# Validation / suggestions
# ----------------------------
def _suggest_for_missing(missing: List[str]) -> List[str]:
    s: List[str] = []
    if "wbucket" in missing:
        s.append("Aggiungi una window tipo: w0900_1300")
    if "volbucket" in missing:
        s.append("Aggiungi un bucket volume tipo: q4_high")
    if "deltabucket" in missing:
        s.append("Aggiungi un bucket delta tipo: q3_midhigh")
    if "level" in missing:
        s.append("Specifica il livello: VAH/VAL/POC/VWAP")
    if "side" in missing:
        s.append("Specifica il lato: sopra/sotto (above/below)")
    if "minutes" in missing:
        s.append("Specifica i minuti: es '10m' o '60 minuti'")
    if "mode" in missing:
        s.append("Specifica mode: nearest oppure at_least")
    if "session" in missing:
        s.append("Specifica sessione: asia/europe/usa")
    return s


def _error(code: str, message: str, **extra) -> Dict[str, Any]:
    err = {"ok": False, "error": {"code": code, "message": message}}
    if extra:
        err["error"].update(extra)
    return err

def _safe_rule_id(rule: Any) -> Optional[str]:
    if isinstance(rule, dict):
        rid = rule.get("id")
        return rid if isinstance(rid, str) else None
    return None



# ----------------------------
# Main parse function
# ----------------------------
def parse_query(text: str) -> Dict[str, Any]:
    onto = _load_yaml(ONTOLOGY_PATH)
    _ = _load_yaml(RULES_PATH)  # rules_doc non serve qui, lo ricarichi dopo
    inventory = _load_inventory()


    t = _normalize_text(text)

    # Heuristic compare: compare/confronta + connettore (vs/and/e/tra/versus)
    looks_like_compare = bool(
        re.search(r"(?i)\b(confronta|compare)\b", t)
        and re.search(r"(?i)\b(vs|versus|and|e|tra)\b", t)
    )

    # 1) extract slots
    enum_index = _build_enum_index(onto.get("enums", {}))
    slots: Dict[str, Any] = {}
    slots.update(_extract_enum_slots(t, enum_index))
    slots = _resolve_calendar_number_ambiguity(text, slots)

    # reject ambiguous enum slots early (except compare)
    for k, v in slots.items():
        if isinstance(v, dict) and v.get("_ambiguous"):
            if looks_like_compare:
                continue
            return _error(
                "AMBIGUOUS_QUERY",
                f"Ambiguità sullo slot '{k}': {v['_ambiguous']}",
                slot=k,
                candidates=v["_ambiguous"],
                debug={"slots": slots},
            )

    regex_map = onto.get("regex", {})

    minutes = _extract_minutes(
        t,
        regex_map.get("minutes", r"(?P<minutes>\d{1,3})\s*(m|min|minutes|minuti)\b"),
    )
    if minutes is not None:
        slots["minutes"] = minutes

    wbucket = _extract_wbucket(t, regex_map.get("wbucket", r"\b(w\d{4}_\d{4})\b"))
    if wbucket is not None:
        slots["wbucket"] = wbucket

    qb_all = _extract_qbuckets_all(t)
    if qb_all:
        slots["qbucket_all"] = qb_all

    # 2) route
    rules_doc = yaml.safe_load(open(RULES_PATH, encoding="utf-8"))
    if isinstance(rules_doc, list):
        rules = rules_doc
    elif isinstance(rules_doc, dict):
        rules = rules_doc.get("rules", []) or []
    else:
        rules = []

    slots_for_routing = slots
    if looks_like_compare:
        slots_for_routing = {
            k: v for k, v in slots.items()
            if not (isinstance(v, dict) and v.get("_ambiguous"))
        }

    rule, _score, tied = _match_rule(t, rules, slots_for_routing)

    # porta i regex groups nei slots (per compat params_from_slots ecc.)
    if rule and isinstance(rule, dict):
        rg = rule.get("_regex_groups") or {}
        if isinstance(rg, dict) and rg:
            for k, v in rg.items():
                if v is not None and str(v).strip() != "":
                    slots[k] = str(v).strip()

    # tie-break
    if tied and len(tied) > 1:
        id2rule = {r.get("id"): r for r in rules}
        candidates = [id2rule.get(rid) for rid in tied if id2rule.get(rid)]

        def missing_required_count(r: dict) -> int:
            slots_def = r.get("slots", {}) or {}
            req = [k for k, v in slots_def.items() if isinstance(v, dict) and v.get("required")]
            return sum(1 for k in req if k not in slots)

        if candidates:
            if "session" in slots:
                specific = next(
                    (r for r in candidates if r.get("id") == "rule_success_by_weekday_session"),
                    None,
                )
                if specific is not None:
                    rule = specific
                    tied = []

            scored = [(missing_required_count(r), r) for r in candidates]
            scored.sort(key=lambda x: x[0])
            best_missing = scored[0][0]
            best_rules = [r for m, r in scored if m == best_missing]

            if len(best_rules) == 1:
                rule = best_rules[0]
            else:
                tied_ids = sorted({r.get("id") for r in best_rules if r.get("id")})
                dyn = _build_dynamic_suggestions(rules, limit=6, only_rule_ids=tied_ids)
                return {
                    "ok": False,
                    "error": {
                        "code": "AMBIGUOUS_QUERY",
                        "message": f"Query matcha più regole: {tied_ids}. Specifica meglio.",
                        "ambiguous_rules": tied_ids,
                    },
                    "suggestions": dyn,
                    "debug": {"slots": slots},
                }

    if not rule:
        dyn_suggestions = _build_dynamic_suggestions(rules, limit=6)
        return {
            "ok": False,
            "error": {
                "code": "OUT_OF_SCOPE",
                "message": "Query non mappabile a intent supportati. Prova con uno degli esempi qui sotto.",
            },
            "suggestions": dyn_suggestions,
            "debug": {"slots": slots},
        }

    # intent id
    rid = _safe_rule_id(rule)
    intent_id = rule.get("intent_id") or (rule.get("maps_to") or {}).get("intent_id")
    if not intent_id:
        return _error(
            "INTERNAL_ERROR",
            f"Rule '{rid}' non contiene intent_id",
            debug={"slots": slots, "rule_id": rid, "rule": rule},
        )

    if intent_id not in inventory:
        return _error(
            "INTERNAL_ERROR",
            f"Intent '{intent_id}' non trovato in nl_layer/tools/intent_inventory.json",
            debug={"slots": slots, "rule_id": rid},
        )

    # special-case: weekday_volatility_and_breakout_success
    if intent_id == "weekday_volatility_and_breakout_success":
        wd_raw = slots.get("weekday") if isinstance(slots, dict) else None
        if wd_raw is None or str(wd_raw).strip() == "":
            wd = "ALL"
        else:
            wd_norm = _weekday_any_to_engine(str(wd_raw))
            wd = wd_norm if wd_norm else str(wd_raw).strip()

        return {
            "ok": True,
            "type": "intent",
            "intent_id": intent_id,
            "params": {"weekday": wd},
            "explain": {"rule_id": rule.get("id") if isinstance(rule, dict) else None, "slots": slots},
        }

    # 3) validate required slots (rule-level)
    required: List[str] = []
    rule_slots_def = rule.get("slots", {}) or {}
    for k, v in rule_slots_def.items():
        if isinstance(v, dict) and v.get("required"):
            required.append(k)

    missing: List[str] = []
    for s in required:
        if s in ("wbucket", "volbucket", "deltabucket"):
            if "qbucket_all" not in slots or len(slots["qbucket_all"]) < 3:
                missing.append(s)
        elif s not in slots:
            missing.append(s)

    if intent_id == "win03_success_by_bucket_and_init_vol_delta_report":
        if "qbucket_all" not in slots or len(slots["qbucket_all"]) < 3:
            if "volbucket" not in missing:
                missing.append("volbucket")
            if "deltabucket" not in missing:
                missing.append("deltabucket")

    if missing:
        return {
            "ok": False,
            "error": {
                "code": "MISSING_SLOT",
                "message": f"Mancano slot obbligatori per {intent_id}: {missing}",
                "missing": missing,
            },
            "suggestions": _suggest_for_missing(missing),
            "debug": {"slots": slots, "rule_id": rid, "intent_id": intent_id},
        }

    # UX guard-rail: acceptance su level senza side
    if intent_id == "prev_day_level_acceptance_h60":
        lvl = slots.get("level")
        side = slots.get("side")
        minutes_ = slots.get("minutes")

        if lvl and minutes_ is not None and not side:
            return {
                "ok": False,
                "error": {
                    "code": "MISSING_SLOT",
                    "message": "Specifica il lato per l’acceptance: sopra o sotto (above/below).",
                    "missing": ["side"],
                },
                "suggestions": [
                    f"accettazione {lvl} sopra {minutes_}m",
                    f"accettazione {lvl} sotto {minutes_}m",
                    f"acceptance {lvl} above {minutes_}m",
                    f"acceptance {lvl} below {minutes_}m",
                ],
                "debug": {"slots": slots, "rule_id": rid, "intent_id": intent_id},
            }

        # 4) build params (intent-specific, deterministic)

    # rid lo hai già sopra: rid = _safe_rule_id(rule)

    # --- FIX: overview hour -> hour=ALL PRIMA di _build_params_from_slots ---
    maps_to = rule.get("maps_to") or {}
    explicit_params = maps_to.get("params") or {}

    # Caso A: riconosco per rule_id (più robusto)
    if rid in ("cal_rule_success_by_hour_overview", "cal_rule_volatility_by_hour_overview"):
        slots = dict(slots or {})
        slots["hour"] = "ALL"

    # Caso B (opzionale): se vuoi che funzioni per altre rule future che mettono params.hour="ALL"
    elif intent_id in ("success_by_hour", "volatility_by_hour"):
        if isinstance(explicit_params, dict) and explicit_params.get("hour") == "ALL":
            slots = dict(slots or {})
            slots["hour"] = "ALL"
    # --- END FIX ---

    regex_groups = rule.get("_regex_groups") or {}

    try:
        params = _build_params_from_slots(rule, slots, regex_groups=regex_groups)

        if regex_groups:
            params.update(_build_params_from_regex(rule, regex_groups))

        if intent_id in ("compare_success_by_weekday", "compare_volatility_by_weekday"):
            if "a" in params and params["a"] is not None:
                params["a"] = _weekday_any_to_engine(str(params["a"])) or str(params["a"])
                params["a"] = _weekday_any_to_calendar(str(params["a"])) or params["a"]
            if "b" in params and params["b"] is not None:
                params["b"] = _weekday_any_to_engine(str(params["b"])) or str(params["b"])
                params["b"] = _weekday_any_to_calendar(str(params["b"])) or params["b"]

        if regex_groups:
            for kk in ("weekday", "weekday_calendar", "month", "day_of_month", "week_of_month", "hour"):
                params.pop(kk, None)

        _TITLE_RE = re.compile(r"(?:\btitle\b|\btitolo\b)\s*:\s*(.+)$", re.IGNORECASE)

        def _extract_explicit_title(raw: str) -> str | None:
            if not raw:
                return None
            m = _TITLE_RE.search(raw)
            if not m:
                return None
            tt = m.group(1).strip()
            return tt if tt else None

        explicit_title = _extract_explicit_title(text)
        if explicit_title:
            params["title"] = explicit_title

        if intent_id.startswith("compare_") and not params.get("title"):
            a = params.get("a")
            b = params.get("b")
            if intent_id == "compare_success_by_day_of_month":
                params["title"] = f"Confronto successo giorno {a} vs {b}"
            elif intent_id == "compare_success_by_week_of_month":
                params["title"] = f"Confronto successo settimana {a} vs {b}"
            elif intent_id == "compare_success_by_month":
                params["title"] = f"Confronto successo mese {a} vs {b}"
            elif intent_id == "compare_success_by_hour":
                params["title"] = f"Confronto successo ora {a} vs {b}"
            elif intent_id == "compare_success_by_weekday":
                params["title"] = f"Confronto successo {a} vs {b}"
            elif intent_id == "compare_volatility_by_day_of_month":
                params["title"] = f"Confronto volatilità giorno {a} vs {b}"
            elif intent_id == "compare_volatility_by_hour":
                params["title"] = f"Confronto volatilità ora {a} vs {b}"
            elif intent_id == "compare_volatility_by_weekday":
                params["title"] = f"Confronto volatilità {a} vs {b}"
            elif intent_id == "compare_volatility_by_month":
                params["title"] = f"Confronto volatilità mese {a} vs {b}"
            else:
                params["title"] = f"Confronto {a} vs {b}"

    except ValueError as e:
        return _error(
            "INVALID_QUERY",
            str(e),
            debug={"slots": slots, "rule_id": rid, "intent_id": intent_id},
        )

    explain = {"rule_id": rid, "slots": slots}
    if rule.get("_regex_groups"):
        explain["regex_groups"] = rule["_regex_groups"]

    return {
        "ok": True,
        "type": "intent",
        "intent_id": intent_id,
        "params": params,
        "explain": explain,
    }




# ----------------------------
# Canon helpers
# ----------------------------
import re
from typing import Any, Dict

def _weekday_any_to_calendar(s: str) -> str:
    """
    Converte input umano/engine in nome weekday in inglese 'Monday'..'Sunday'.
    Supporta: lunedì/lun, mon/monday, mar/martedì, tue/tuesday, ecc.
    """
    if s is None:
        return ""

    x = str(s).strip().lower()

    # normalizza accenti e apostrofi comuni
    x = (
        x.replace("ì", "i")
         .replace("’", "'")
         .replace("`", "'")
    )

    # ITA -> ENG full
    if x.startswith("lun"):
        return "Monday"
    if x.startswith("mar"):
        return "Tuesday"
    if x.startswith("mer"):
        return "Wednesday"
    if x.startswith("gio"):
        return "Thursday"
    if x.startswith("ven"):
        return "Friday"
    if x.startswith("sab"):
        return "Saturday"
    if x.startswith("dom"):
        return "Sunday"

    # ENG short/full -> ENG full
    if x in ("mon", "monday"):
        return "Monday"
    if x in ("tue", "tues", "tuesday"):
        return "Tuesday"
    if x in ("wed", "wednesday"):
        return "Wednesday"
    if x in ("thu", "thurs", "thursday"):
        return "Thursday"
    if x in ("fri", "friday"):
        return "Friday"
    if x in ("sat", "saturday"):
        return "Saturday"
    if x in ("sun", "sunday"):
        return "Sunday"

    # fallback: se arriva già "Monday" con case strano, prova title()
    if x in ("monday","tuesday","wednesday","thursday","friday","saturday","sunday"):
        return x.title()

    return str(s).strip()


def _resolve_calendar_number_ambiguity(text: str, slots: Dict[str, Any]) -> Dict[str, Any]:
    """
    Risolve casi tipo: "successo il 20 alle 15"
    Quando day_of_month e hour risultano entrambi ambigui sugli stessi numeri.
    Heuristica:
    - "il <n>" => day_of_month
    - "alle/ore/at <n>" => hour
    """
    if not isinstance(slots, dict):
        return slots

    # solo se entrambi sono ambigui
    dom = slots.get("day_of_month")
    hr = slots.get("hour")

    if not (isinstance(dom, dict) and dom.get("_ambiguous")):
        return slots
    if not (isinstance(hr, dict) and hr.get("_ambiguous")):
        return slots

    t = (text or "").lower()

    m_dom = re.search(r"(?i)\b(il|giorno)\s*(\d{1,2})\b", t)
    m_hr  = re.search(r"(?i)\b(alle|ore|at)\s*(\d{1,2})\b", t)

    # se troviamo entrambi, risolviamo deterministico
    if m_dom and m_hr:
        d = m_dom.group(2)
        h = m_hr.group(2)
        slots["day_of_month"] = d
        slots["hour"] = h
        return slots

    # fallback: se trovi solo "alle/ore/at <n>", forzalo su hour e lascia day_of_month ambigua
    if m_hr:
        slots["hour"] = m_hr.group(2)
        return slots

    # fallback: se trovi solo "il <n>", forzalo su day_of_month e lascia hour ambigua
    if m_dom:
        slots["day_of_month"] = m_dom.group(2)
        return slots

    return slots

def _strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def _weekday_any_to_engine(s: str) -> Optional[str]:
    """
    Converte input libero (IT/EN, abbreviazioni) -> Monday/Tuesday/... oppure None se non riconosciuto.
    """
    if s is None:
        return None
    raw = _strip_accents(str(s).strip().lower())
    raw = re.sub(r"[^a-z]", "", raw)  # tieni solo lettere

    if not raw:
        return None

    mapping = {
        # EN
        "monday": "Monday", "mon": "Monday",
        "tuesday": "Tuesday", "tue": "Tuesday", "tues": "Tuesday",
        "wednesday": "Wednesday", "wed": "Wednesday",
        "thursday": "Thursday", "thu": "Thursday", "thur": "Thursday", "thurs": "Thursday",
        "friday": "Friday", "fri": "Friday",
        "saturday": "Saturday", "sat": "Saturday",
        "sunday": "Sunday", "sun": "Sunday",

        # IT
        "lunedi": "Monday", "lun": "Monday",
        "martedi": "Tuesday", "mar": "Tuesday",
        "mercoledi": "Wednesday", "mer": "Wednesday",
        "giovedi": "Thursday", "gio": "Thursday",
        "venerdi": "Friday", "ven": "Friday",
        "sabato": "Saturday", "sab": "Saturday",
        "domenica": "Sunday", "dom": "Sunday",
    }

    return mapping.get(raw)

def _canon_qbucket(b: str) -> str:
    b = str(b).strip()
    if b.lower().startswith("q") and len(b) >= 2 and b[1].isdigit():
        return "Q" + b[1:]
    return b

def _weekday_to_engine(s: str) -> Optional[str]:
    if not s:
        return None
    x = str(s).strip().lower()

    # normalizza accenti
    x = _strip_accents(x)

    m = {
        # canonical ontology -> engine
        "mon": "Monday",
        "tue": "Tuesday",
        "wed": "Wednesday",
        "thu": "Thursday",
        "fri": "Friday",
        "sat": "Saturday",
        "sun": "Sunday",

        # english names / abbr
        "monday": "Monday",
        "tuesday": "Tuesday",
        "wednesday": "Wednesday",
        "thursday": "Thursday",
        "friday": "Friday",
        "saturday": "Saturday",
        "sunday": "Sunday",
        "mo": "Monday", "tu": "Tuesday", "we": "Wednesday", "th": "Thursday",
        "fr": "Friday", "sa": "Saturday", "su": "Sunday",

        # italian
        "lun": "Monday", "lunedi": "Monday",
        "mar": "Tuesday", "martedi": "Tuesday",
        "mer": "Wednesday", "mercoledi": "Wednesday",
        "gio": "Thursday", "giovedi": "Thursday",
        "ven": "Friday", "venerdi": "Friday",
        "sab": "Saturday", "sabato": "Saturday",
        "dom": "Sunday", "domenica": "Sunday",
    }

    # già in formato engine?
    if x.capitalize() in ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"):
        return x.capitalize()

    return m.get(x)


def _required_slots_from_rule(rule: dict) -> list[str]:
    # supporta sia required_slots esplicito, sia slots: {.. required:true ..}
    req = rule.get("required_slots")
    if isinstance(req, list) and req:
        return req

    out: list[str] = []
    slots_spec = rule.get("slots") or {}
    if isinstance(slots_spec, dict):
        for k, spec in slots_spec.items():
            if isinstance(spec, dict) and spec.get("required"):
                out.append(k)
    return out


# ----------------------------
# Intent-specific params builder (stable)
# ----------------------------

def _build_params(intent_id: str, slots: Dict[str, Any]) -> Dict[str, Any]:
    # --- Calendar ranking (best/worst) ---
    if intent_id == "success_by_month_best":
        return {"rank": "best", "title": "Mese con più successo"}
    if intent_id == "success_by_month_worst":
        return {"rank": "worst", "title": "Mese con meno successo"}

    if intent_id == "volatility_by_hour_best":
        return {"rank": "best", "title": "Ora più volatile"}
    if intent_id == "volatility_by_hour_worst":
        return {"rank": "worst", "title": "Ora meno volatile"}

    if intent_id == "volatility_by_day_of_month_best":
        return {"rank": "best", "title": "Giorno del mese più volatile"}
    if intent_id == "volatility_by_day_of_month_worst":
        return {"rank": "worst", "title": "Giorno del mese meno volatile"}

    # WIN03: combo di 3 bucket in ordine -> (wbucket, volbucket, deltabucket)
    if intent_id == "win03_success_by_bucket_and_init_vol_delta_report":
        qb = slots.get("qbucket_all", [])
        if not (isinstance(qb, list) and len(qb) >= 3):
            raise ValueError(
                "WIN03 richiede 3 bucket Q in ordine: wbucket volbucket deltabucket "
                "(es: q4_high q3_midhigh q3_midhigh)."
            )
        return {
            "wbucket": _canon_qbucket(qb[0]),
            "volbucket": _canon_qbucket(qb[1]),
            "deltabucket": _canon_qbucket(qb[2]),
        }

    # LV04 time confirm
    if intent_id == "level_time_confirm_h60":
        return {
            "level": slots["level"],
            "side": slots["side"],
            "minutes": slots["minutes"],
            "mode": slots.get("mode", "nearest"),
        }

    # Retest probability
    if intent_id == "retest_probability_by_session_minutes":
        return {
            "session": slots["session"],
            "minutes": slots["minutes"],
        }

    # Success by weekday (RAW)
    if intent_id == "success_by_weekday_raw":
        slots_d = slots if isinstance(slots, dict) else {}
        wd_raw = slots_d.get("weekday")
        if not wd_raw:
            raise ValueError("Missing weekday")
        wd = _weekday_to_engine(str(wd_raw))
        if not wd:
            raise ValueError(f"Invalid weekday: {wd_raw}")
        return {"weekday": wd}

    # Success by weekday + session
    if intent_id == "success_by_weekday_session":
        return {
            "weekday": _weekday_to_engine(slots["weekday"]),
            "session": slots["session"],
        }

    # MP06 / MP07
    if intent_id in ("mp06_success_accept5m_high_vol_report", "mp07_success_accept5m_by_delta_sign_report"):
        return {"session": slots["session"]}

    # Calendar: successo by day_of_month + hour (combo)
    if intent_id == "success_by_day_of_month_and_hour":
        return {
            "day_of_month": str(slots["day_of_month"]),
            "hour": str(slots["hour"]),
        }

    # --- FIX: supporta hour=ALL per gli overview by_hour ---
    if intent_id in ("volatility_by_hour", "success_by_hour"):
        h = slots.get("hour")
        if h is None:
            raise ValueError("Missing hour")

        hs = str(h).strip()
        if hs.upper() == "ALL":
            return {"hour": "ALL"}

        try:
            hi = int(hs)
        except Exception:
            raise ValueError(f"Invalid hour: {h}")

        if not (0 <= hi <= 23):
            raise ValueError("Hour fuori range (0-23).")

        return {"hour": str(hi)}

        # Calendar: day_of_month (single/overview)
    if intent_id in ("success_by_day_of_month", "volatility_by_day_of_month"):
        d = slots.get("day_of_month")

        # overview mode: day_of_month=ALL
        if d is None:
            raise ValueError("Missing day_of_month")

        if isinstance(d, str) and d.upper() == "ALL":
            return {"day_of_month": "ALL"}

        try:
            di = int(d)
        except Exception:
            raise ValueError(f"Invalid day_of_month: {d}")

        if not (1 <= di <= 31):
            raise ValueError(f"INVALID_RANGE: day_of_month={di}")

        return {"day_of_month": str(di)}



    # default: prova a passare pari-pari tutto ciò che sembra “atomico”
    # (evita liste grosse come qbucket_all)
    out: Dict[str, Any] = {}
    for k, v in slots.items():
        if k == "qbucket_all":
            continue
        out[k] = v
    return out


# ----------------------------
# Rule -> params binding
# ----------------------------


from typing import Any, Dict

def _build_params_from_slots(rule: dict, slots: dict, regex_groups: dict | None = None) -> dict:
    rg = regex_groups or {}

    # 0) merge slots + regex named groups
    merged: Dict[str, Any] = dict(slots or {})
    for k, v in rg.items():
        if v is not None and str(v).strip() != "":
            merged[k] = str(v).strip()

    maps_to = rule.get("maps_to") or {}
    rule_intent_id = rule.get("intent_id") or maps_to.get("intent_id")
    maps_type = rule.get("type") or maps_to.get("type")

    # se non è un intent, ritorna params espliciti (se presenti)
    if (maps_type and maps_type != "intent") and (rule_intent_id is None):
        return maps_to.get("params", {}) or {}

    intent_id = None
    if rule_intent_id:
        intent_id = rule_intent_id
    elif maps_type == "intent":
        intent_id = (maps_to.get("intent_id") or maps_to.get("id"))

    params: Dict[str, Any] = {}

        # 1) explicit params
    explicit = maps_to.get("params") or {}
    if isinstance(explicit, dict):
        params.update(explicit)

        # IMPORTANT: fai vedere gli explicit anche al builder intent-specific
        # così overview tipo day_of_month=ALL / hour=ALL non falliscono
        for k, v in explicit.items():
            if v is not None and k not in merged:
                merged[k] = v


    # 2) bind required slots by same name  (USA merged)
    required = _required_slots_from_rule(rule)
    for key in required:
        if key in merged:
            params[key] = merged[key]

    # 3) optional explicit mapping (support both params_from_slots and param_map) (USA merged)
    pfs = (
        rule.get("params_from_slots")
        or rule.get("param_map")
        or maps_to.get("params_from_slots")
        or maps_to.get("param_map")
        or {}
    )
    if isinstance(pfs, dict):
        for param_name, slot_name in pfs.items():
            if slot_name in merged:
                params[param_name] = merged[slot_name]

    # 3b) mapping da regex groups dichiarato nello YAML (USA merged)
    pfrg = (
        rule.get("params_from_regex_groups")
        or maps_to.get("params_from_regex_groups")
        or {}
    )
    if isinstance(pfrg, dict):
        for param_name, rg_name in pfrg.items():
            if rg_name in merged:
                params[param_name] = merged[rg_name]

    # 4) special cases by rule id (WIN03 rule-centric)
    rule_id = _safe_rule_id(rule)
    if rule_id == "rule_win03_combo":
        q = merged.get("qbucket_all")
        if isinstance(q, list) and len(q) >= 3:
            params["wbucket"] = _canon_qbucket(q[0])
            params["volbucket"] = _canon_qbucket(q[1])
            params["deltabucket"] = _canon_qbucket(q[2])

    # 5) intent-specific canonicalization/override (USA merged)
    if intent_id:
        built = _build_params(intent_id, merged)
        params.update(built)

    # 6) drop extra params
    _ALLOWED_PARAMS = {
        "volatility_by_hour": {"hour"},
        "success_by_hour": {"hour"},
        "success_by_day_of_month": {"day_of_month"},
        "volatility_by_day_of_month": {"day_of_month"},
        "success_by_weekday": {"weekday"},
        "success_by_month": {"month"},
        "success_by_week_of_month": {"week_of_month"},
    }
    if intent_id in _ALLOWED_PARAMS:
        allowed = _ALLOWED_PARAMS[intent_id]
        params = {k: v for k, v in params.items() if k in allowed}
   
       

    return params



def _build_params_from_regex(rule: dict, regex_groups: dict) -> dict:
    """
    Supporta:
      params_from_regex:
        a: a
        b: b
    oppure:
      maps_to:
        params_from_regex:
          a: a
          b: b

    Dove a/b a destra sono i nomi dei gruppi (?P<a>...) nella regex.
    """
    if not isinstance(regex_groups, dict) or not regex_groups:
        return {}

    maps_to = rule.get("maps_to") or {}
    pfr = rule.get("params_from_regex") or maps_to.get("params_from_regex") or {}
    if not isinstance(pfr, dict) or not pfr:
        return {}

    def _cast_value(v):
        # None rimane None
        if v is None:
            return None

        # se è già numero/bool ok
        if isinstance(v, (int, float, bool)):
            return v

        # string cleanup
        if isinstance(v, str):
            s = v.strip()
            if s == "":
                return None

            # prova int
            if s.isdigit():
                try:
                    return int(s)
                except Exception:
                    return s

            # prova float (anche "11.0")
            try:
                f = float(s.replace(",", "."))
                # se è intero tipo 11.0 -> 11
                if f.is_integer():
                    return int(f)
                return f
            except Exception:
                return s

        # fallback
        return v

    out = {}
    for out_key, group_name in pfr.items():
        if group_name in regex_groups:
            out[out_key] = _cast_value(regex_groups.get(group_name))

    # (opzionale) normalizzazione weekday se usi group tipo "weekday"
    # if "weekday" in out and isinstance(out["weekday"], str):
    #     wd = _weekday_any_to_engine(out["weekday"])
    #     if wd:
    #         out["weekday"] = wd

    return out





