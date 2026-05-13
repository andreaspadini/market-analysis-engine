# nl_layer/run_nl_query.py
import json
import sys
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from .nl_parse import parse_query

PYTHON_EXE = sys.executable

# Ensure project root is on sys.path when executed as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def _run(cmd: list, *, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def _find_report_json(out_root: Path) -> Path:
    reports = list(out_root.rglob("report.json"))
    if not reports:
        raise FileNotFoundError(f"report.json non trovato sotto {out_root}")
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0]

def _normalize_ui_payload(ui: dict, report_json: dict) -> dict:
    """
    Rende l'oggetto ui coerente anche quando render_report ritorna un placeholder.

    Caso tipico: ui.text = "Report 'None' disponibile." ma report_json contiene:
      report_json["ui"]["text"] oppure report_json["report"]["ui"]["text"]
      report_json["data"] con n e metriche.

    Strategia:
    - se ui sembra placeholder -> usa report_json.report.ui.text / report_json.ui.text
    - se mancano kpis e ci sono data+metric -> costruisce kpis minime
    - setta kind se possibile
    """
    ui = ui or {}
    report_json = report_json or {}

    # --- helper: report object (calendar nested vs flat) ---
    rep_obj = report_json.get("report") if isinstance(report_json, dict) else None
    if isinstance(rep_obj, dict):
        rep_kind = rep_obj.get("kind")
        rep_title = rep_obj.get("title")
        rep_metric = rep_obj.get("metric")
        rep_kpis = rep_obj.get("kpis") or []
        rep_mode = rep_obj.get("mode")
        rep_ui_text = (report_json.get("ui") or {}).get("text") or (rep_obj.get("ui") or {}).get("text")
        rep_nl_text = report_json.get("nl_text") or rep_obj.get("nl_text")
        rep_data = report_json.get("data") or rep_obj.get("data") or []
    else:
        rep_kind = report_json.get("kind")
        rep_title = report_json.get("title")
        rep_metric = report_json.get("metric")
        rep_kpis = report_json.get("kpis") or []
        rep_mode = report_json.get("tags", {}).get("mode") or report_json.get("mode")
        rep_ui_text = (report_json.get("ui") or {}).get("text")
        rep_nl_text = report_json.get("nl_text")
        rep_data = report_json.get("data") or []

    # --- detect placeholder UI ---
    txt = (ui.get("text") or "").strip()
    nl_txt = (ui.get("nl_text") or "").strip()
    is_placeholder_text = ("Report 'None' disponibile" in txt) or ("Report 'None' disponibile" in nl_txt)
    is_empty = (not txt) and (not nl_txt)
    is_empty_kpis = not ui.get("kpis")
    is_placeholder = is_placeholder_text or is_empty or (is_empty_kpis and ui.get("n", 0) == 0)

    out = dict(ui)

    # --- Fix text/nl_text ---
    if is_placeholder:
        better_text = rep_ui_text or rep_nl_text or rep_title
        if better_text:
            out["text"] = better_text
        if rep_nl_text:
            out["nl_text"] = rep_nl_text
        elif out.get("nl_text") in (None, "", "Report 'None' disponibile."):
            # fallback: usa text anche come nl_text
            out["nl_text"] = out.get("text")

    # --- Fix kind ---
    if not out.get("kind"):
        out["kind"] = rep_kind or "calendar"
    # (nel tuo caso kind="calendar" giÃ  c'Ã¨, ok)

    # --- Build minimal KPIs if missing but we have data ---
    # esempio: data[0] = {"hour":15, "n":3, "avg_atr_before_pts": 28.41}
    if (not out.get("kpis")) and rep_data and isinstance(rep_data, list) and isinstance(rep_data[0], dict):
        row0 = rep_data[0]
        # prova a usare metric + n
        metric_name = rep_metric if isinstance(rep_metric, str) else None
        n = row0.get("n") if isinstance(row0.get("n"), (int, float)) else None

        kpis = []
        if metric_name and metric_name in row0:
            kpis.append({"name": metric_name, "value": row0.get(metric_name), "n": n or 0})
        if n is not None:
            kpis.append({"name": "n", "value": n, "n": int(n)})

        if kpis:
            out["kpis"] = kpis
            out["n"] = int(n) if n is not None else out.get("n", 0)

    # --- ensure defaults ---
    out.setdefault("warnings", [])
    out.setdefault("confidence", out.get("confidence") or "low")

    return out



