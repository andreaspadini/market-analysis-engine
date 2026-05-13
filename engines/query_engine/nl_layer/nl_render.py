# nl_layer/nl_render.py
from typing import Dict, Any, List, Optional
def _confidence_from_n(n: int) -> str:
    if n < 30:
        return "low"
    if n < 100:
        return "medium"
    return "high"

from typing import Any, Dict

def render_report(report: Dict[str, Any]) -> Dict[str, Any]:
    rep = report.get("report", {}) if isinstance(report, dict) else {}
    kind = report.get("kind") or rep.get("kind")


    # --- known kinds ---
    if kind == "win03_success_by_bucket_vol_delta":
        out = _render_win03(report)

    elif kind == "success_by_weekday_session":
        out = _render_success_by_weekday_session(report)

    elif kind == "mp06_success_accept5m_high_vol":
        out = _render_mp06_high_vol(report)

    elif kind == "mp07_success_accept5m_by_delta_sign":
        out = _render_mp07_delta_sign(report)

    elif kind == "success_by_weekday":
        out = render_success_by_weekday(report)

    elif kind == "retest_proxy_by_session_and_horizon":
        out = _render_retest_proxy_by_session_and_horizon(report)

    elif kind == "lv04_first_close_bucket_prev_day_h60":
        out = _render_lv04_first_close_bucket(report)

    elif kind == "level_acceptance_prev_day_h60":
        out = _render_lv01_level_acceptance(report)

    elif kind == "success_by_weekday_report":
        out = _render_success_by_weekday(report)

    elif kind == "weekday_volatility_and_breakout_success":
        out = _render_weekday_volatility_breakout(report)

    elif kind == "weekday_volatility_and_success":
        out = _render_weekday_volatility_and_success(report)

    elif kind == "conditional_success_given_level_acceptance_prev_day_h60":
        out = _render_conditional_success_given_level_acceptance_prev_day_h60(report)

    elif kind == "time_above_vah_first_close_bucket_prev_day_h60":
        out = _render_time_above_vah_first_close_bucket_prev_day_h60(report)

    elif kind == "win01_success_by_vol_bucket":
        out = _render_win01_success_by_vol_bucket(report)

    elif kind == "calendar":
        out = _render_calendar(report)


    else:
        # --- fallback: always UI-contract compliant ---
        n = report.get("n")
        try:
            n_int = int(n) if n is not None else 0
        except Exception:
            n_int = 0

        out = {
            "text": f"Report '{kind}' disponibile.",
            "kpis": [],
            "warnings": [],
            "confidence": _confidence_from_n(n_int),
            "n": n_int,
        }
 
    # ==================================================
    # POST-PROCESS UI: 2 decimali + % per p_success
    # ==================================================

    def _fmt_value(metric, v):
        if v is None:
            return "NA"
        if metric.startswith("p_success"):
            return f"{v * 100:.2f}%"
        return f"{v:.2f}"

    # vale solo per i report calendar (come i tuoi)
    if kind == "calendar":
        rep = report.get("report", {})
        data = report.get("data", [])

        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            row0 = data[0]
            metric = rep.get("metric")
            dimension = rep.get("dimension")
            title = rep.get("title")

            val = row0.get(metric)
            n = row0.get("n")
            dim_val = row0.get(dimension)

            if metric in row0 and n is not None:
                val_fmt = _fmt_value(metric, val)

                # label dimensione
                if dimension == "hour" and dim_val is not None:
                    dim_label = f"{int(dim_val):02d}:00"
                elif dimension == "day_of_month" and dim_val is not None:
                    dim_label = f"giorno {dim_val}"
                elif dimension == "weekday" and dim_val is not None:
                    dim_label = str(dim_val)
                else:
                    dim_label = ""

                out["text"] = f"{val_fmt} (n={int(n)}) — {title}"
                out["nl_text"] = out["text"]
        
        # safe flag (set to False if frontend schema is strict)
        _ENABLE_NLG = True
        if _ENABLE_NLG:
            out["nl_text"] = _nlg_ui(out, kind)

    return out
    
def _safe_max(rows, key):
    try:
        return max(rows, key=lambda x: float(x.get(key) or float("-inf")))
    except Exception:
        return None

def _safe_min(rows, key):
    try:
        return min(rows, key=lambda x: float(x.get(key) or float("inf")))
    except Exception:
        return None


def _render_retest(r: Dict[str, Any]) -> Dict[str, Any]:
    s = r["session"]
    used = r["used_horizon_min"]
    m = r["metrics"]
    p = m["p_retest_proxy"]["value"]
    n = m["p_retest_proxy"]["n"]
    avg = m["p_retest_proxy"]["session_avg"]
    mae = m["avg_mae_pts"]["value"]
    mae_avg = m["avg_mae_pts"]["session_avg"]
    text = (
        f"Retest proxy in sessione {s.upper()} @ {used}m: "
        f"p_retest_proxy={p:.2f} (n={n}, avg session={avg:.2f}); "
        f"avg_mae_pts={mae:.2f} (avg session={mae_avg:.2f})."
    )
    warnings = []
    if n < 30:
        warnings.append(f"Campione piccolo: n={n} (risultato poco robusto).")

    return {
        "text": text,
        "kpis": [
            {"name": "p_retest_proxy", "value": p, "n": n, "session_avg": avg},
            {"name": "avg_mae_pts", "value": mae, "session_avg": mae_avg},
        ],
        "warnings": warnings,
        "confidence": _confidence_from_n(n),
        "n": n,
    }

def _render_lv04(r: Dict[str, Any]) -> Dict[str, Any]:
    level = r["level"].upper()
    side = r["side"]
    req = r["requested_minutes"]
    mode = r["mode"]
    chosen = r["chosen_bucket"]
    top = r["top_bucket"]
    n = r["total_n"]
    side_it = "sopra" if side == "above" else "sotto"
    text = (
        f"LV04 primo close {side_it} {level}: richiesto {req}m ({mode}). "
        f"Bucket scelto: {chosen['label']} (n={chosen['n']}, share={chosen['share']:.2f}). "
        f"Più frequente: {top['label']} (share={top['share']:.2f}). Totale n={n}."
    )
    warnings = []
    if n < 30:
        warnings.append(f"Campione piccolo: n={n} (risultato poco robusto).")

    return {
        "text": text,
        "kpis": [
            {"name": "chosen_bucket_share", "value": chosen["share"], "n": chosen["n"], "label": chosen["label"]},
            {"name": "top_bucket_share", "value": top["share"], "n": top["n"], "label": top["label"]},
            {"name": "total_n", "value": n},
        ],
        "warnings": warnings,
        "confidence": _confidence_from_n(n),
        "n": n,
    }

def _render_win03(r: Dict[str, Any]) -> Dict[str, Any]:
    w = r["w0900_1300__bucket"]
    v = r["init_vol__bucket"]
    d = r["init_delta__bucket"]
    n = r["n"]
    p = r["metrics"]["p_success_1ATR"]
    text = f"WIN03 combo {w} × {v} × {d}: p_success_1ATR={p:.2f} (n={n})."
    warnings = []
    if n < 30:
        warnings.append(f"Campione piccolo: n={n} (risultato poco robusto).")

    return {
    "text": text,
    "kpis": [{"name": "p_success_1ATR", "value": p, "n": n}],
    "warnings": warnings,
    "confidence": _confidence_from_n(n),
    "n": n,
}

def _render_success_by_weekday_session(r: Dict[str, Any]) -> Dict[str, Any]:
    weekday = r["weekday"]
    session = r["session"]
    metric = r.get("metric", "p_success_1ATR")
    value = r["value"]
    n = r["n"]

    refs = r.get("references", {}) or {}
    tags = r.get("tags", {}) or {}

    weekday_avg = refs.get("weekday_avg")
    session_avg = refs.get("session_avg")
    global_avg = refs.get("global_avg")

    vs_weekday = tags.get("vs_weekday_avg")
    vs_session = tags.get("vs_session_avg")
    vs_global = tags.get("vs_global_avg")

    warnings = []
    if n < 30:
        warnings.append(f"Campione piccolo: n={n} (risultato poco robusto).")

    # confidence se l'hai già aggiunta: usa la tua helper _confidence_from_n
    conf = _confidence_from_n(n) if "_confidence_from_n" in globals() else ("low" if n < 30 else "medium")

    # testo UI: corto ma informativo
    parts = [f"{metric}={value:.2f} (n={n}) — {weekday} / {session.upper()}"]
    if global_avg is not None:
        parts.append(f"vs global {global_avg:.2f}: {vs_global}")
    if session_avg is not None:
        parts.append(f"vs session {session_avg:.2f}: {vs_session}")
    if weekday_avg is not None:
        parts.append(f"vs weekday {weekday_avg:.2f}: {vs_weekday}")

    text = " | ".join(parts)

    kpis = [
        {"name": metric, "value": value, "n": n},
    ]
    # aggiungi reference kpis per cards secondarie (opzionale)
    if global_avg is not None:
        kpis.append({"name": "global_avg", "value": global_avg})
    if session_avg is not None:
        kpis.append({"name": "session_avg", "value": session_avg})
    if weekday_avg is not None:
        kpis.append({"name": "weekday_avg", "value": weekday_avg})

    return {
        "text": text,
        "kpis": kpis,
        "warnings": warnings,
        "confidence": conf,
        "n": n,
    }

def _render_mp06_high_vol(r: Dict[str, Any]) -> Dict[str, Any]:
    session = r["session"]
    n = r["n"]
    m = r.get("metrics", {}) or {}

    p1 = m.get("p_success_1ATR")
    pglob = m.get("p_success_global")
    nglob = m.get("n_global")
    atrb = m.get("avg_atr_before")

    warnings = []
    if n < 30:
        warnings.append(f"Campione piccolo: n={n} (risultato poco robusto).")

    conf = _confidence_from_n(n) if "_confidence_from_n" in globals() else ("low" if n < 30 else "medium")

    text = (
        f"MP06 high volume — {session.upper()}: "
        f"p_success_1ATR={p1:.2f} (n={n}); "
        f"global={pglob:.2f} (n={nglob})."
    )
    if atrb is not None:
        text += f" avg_atr_before={atrb:.2f}."

    kpis = []
    if p1 is not None:
        kpis.append({"name": "p_success_1ATR", "value": p1, "n": n})
    if pglob is not None:
        kpis.append({"name": "p_success_global", "value": pglob, "n": nglob})
    if atrb is not None:
        kpis.append({"name": "avg_atr_before", "value": atrb})

    return {
        "text": text,
        "kpis": kpis,
        "warnings": warnings,
        "confidence": conf,
        "n": n,
    }


def _render_mp07_delta_sign(r: Dict[str, Any]) -> Dict[str, Any]:
    session = r["session"]
    n = r["n"]
    m = r.get("metrics", {}) or {}

    p1 = m.get("p_success_1ATR")
    pglob = m.get("p_success_global")
    nglob = m.get("n_global")
    d = m.get("avg_initial_delta")
    v = m.get("avg_initial_volume")

    warnings = []
    if n < 30:
        warnings.append(f"Campione piccolo: n={n} (risultato poco robusto).")

    conf = _confidence_from_n(n) if "_confidence_from_n" in globals() else ("low" if n < 30 else "medium")

    text = (
        f"MP07 delta — {session.upper()}: "
        f"p_success_1ATR={p1:.2f} (n={n}); "
        f"global={pglob:.2f} (n={nglob})."
    )
    if d is not None:
        text += f" avg_initial_delta={d:.1f}."
    if v is not None:
        text += f" avg_initial_volume={v:.0f}."

    kpis = []
    if p1 is not None:
        kpis.append({"name": "p_success_1ATR", "value": p1, "n": n})
    if pglob is not None:
        kpis.append({"name": "p_success_global", "value": pglob, "n": nglob})
    if d is not None:
        kpis.append({"name": "avg_initial_delta", "value": d})
    if v is not None:
        kpis.append({"name": "avg_initial_volume", "value": v})

    return {
        "text": text,
        "kpis": kpis,
        "warnings": warnings,
        "confidence": conf,
        "n": n,
    }
def render_success_by_weekday(rep: dict) -> dict:
    n = int(rep.get("n", 0) or 0)
    conf = _confidence_from_n(n)

    value = float(rep.get("value", 0.0))
    weekday = rep.get("weekday", "?")

    refs = rep.get("references", {}) or {}
    global_avg = float(refs.get("global_avg", 0.0))
    global_n = refs.get("global_n")

    tags = rep.get("tags", {}) or {}
    vs_global = tags.get("vs_global_avg", "n/a")

    warnings = []
    if n and n < 30:
        warnings.append(f"Campione piccolo: n={n} (risultato poco robusto).")

    txt = (
        f"p_success_1ATR={value:.2f} (n={n}) — {weekday} | "
        f"vs global {global_avg:.2f}: {vs_global}"
        + (f" (global n={global_n})" if global_n is not None else "")
    )

    return {
        "text": txt,
        "kpis": [
            {"name": "p_success_1ATR", "value": value, "n": n},
            {"name": "global_avg", "value": global_avg, "n": global_n} if global_n is not None else {"name": "global_avg", "value": global_avg},
        ],
        "warnings": warnings,
        "confidence": conf,
        "n": n,
    }