def run_nl_query(
    text: str,
    *,
    out_root_base: str = "out_nl",
    registry: str = "nl_layer/registry/intents.json",
    frozen_root: Optional[str] = None,
    cache_dir: Optional[str] = None,
    render: bool = True,
) -> Dict[str, Any]:
    parsed = parse_query(text)
    if parsed is None:
        parsed = {
            "ok": False,
            "error": {"code": "INTERNAL_ERROR", "message": "parse_query returned None"},
            "debug": {"nl_text": text},
        }

    if not parsed.get("ok"):
        return {"ok": False, "parse": parsed}

    if parsed.get("type") != "intent":
        return {
            "ok": False,
            "parse": parsed,
            "error": {"code": "NOT_IMPLEMENTED", "message": "v1 supporta solo intent (compose non ancora cablate)."},
        }

    intent_id = parsed["intent_id"]
    params = parsed.get("params", {})

    # 1) prepara out-root unico
    run_id = uuid.uuid4().hex[:10]
    out_root = Path(out_root_base) / f"nl_{intent_id}_{run_id}"
    out_root.mkdir(parents=True, exist_ok=True)

    # 2) scrivi params.json
    params_path = out_root / "params.json"
    params_path.write_text(json.dumps(params, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3) run_intent.py
    cmd = [
        PYTHON_EXE,
        "nl_layer/run_intent.py",
        "--intent",
        intent_id,
        "--registry",
        registry,
        "--out-root",
        str(out_root),
        "--params",
        str(params_path),
    ]
    if frozen_root:
        cmd += ["--frozen-root", frozen_root]
    if cache_dir:
        cmd += ["--cache-dir", cache_dir]

    proc = _run(cmd)

    if proc.returncode != 0:
        return {
            "ok": False,
            "parse": parsed,
            "error": {
                "code": "ENGINE_ERROR",
                "message": "run_intent.py ha fallito",
                "stderr": proc.stderr.strip(),
                "stdout": proc.stdout.strip(),
                "cmd": cmd,
            },
        }

    # 4) trova report.json
    try:
        report_path = _find_report_json(out_root)
    except Exception as e:
        return {
            "ok": False,
            "parse": parsed,
            "error": {
                "code": "REPORT_NOT_FOUND",
                "message": str(e),
                "out_root": str(out_root),
                "stdout": proc.stdout.strip(),
            },
        }

    # 5) carica report.json per la GUI
    report_json = None
    try:
        report_json = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "ok": False,
            "parse": parsed,
            "error": {
                "code": "REPORT_NOT_JSON",
                "message": f"report.json non parsabile: {e}",
                "report_path": str(report_path),
            },
            "engine_stdout": proc.stdout.strip(),
        }
    from .nl_render import render_report
    ui_raw = render_report(report_json)
    pretty_text = ui_raw.get("text") if isinstance(ui_raw, dict) else None

    ui = _normalize_ui_payload(ui_raw, report_json)

    rep = report_json.get("report", {}) if isinstance(report_json, dict) else {}
    kind = rep.get("kind") or report_json.get("kind")

    if kind == "calendar" and pretty_text:
        ui["text"] = pretty_text
        ui["nl_text"] = pretty_text



    # 6) rendered_text: per v1 usiamo lo stdout giÃ  â€œumanoâ€
    rendered_text = _extract_human_summary(proc.stdout)

    return {
        "ok": True,
        "parse": parsed,
        "ui": ui,
        "report": report_json,
        "debug": {
            "out_root": str(out_root),
            "report_path": str(report_path),
            "stdout": proc.stdout.strip()
        }
        }

def _extract_human_summary(stdout: str) -> str:
    """
    Estrae la parte 'umana' giÃ  stampata dagli script intent.
    Heuristica semplice: prende le righe tra una riga di trattini e la prima riga vuota lunga,
    altrimenti ritorna tutto stdout pulito.
    """
    s = (stdout or "").strip()
    if not s:
        return ""

    lines = s.splitlines()

    # Caso comune: blocco con "------"
    dash_idx = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("------"):
            dash_idx = i
            break

    if dash_idx is not None:
        # prendi alcune righe dopo i trattini (max 30)
        snippet = lines[dash_idx : min(dash_idx + 35, len(lines))]
        return "\n".join(snippet).strip()

    return s


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        print("Usage: python nl_layer/run_nl_query.py \"...query...\"")
        raise SystemExit(1)

    out = run_nl_query(text, render=True)
    print(json.dumps(out, indent=2, ensure_ascii=False))