def _render_retest_proxy_by_session_and_horizon(r: Dict[str, Any]) -> Dict[str, Any]:
    sess = r.get("session", "?")
    req = int(r.get("requested_minutes", 0) or 0)
    used = int(r.get("used_horizon_min", 0) or 0)
    proxy = bool(r.get("used_is_proxy_bucket", False))

    metrics = r.get("metrics", {}) or {}
    p = metrics.get("p_retest_proxy", {}) or {}
    mae = metrics.get("avg_mae_pts", {}) or {}

    p_val = float(p.get("value", 0.0) or 0.0)
    p_n = int(p.get("n", 0) or 0)
    p_savg = float(p.get("session_avg", 0.0) or 0.0)

    mae_val = float(mae.get("value", 0.0) or 0.0)
    mae_savg = float(mae.get("session_avg", 0.0) or 0.0)

    # UI helpers (coerente con gli altri renderer)
    warnings: List[str] = []
    conf = _confidence_from_n(p_n) if "_confidence_from_n" in globals() else ("low" if p_n < 30 else "medium")
    if p_n and p_n < 30:
        warnings.append(f"Campione piccolo: n={p_n} (risultato poco robusto).")

    note = f"(richiesti {req}m → usati {used}m)" if proxy else f"({used}m)"
    tag = "above_avg" if p_val > p_savg else ("below_avg" if p_val < p_savg else "flat")

    text = (
        f"p_retest_proxy={p_val:.2f} (n={p_n}) — {sess.upper()} {note} | "
        f"vs session {p_savg:.2f}: {tag} | MAE {mae_val:.2f} vs {mae_savg:.2f}"
    )

    return {
        "text": text,
        "kpis": [
            {"name": "p_retest_proxy", "value": p_val, "n": p_n},
            {"name": "session_avg", "value": p_savg},
            {"name": "avg_mae_pts", "value": mae_val},
            {"name": "avg_mae_session", "value": mae_savg},
        ],
        "warnings": warnings,
        "confidence": conf,
        "n": p_n,
    }

def _render_lv04_first_close_bucket(r: Dict[str, Any]) -> Dict[str, Any]:
    level = r.get("level", "?")
    side = r.get("side", "?")
    req = int(r.get("requested_minutes", 0) or 0)
    mode = r.get("mode", "nearest")
    total_n = int(r.get("total_n", r.get("n", 0)) or 0)

    chosen = r.get("chosen_bucket", {}) or {}
    top = r.get("top_bucket", {}) or {}

    cb_label = chosen.get("label", "?")
    cb_low = chosen.get("low_min", "?")
    cb_high = chosen.get("high_min", "?")
    cb_n = int(chosen.get("n", 0) or 0)
    cb_share = float(chosen.get("share", 0.0) or 0.0)

    tb_label = top.get("label", "?")
    tb_n = int(top.get("n", 0) or 0)
    tb_share = float(top.get("share", 0.0) or 0.0)

    warnings = []
    if total_n and total_n < 30:
        warnings.append(f"Campione piccolo: n={total_n} (risultato poco robusto).")

    conf = _confidence_from_n(total_n) if "_confidence_from_n" in globals() else ("low" if total_n < 30 else "medium")

    txt = (
        f"LV04 first close {side} {level} — requested {req}m (mode={mode}) | "
        f"chosen bucket {cb_label} ({cb_low}-{cb_high}m): share={cb_share:.2f} (n={cb_n}/{total_n}) | "
        f"top bucket {tb_label}: share={tb_share:.2f} (n={tb_n}/{total_n})"
    )

    return {
        "text": txt,
        "kpis": [
            {"name": "chosen_share", "value": cb_share, "n": cb_n},
            {"name": "top_share", "value": tb_share, "n": tb_n},
            {"name": "total_n", "value": total_n},
        ],
        "warnings": warnings,
        "confidence": conf,
        "n": total_n,
    }

def _render_lv01_level_acceptance(r: Dict[str, Any]) -> Dict[str, Any]:
    level = r.get("level")
    side = r.get("side")

    # NEW: supporta sia vecchio schema (accept_minutes) sia nuovo (requested/used)
    req = r.get("requested_minutes")
    used = r.get("used_minutes")
    mode = r.get("mode", "nearest")

    if req is not None and used is not None:
        try:
            req_i = int(req)
            used_i = int(used)
        except Exception:
            req_i, used_i = req, used

        if req_i != used_i:
            mode_s = f" (mode={mode})" if mode and mode != "nearest" else ""
            horizon = f"{req_i}m→{used_i}m{mode_s}"

        else:
            horizon = f"{req_i}m"
    else:
        # fallback compatibilità (vecchio campo)
        minutes = r.get("accept_minutes")
        horizon = f"{minutes}m" if minutes is not None else "?"

    n = int(r.get("n", 0) or 0)
    conf = _confidence_from_n(n) if "_confidence_from_n" in globals() else ("low" if n < 30 else "medium")

    m = r.get("metrics", {}) or {}
    p_accept = m.get("p_accept")
    p_touched = m.get("p_touched")
    p_closed = m.get("p_closed_side")
    p_success = m.get("p_success_1ATR")

    def fmt(x):
        return None if x is None else round(float(x), 2)

    text = (
        f"LV01 acceptance prev-day — {level} {side} @ {horizon}: "
        f"p_accept={fmt(p_accept)} | p_touched={fmt(p_touched)} | "
        f"p_closed_side={fmt(p_closed)} | p_success_1ATR={fmt(p_success)} (n={n})"
    )

    kpis = []
    if p_accept is not None: kpis.append({"name": "p_accept", "value": float(p_accept), "n": n})
    if p_touched is not None: kpis.append({"name": "p_touched", "value": float(p_touched)})
    if p_closed is not None: kpis.append({"name": "p_closed_side", "value": float(p_closed)})
    if p_success is not None: kpis.append({"name": "p_success_1ATR", "value": float(p_success)})

    warnings = []
    if n and n < 30:
        warnings.append(f"Campione piccolo: n={n} (risultato poco robusto).")

    return {
        "text": text,
        "kpis": kpis,
        "warnings": warnings,
        "confidence": conf,
        "n": n,
    }

def _safe_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def _render_success_by_weekday(r):
    # Prova a leggere una struttura "rows" o simile
    rows = r.get("rows") or r.get("data") or r.get("by_weekday") or []
    n = int(r.get("n", 0) or 0)

    # prova a trovare best weekday se c'è info
    best = r.get("best") or {}
    best_day = best.get("weekday") or best.get("day")
    best_p = _safe_float(best.get("p_success") or best.get("success_rate"))

    text = "Success by weekday."
    if best_day is not None and best_p is not None:
        text = f"Success by weekday — best={best_day}: p_success={best_p:.2f}"
    elif rows:
        text = f"Success by weekday — {len(rows)} rows"

    kpis = []
    if best_p is not None:
        kpis.append({"name": "best_p_success", "value": float(best_p)})
    if n:
        kpis.append({"name": "total_n", "value": n})

    return {
        "text": text,
        "kpis": kpis,
        "warnings": [],
        "confidence": "high" if n >= 100 else ("medium" if n >= 30 else "low"),
        "n": n if n else None,
    }

def _render_success_by_weekday_session(r: Dict[str, Any]) -> Dict[str, Any]:
    """
    Report kind: success_by_weekday_session

    Forma reale (single point):
      {
        "weekday": "...",
        "session": "...",
        "metric": "p_success_1ATR" | ...,
        "value": <float>,
        "n": <int>,
        "references": {...},
        "tags": {...}
      }
    """
    weekday = r.get("weekday")
    session = r.get("session")
    metric = r.get("metric") or "p_success"
    value = r.get("value")
    refs = r.get("references") or {}

    # n
    n = r.get("n")
    try:
        n_int = int(n) if n is not None else 0
    except Exception:
        n_int = 0

    warnings: List[str] = []
    if n_int and n_int < 30:
        warnings.append(f"Campione piccolo: n={n_int} (risultato poco robusto).")

    # baseline / global (best-effort)
    # (non sappiamo le chiavi esatte: proviamo le più comuni)
    global_p = (
        refs.get("global_p_success_1ATR")
        or refs.get("global_p_success")
        or refs.get("p_success_global")
        or refs.get("global_value")
    )

    kpis: List[Dict[str, Any]] = []
    if weekday is not None:
        kpis.append({"name": "weekday", "value": weekday})
    if session is not None:
        kpis.append({"name": "session", "value": session})

    if value is not None:
        kpis.append({"name": metric, "value": value, "n": n_int})

    if global_p is not None:
        kpis.append({"name": "p_success_global", "value": global_p})

    # testo
    title = "Success by weekday & session"
    scope = []
    if weekday is not None:
        scope.append(f"{weekday}")
    if session is not None:
        scope.append(f"{session}")
    scope_txt = " / ".join(scope) if scope else "ALL"

    main = f"{metric}={_fmt(value)}" if value is not None else f"{metric}=n/a"
    text = f"{title} — {scope_txt}: {main} (n={n_int})"

    if global_p is not None:
        text += f" | global={_fmt(global_p)}"

    return {
        "text": text,
        "kpis": kpis,
        "warnings": warnings,
        "confidence": _confidence_from_n(n_int),
        "n": n_int,
    }

def _render_weekday_volatility_breakout(r: dict) -> dict:
    """
    Backward-compatible renderer.
    Alcune versioni usavano kind='weekday_volatility_and_breakout_success'
    ma il report corrente produce kind='weekday_volatility_and_success'.
    Reindirizziamo al renderer ufficiale.
    """
    # forza il kind “canonico” se arriva quello vecchio
    if isinstance(r, dict) and r.get("kind") == "weekday_volatility_and_breakout_success":
        r = dict(r)
        r["kind"] = "weekday_volatility_and_success"
    return _render_weekday_volatility_and_success(r)


def _fmt(x: Any, nd: int = 2) -> Optional[float]:
    if x is None:
        return None
    try:
        return round(float(x), nd)
    except Exception:
        return None


def _kpi(name: str, value: Any, n: Optional[int] = None) -> Dict[str, Any]:
    k = {"name": name, "value": value}
    if n is not None:
        k["n"] = n
    return k


def _confidence_from_n(n: int) -> str:
    # se già esiste nel file, usa la tua. Qui una fallback robusta.
    if n >= 80:
        return "high"
    if n >= 30:
        return "medium"
    return "low"

def _render_weekday_volatility_and_success(r: Dict[str, Any]) -> Dict[str, Any]:
    """
    Report kind: weekday_volatility_and_success

    Supporta:
      - overview: weekday="ALL", rows/best/worst
      - single: weekday="Monday"... metrics/n + references
    """
    tags = r.get("tags") or {}
    mode = (tags.get("mode") or "").lower()
    weekday = r.get("weekday") or "ALL"

    refs = r.get("references") or {}
    g_atr = refs.get("global_avg_atr_before_pts")
    g_n_vol = refs.get("global_n_vol")
    g_p = refs.get("global_avg_p_success_1ATR")
    g_n_succ = refs.get("global_n_succ")

    warnings: List[str] = []
    kpis: List[Dict[str, Any]] = []

    # sempre: KPI globali (se presenti)
    if g_atr is not None:
        kpis.append({"name": "global_avg_atr_before_pts", "value": g_atr, "n": g_n_vol})
    if g_p is not None:
        kpis.append({"name": "global_avg_p_success_1ATR", "value": g_p, "n": g_n_succ})

    if mode == "single" or str(weekday).upper() != "ALL":
        # supporta 2 formati:
        # A) nuovo (reale): volatility/success come oggetti {value,n,weekly_avg,tag}
        # B) legacy: metrics + n
        metrics = r.get("metrics") or {}
        nn = r.get("n") or {}

        vol_obj = r.get("volatility") if isinstance(r.get("volatility"), dict) else {}
        succ_obj = r.get("success") if isinstance(r.get("success"), dict) else {}

        atr = vol_obj.get("value")
        p_succ = succ_obj.get("value")

        # fallback legacy
        if atr is None:
            atr = metrics.get("avg_atr_before_pts")
        if p_succ is None:
            p_succ = metrics.get("p_success_1ATR")

        n_vol = vol_obj.get("n")
        n_succ = succ_obj.get("n")

        # fallback legacy
        if n_vol is None:
            n_vol = nn.get("volatility")
        if n_succ is None:
            n_succ = nn.get("success")

        # n effettivo per confidence/warnings
        try:
            n_candidates = [int(x) for x in [n_vol, n_succ] if x is not None]
            n_eff = min(n_candidates) if n_candidates else 0
        except Exception:
            n_eff = 0

        if n_eff and n_eff < 30:
            warnings.append(f"Campione piccolo: n={n_eff} (risultato poco robusto).")

        # KPI specifici (NON mettere value=None)
        kpis.append({"name": "weekday", "value": weekday})
        if atr is not None:
            kpis.append({"name": "avg_atr_before_pts", "value": atr, "n": n_vol})
        if p_succ is not None:
            kpis.append({"name": "p_success_1ATR", "value": p_succ, "n": n_succ})

        # se disponibili, aggiungi confronto vs weekly_avg
        if vol_obj.get("weekly_avg") is not None:
            kpis.append({"name": "global_avg_atr_before_pts", "value": vol_obj.get("weekly_avg")})
        if succ_obj.get("weekly_avg") is not None:
            kpis.append({"name": "global_avg_p_success_1ATR", "value": succ_obj.get("weekly_avg")})

        text = (
            f"Weekday vol+success — scope={weekday}. "
            f"ATR={_fmt(atr)} (n_vol={n_vol}) | "
            f"p_success_1ATR={_fmt(p_succ)} (n_succ={n_succ}). "
            f"Global: ATR={_fmt(g_atr)} (n_vol={g_n_vol}) | "
            f"p_success_1ATR={_fmt(g_p)} (n_succ={g_n_succ})."
        )

        confidence = _confidence_from_n(n_eff) if n_eff else "low"

        return {
            "text": text,
            "kpis": kpis,
            "warnings": warnings,
            "confidence": confidence,
            "n": n_eff,
        }


    # -----------------------------
    # OVERVIEW MODE (ALL)
    # -----------------------------
    rows = r.get("rows") or []
    best = r.get("best") or {}
    worst = r.get("worst") or {}

    best_s = best.get("success") or None
    worst_s = worst.get("success") or None
    best_v = best.get("volatility") or None
    worst_v = worst.get("volatility") or None

    # fallback se best/worst non ci sono o sono vuoti
    def _safe_max(rows_, key):
        try:
            return max(rows_, key=lambda x: float(x.get(key) or float("-inf")))
        except Exception:
            return None

    def _safe_min(rows_, key):
        try:
            return min(rows_, key=lambda x: float(x.get(key) or float("inf")))
        except Exception:
            return None

    best_vol = best_v if isinstance(best_v, dict) and best_v else None
    worst_vol = worst_v if isinstance(worst_v, dict) and worst_v else None
    best_succ = best_s if isinstance(best_s, dict) and best_s else None
    worst_succ = worst_s if isinstance(worst_s, dict) and worst_s else None

    if best_vol is None:
        best_vol = _safe_max(rows, "avg_atr_before_pts")
    if worst_vol is None:
        worst_vol = _safe_min(rows, "avg_atr_before_pts")
    if best_succ is None:
        best_succ = _safe_max(rows, "p_success_1ATR")
    if worst_succ is None:
        worst_succ = _safe_min(rows, "p_success_1ATR")

    if not rows:
        warnings.append("Nessuna riga trovata nel report (rows vuoto).")

    # n_eff + warning campione piccolo
    n_eff = min(g_n_vol or 0, g_n_succ or 0)
    if n_eff and n_eff < 30:
        warnings.append(f"Campione globale basso (n={n_eff}): interpretare con cautela.")

    def wk_label(x):
        if not isinstance(x, dict):
            return "n/a"
        return (x.get("weekday") or "n/a")

    def wk_n(x, field):
        if not isinstance(x, dict):
            return None
        try:
            return int(float(x.get(field) or 0))
        except Exception:
            return None

    def wk_val(x, field, nd=2):
        if not isinstance(x, dict):
            return None
        return _fmt(x.get(field), nd=nd)

    text = (
        f"Weekday vol+success — scope=ALL. "
        f"Global: ATR={_fmt(g_atr)} (n_vol={g_n_vol}) | "
        f"p_success_1ATR={_fmt(g_p)} (n_succ={g_n_succ}). "
        f"Best success: {wk_label(best_succ)} p={wk_val(best_succ,'p_success_1ATR')} (n={wk_n(best_succ,'n_succ')}). "
        f"Worst success: {wk_label(worst_succ)} p={wk_val(worst_succ,'p_success_1ATR')} (n={wk_n(worst_succ,'n_succ')}). "
        f"Max vol: {wk_label(best_vol)} ATR={wk_val(best_vol,'avg_atr_before_pts')} (n={wk_n(best_vol,'n_vol')}). "
        f"Min vol: {wk_label(worst_vol)} ATR={wk_val(worst_vol,'avg_atr_before_pts')} (n={wk_n(worst_vol,'n_vol')})."
    )

    # KPI overview (aggiungi solo se presenti dict validi)
    if isinstance(best_succ, dict):
        kpis.append(_kpi("best_success_weekday", wk_label(best_succ)))
        kpis.append(_kpi("best_success_p_success_1ATR", best_succ.get("p_success_1ATR"), wk_n(best_succ, "n_succ")))

    if isinstance(worst_succ, dict):
        kpis.append(_kpi("worst_success_weekday", wk_label(worst_succ)))
        kpis.append(_kpi("worst_success_p_success_1ATR", worst_succ.get("p_success_1ATR"), wk_n(worst_succ, "n_succ")))

    if isinstance(best_vol, dict):
        kpis.append(_kpi("max_vol_weekday", wk_label(best_vol)))
        kpis.append(_kpi("max_vol_avg_atr_before_pts", best_vol.get("avg_atr_before_pts"), wk_n(best_vol, "n_vol")))

    if isinstance(worst_vol, dict):
        kpis.append(_kpi("min_vol_weekday", wk_label(worst_vol)))
        kpis.append(_kpi("min_vol_avg_atr_before_pts", worst_vol.get("avg_atr_before_pts"), wk_n(worst_vol, "n_vol")))

    confidence = _confidence_from_n(n_eff) if n_eff else "low"

    return {
        "text": text,
        "kpis": kpis,
        "warnings": warnings,
        "confidence": confidence,
        "n": n_eff,
    }

def _render_time_above_vah_first_close_bucket_prev_day_h60(r: Dict[str, Any]) -> Dict[str, Any]:
    rr = dict(r)
    rr.setdefault("level", "VAH")
    rr.setdefault("side", "above")

    out = _render_lv04_first_close_bucket(rr)

    # fix doppione testo (lavora sull'output, non su "txt")
    if isinstance(out, dict) and isinstance(out.get("text"), str):
        t = out["text"]

        # rimozione robusta del doppione "above VAH"
        t = t.replace(" (bucket) above VAH", " (bucket)")
        t = t.replace(" above VAH —", " —")   # fallback se cambia forma

        # eventuale normalizzazione vecchia
        t = t.replace("LV04 first close", "Time above VAH (bucket)")

        out["text"] = t

    

    return out

def _render_conditional_success_given_level_acceptance_prev_day_h60(r: Dict[str, Any]) -> Dict[str, Any]:
    level = r.get("level", r.get("ref_level", "?"))

    # nel report reale c'è "given_accept_minutes"
    given_m = r.get("given_accept_minutes", r.get("given_minutes", r.get("minutes")))
    horizon = f"{int(given_m)}m" if given_m is not None else "?"

    n = int(r.get("n", r.get("total_n", 0)) or 0)
    confidence = _confidence_from_n(n)

    # metrics è top-level
    m = r.get("metrics", {}) or {}
    p = m.get("p_success_1ATR", m.get("p_success"))

    warnings: List[str] = []
    if n and n < 30:
        warnings.append(f"Campione piccolo: n={n} (risultato poco robusto).")
    if p is None:
        warnings.append("Manca metrica p_success_1ATR nel report.")

    # testo “true”: è già condizionato per definizione dell’intent
    text = f"Success (1ATR) dato acceptance entro {horizon} — level={level}"
    if p is not None:
        text += f": p_success={float(p):.2f}"
    if n:
        text += f" (n={n})"

    kpis: List[Dict[str, Any]] = []
    if p is not None:
        kpis.append({"name": "p_success_1ATR_given_accept", "value": float(p), "n": n})
    if given_m is not None:
        kpis.append({"name": "given_accept_minutes", "value": int(given_m)})

    return {
        "text": text,
        "kpis": kpis,
        "warnings": warnings,
        "confidence": confidence,
        "n": n,
    }

def _render_win01_success_by_vol_bucket(r: Dict[str, Any]) -> Dict[str, Any]:
    """
    WIN01: success rate by volatility bucket.

    Supporta due schemi:
    1) "table/rows": data.rows (o rows/table/buckets/series/items) con righe bucket + p_success + n
    2) "single bucket vs global" (schema visto nel tuo out_smoke/win01):
       - top-level: bucket, n
       - metrics: p_success_1ATR, p_success_global, n_global
    """
    data = r.get("data") if isinstance(r.get("data"), dict) else {}

    # --- helpers ---
    def _as_list(x: Any) -> List[Any]:
        return x if isinstance(x, list) else []

    def _label(x: Dict[str, Any]) -> str:
        return str(
            x.get("bucket")
            or x.get("label")
            or x.get("vol_bucket")
            or x.get("name")
            or "?"
        )

    def _n_of(x: Dict[str, Any]) -> int:
        try:
            return int(x.get("n", x.get("count", 0)) or 0)
        except Exception:
            return 0

    def _p_of(x: Dict[str, Any]):
        # prova varie chiavi comuni
        v = x.get("p_success_1ATR")
        if v is None: v = x.get("p_success")
        if v is None: v = x.get("success_rate")
        if v is None: v = x.get("p")
        if v is None: v = x.get("p_win01")
        if v is None: v = x.get("win01")
        if v is None: v = x.get("p_success_win01")
        if v is None:
            return None
        try:
            return float(v)
        except Exception:
            return None

    # --- collect rows from multiple possible locations ---
    rows: List[Dict[str, Any]] = []

    # prefer: data.rows
    rows = _as_list(data.get("rows")) if isinstance(data, dict) else []
    if not rows:
        # other candidates: data.table / data.buckets / ...
        for key in ("table", "buckets", "series", "items"):
            cand = _as_list(data.get(key)) if isinstance(data, dict) else []
            if cand:
                rows = cand
                break

    if not rows:
        # top-level candidates: rows/table/buckets/...
        for key in ("rows", "table", "buckets", "series", "items"):
            cand = _as_list(r.get(key))
            if cand:
                rows = cand
                break

    scored: List[tuple] = []
    for x in rows:
        if not isinstance(x, dict):
            continue
        p = _p_of(x)
        if p is None:
            continue
        scored.append((p, _n_of(x), _label(x)))

    # total n
    total_n = int(r.get("n", r.get("total_n", 0)) or 0)
    if total_n == 0 and scored:
        total_n = sum(n for _, n, _ in scored)

    # --- Case 1: table/rows available ---
    if scored:
        best_p, best_n, best_label = max(scored, key=lambda t: t[0])
        worst_p, worst_n, worst_label = min(scored, key=lambda t: t[0])
        delta = best_p - worst_p

        warnings: List[str] = []
        conf = _confidence_from_n(total_n) if total_n else "low"
        if total_n and total_n < 30:
            warnings.append(f"Campione piccolo: n={total_n} (risultato poco robusto).")
        if best_n and best_n < 10:
            warnings.append(f"Best bucket con pochi esempi: n={best_n}.")
        if worst_n and worst_n < 10:
            warnings.append(f"Worst bucket con pochi esempi: n={worst_n}.")

        text = (
            f"WIN01 success by vol bucket — best {best_label}: p={best_p:.2f} (n={best_n}) | "
            f"worst {worst_label}: p={worst_p:.2f} (n={worst_n}) | Δ={delta:.2f} (total n={total_n})"
        )

        kpis = [
            {"name": "best_bucket", "value": best_label, "n": best_n},
            {"name": "best_p_success", "value": best_p, "n": best_n},
            {"name": "worst_bucket", "value": worst_label, "n": worst_n},
            {"name": "worst_p_success", "value": worst_p, "n": worst_n},
            {"name": "delta_best_worst", "value": delta},
            {"name": "total_n", "value": total_n},
        ]

        return {
            "text": text,
            "kpis": kpis,
            "warnings": warnings,
            "confidence": conf,
            "n": total_n,
        }

    # --- Case 2: single bucket vs global (schema reale out_smoke/win01) ---
    bucket = r.get("bucket", r.get("label", "?"))
    m = r.get("metrics", {}) or {}

    p_bucket = m.get("p_success_1ATR", m.get("p_success"))
    p_global = m.get("p_success_global")
    n_bucket = int(r.get("n", 0) or 0)
    n_global = int(m.get("n_global", 0) or 0)

    warnings: List[str] = []
    base_n = n_bucket if n_bucket else n_global
    conf = _confidence_from_n(base_n) if base_n else "low"

    if n_bucket and n_bucket < 30:
        warnings.append(f"Campione piccolo nel bucket: n={n_bucket}.")

    if p_bucket is None:
        warnings.append("Manca p_success_1ATR nel report.")
        return {
            "text": "WIN01 success by vol bucket — dati non disponibili nel formato atteso.",
            "kpis": [],
            "warnings": warnings,
            "confidence": conf,
            "n": n_bucket,
        }

    p_bucket_f = float(p_bucket)
    text = f"WIN01 success — bucket {bucket}: p={p_bucket_f:.2f} (n={n_bucket})"

    kpis: List[Dict[str, Any]] = [
        {"name": "bucket", "value": bucket, "n": n_bucket},
        {"name": "p_success_1ATR_bucket", "value": p_bucket_f, "n": n_bucket},
    ]

    if p_global is not None:
        p_global_f = float(p_global)
        delta = p_bucket_f - p_global_f
        text += f" | global p={p_global_f:.2f} (n={n_global}) | Δ={delta:.2f}"
        kpis += [
            {"name": "p_success_1ATR_global", "value": p_global_f, "n": n_global},
            {"name": "delta_bucket_minus_global", "value": delta},
            {"name": "n_global", "value": n_global},
        ]

    return {
        "text": text,
        "kpis": kpis,
        "warnings": warnings,
        "confidence": conf,
        "n": n_bucket,
    }
def _nlg_ui(out: Dict[str, Any], kind: str) -> str:
    """
    Deterministic NLG layer on top of UI contract output.
    Uses kind + kpis + warnings + n to produce a more readable sentence.
    Never raises.
    """
    _KPI_ALIASES = {
        # probabilità di successo (tutte le varianti che abbiamo visto nei renderer)
        "p_success": [
            "p_success",
            "p_success_1ATR",
            "p_success_1ATR_given_accept",  # per conditional_success_given_level_acceptance
            "p_success_1ATR_bucket",
            "best_p_success",
        ],
        # probabilità globale
        "p_global": [
            "p_success_global",
            "p_success_1ATR_global",
        ],
        # delta tra bucket e globale / best-worst
        "delta": [
            "delta_bucket_minus_global",
            "delta_best_worst",
            "delta_best_worst_abs",
        ],
        # bucket principali
        "bucket": [
            "bucket",
            "best_bucket",
        ],
        # eventuale bucket peggiore
        "worst_bucket": [
            "worst_bucket",
        ],
        # minuti di acceptance
        "given_accept_minutes": [
            "given_accept_minutes",
            "accept_minutes",
            "minutes",
        ],
        # time-above bucket KPIs
        "chosen_share": ["chosen_share"],
        "top_share": ["top_share"],
        "total_n": ["total_n"],
        
        # acceptance / level KPIs
        "p_accept": ["p_accept", "p_accept_10m", "p_accept_10m_above", "p_accept_10m_below"],
        "p_touched": ["p_touched"],
        "p_closed": ["p_closed", "p_closed_above", "p_closed_below", "p_closed_level"],
        "horizon_min": ["horizon_min", "minutes", "m", "horizon"],
        "level": ["level"],

        # retest KPIs / params (se disponibili)
        "p_retest": ["p_retest", "p_retest_proxy", "retest_p", "prob_retest"],
        "session": ["session"],
        "used_horizon_min": ["used_horizon_min", "horizon_min", "used_minutes"],
        "requested_minutes": ["requested_minutes", "minutes", "m"],

        # weekday success KPIs (nomi “tipici”)
        "weekday": ["weekday", "day"],
        "p_success_weekday": ["p_success_weekday", "p_success", "p_success_1ATR"],

                # weekday vol + success KPIs
        "weekday": ["weekday"],
        "avg_atr_before_pts": ["avg_atr_before_pts", "global_avg_atr_before_pts"],
        "p_success_1ATR": ["p_success_1ATR", "global_avg_p_success_1ATR"],

        "best_success_weekday": ["best_success_weekday"],
        "best_success_p": ["best_success_p_success_1ATR"],

        "worst_success_weekday": ["worst_success_weekday"],
        "worst_success_p": ["worst_success_p_success_1ATR"],

        "max_vol_weekday": ["max_vol_weekday"],
        "max_vol_atr": ["max_vol_avg_atr_before_pts"],

        "min_vol_weekday": ["min_vol_weekday"],
        "min_vol_atr": ["min_vol_avg_atr_before_pts"],

    }

    try:
        text = out.get("text") or ""
        kpis = out.get("kpis") or []
        warnings = out.get("warnings") or []
        n = out.get("n")

        def kpi(name: str):
            for x in kpis:
                if isinstance(x, dict) and x.get("name") == name:
                    return x.get("value")
            return None

        def kpi_any(canon: str):
            for name in _KPI_ALIASES.get(canon, [canon]):
                v = kpi(name)
                if v is not None:
                    return v
            return None

        def _to_float(v):
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                s = v.strip().replace(",", ".")
                try:
                    return float(s)
                except Exception:
                    return None
            try:
                return float(v)
            except Exception:
                return None

        def pct(v):
            x = _to_float(v)
            if x is None:
                return None
            return f"{x * 100:.0f}%"

        def num(v, nd: int = 2):
            x = _to_float(v)
            if x is None:
                return None
            return f"{x:.{nd}f}"


        # --- kind-specific best-effort summaries ---

        if kind == "win01_success_by_vol_bucket":
            p = kpi_any("p_success")
            delta = kpi_any("delta")
            bucket = kpi_any("bucket")
            p_global = kpi_any("p_global")

            if p is not None and bucket is not None:
                s = (
                    f"Nel bucket {bucket} la probabilità di successo (WIN01, 1ATR) è "
                    f"{pct(p) or num(p)}."
                )
                if p_global is not None:
                    s += f" Globale: {pct(p_global) or num(p_global)}."
                if delta is not None:
                    s += f" Δ: {pct(delta) or num(delta)}."
                if n:
                    s += f" (n={n})"
                if warnings:
                    s += " Nota: " + "; ".join(warnings)
                return s

        if kind == "conditional_success_given_level_acceptance_prev_day_h60":
            p = kpi_any("p_success")
            m = kpi_any("given_accept_minutes")

            if p is not None:
                s = "Probabilità di successo (1ATR) condizionata all’acceptance"
                if m is not None:
                    try:
                        s += f" entro {int(m)}m"
                    except Exception:
                        s += f" entro {m}m"
                s += f": {pct(p) or num(p)}"
                if n:
                    s += f" (n={n})"
                if warnings:
                    s += ". Nota: " + "; ".join(warnings)
                return s

        if kind == "time_above_vah_first_close_bucket_prev_day_h60":
            chosen = kpi_any("chosen_share")
            top = kpi_any("top_share")
            tot = kpi_any("total_n") or n

            if chosen is not None and top is not None:
                s = (
                    f"Quota di tempo sopra VAH nel bucket scelto: {pct(chosen) or num(chosen)}."
                    f" Bucket dominante: {pct(top) or num(top)}."
                )
                if tot is not None:
                    try:
                        s += f" (n={int(tot)})"
                    except Exception:
                        s += f" (n={tot})"
                if warnings:
                    s += " Nota: " + "; ".join(warnings)
                return s

        if kind == "level_acceptance_prev_day_h60":
            level = kpi_any("level")
            horizon = kpi_any("horizon_min") or kpi_any("used_horizon_min")
            p_acc = kpi_any("p_accept")
            p_touch = kpi_any("p_touched")
            p_close = kpi_any("p_closed")
            p_succ = kpi_any("p_success")  # già aliasato

            parts = []
            if level is not None:
                parts.append(f"Acceptance su {level}")
            else:
                parts.append("Acceptance sul livello")

            if horizon is not None:
                try:
                    parts.append(f"(entro {int(horizon)}m)")
                except Exception:
                    parts.append(f"(entro {horizon}m)")

            s = " ".join(parts)

            details = []
            if p_acc is not None:
                details.append(f"acceptance {pct(p_acc) or num(p_acc)}")
            if p_touch is not None:
                details.append(f"touch {pct(p_touch) or num(p_touch)}")
            if p_close is not None:
                details.append(f"close {pct(p_close) or num(p_close)}")
            if p_succ is not None:
                details.append(f"successo 1ATR {pct(p_succ) or num(p_succ)}")

            if details:
                s += ": " + " | ".join(details)

            if n:
                s += f" (n={n})"
            if warnings:
                s += " Nota: " + "; ".join(warnings)
            return s

        if kind == "retest_proxy_by_session_and_horizon":
            p_ret = kpi_any("p_retest") or kpi_any("p_success")  # alcuni renderer lo chiamano “success”
            sess = kpi_any("session")
            used_h = kpi_any("used_horizon_min") or kpi_any("horizon_min")
            req = kpi_any("requested_minutes")

            s = "Probabilità di retest"
            if sess is not None:
                s += f" in sessione {sess}"
            if req is not None:
                try:
                    s += f" entro {int(req)}m"
                except Exception:
                    s += f" entro {req}m"
            if used_h is not None:
                try:
                    s += f" (horizon usato {int(used_h)}m)"
                except Exception:
                    s += f" (horizon usato {used_h}m)"

            if p_ret is not None:
                s += f": {pct(p_ret) or num(p_ret)}"
            if n:
                s += f" (n={n})"
            if warnings:
                s += " Nota: " + "; ".join(warnings)
            return s

        if kind == "success_by_weekday":
            wd = kpi_any("weekday")
            p = kpi_any("p_success_weekday") or kpi_any("p_success")
            s = "Successo per weekday"
            if wd is not None:
                s += f" ({wd})"
            if p is not None:
                s += f": {pct(p) or num(p)}"
            if n:
                s += f" (n={n})"
            if warnings:
                s += " Nota: " + "; ".join(warnings)
            return s
        
        if kind == "weekday_volatility_and_success":
            wd = kpi_any("weekday")

            # --- single weekday mode ---
            if wd is not None:
                atr = kpi_any("avg_atr_before_pts")
                ps = kpi_any("p_success_1ATR") or kpi_any("p_success")
                s = f"Weekday {wd}:"
                if atr is not None:
                    s += f" volatilità media (ATR) {num(atr)} pt."
                if ps is not None:
                    s += f" Successo 1ATR {pct(ps) or num(ps)}."
                if n:
                    s += f" (n={n})"
                if warnings:
                    s += " Nota: " + "; ".join(warnings)
                return s

            # --- overview mode ---
            g_atr = kpi_any("avg_atr_before_pts")
            g_ps = kpi_any("p_success_1ATR") or kpi_any("p_success")

            best_wd = kpi_any("best_success_weekday")
            best_p = kpi_any("best_success_p")

            worst_wd = kpi_any("worst_success_weekday")
            worst_p = kpi_any("worst_success_p")

            max_wd = kpi_any("max_vol_weekday")
            max_atr = kpi_any("max_vol_atr")

            min_wd = kpi_any("min_vol_weekday")
            min_atr = kpi_any("min_vol_atr")

            parts = []
            if g_ps is not None or g_atr is not None:
                base = "Baseline"
                det = []
                if g_ps is not None:
                    det.append(f"successo {pct(g_ps) or num(g_ps)}")
                if g_atr is not None:
                    det.append(f"ATR {num(g_atr)} pt")
                parts.append(base + ": " + ", ".join(det))

            if best_wd is not None and best_p is not None:
                parts.append(f"Miglior weekday (successo): {best_wd} {pct(best_p) or num(best_p)}")

            if worst_wd is not None and worst_p is not None:
                parts.append(f"Peggior weekday (successo): {worst_wd} {pct(worst_p) or num(worst_p)}")

            if max_wd is not None and max_atr is not None:
                parts.append(f"Volatilità max: {max_wd} ATR {num(max_atr)} pt")

            if min_wd is not None and min_atr is not None:
                parts.append(f"Volatilità min: {min_wd} ATR {num(min_atr)} pt")

            if parts:
                s = " | ".join(parts)
                if n:
                    s += f" (n={n})"
                if warnings:
                    s += " Nota: " + "; ".join(warnings)
                return s

        if kind == "lv04_first_close_bucket_prev_day_h60":
            chosen = kpi_any("chosen_share")
            top = kpi_any("top_share")
            tot = kpi_any("total_n") or n

            if chosen is not None and top is not None:
                s = (
                    f"Distribuzione del primo close nel bucket scelto: {pct(chosen) or num(chosen)}."
                    f" Bucket dominante: {pct(top) or num(top)}."
                )
                if tot is not None:
                    try:
                        s += f" (n={int(tot)})"
                    except Exception:
                        s += f" (n={tot})"
                if warnings:
                    s += " Nota: " + "; ".join(warnings)
                return s
            
        if kind == "success_by_weekday_session":
            wd = kpi_any("weekday")
            sess = kpi_any("session")
            p = kpi_any("p_success") or kpi_any("p_success_1ATR")
            n0 = n

            if wd is not None or sess is not None:
                s = "Successo (1ATR)"
                scope = []
                if wd is not None:
                    scope.append(str(wd))
                if sess is not None:
                    scope.append(str(sess))
                if scope:
                    s += " per " + " / ".join(scope)
                if p is not None:
                    s += f": {pct(p) or num(p)}"
                if n0:
                    s += f" (n={n0})"
                if warnings:
                    s += " Nota: " + "; ".join(warnings)
                return s
    

        # fallback: keep technical text, append prudence if needed
        if warnings:
            return (text + "  Nota: " + "; ".join(warnings)).strip()
        return text.strip()

    except Exception:
        return (out.get("text") or "").strip()

def _render_calendar(report: Dict[str, Any]) -> Dict[str, Any]:
    rep = report.get("report", {}) if isinstance(report, dict) else {}
    title = rep.get("title") or "Calendar"
    data = report.get("data") or []
    warnings = report.get("warnings") or []

    # Se non ci sono righe -> mostra titolo + warning (no fallback brutto)
    if not data:
        return {
            "text": f"{title}",
            "kpis": [],
            "warnings": warnings,
            "confidence": "low",
            "n": 0,
        }

    row = data[0]
    n = int(row.get("n", 0) or 0)

    # Trova il "valore" (metrica) in modo generico
    metric = rep.get("metric")
    value = row.get(metric) if metric else None

    # format value: percentuale se metrica è p_success...
    if isinstance(value, (int, float)) and metric and metric.startswith("p_"):
        val_str = f"{value*100:.2f}%"
    elif isinstance(value, (int, float)):
        val_str = f"{value:.2f}"
    else:
        val_str = str(value) if value is not None else "NA"

    text = f"{val_str} (n={n}) — {title}"

    kpis = []
    if metric and value is not None:
        kpis.append({"name": metric, "value": value, "n": n})
    kpis.append({"name": "n", "value": n, "n": n})

    return {
        "text": text,
        "kpis": kpis,
        "warnings": warnings,
        "confidence": _confidence_from_n(n),
        "n": n,
    }

