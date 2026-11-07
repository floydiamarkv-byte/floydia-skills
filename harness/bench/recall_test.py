#!/usr/bin/env python3
"""Recall@1 sin modelo grande: recuperación L3 (rg/grep acotado) + respuesta por modelo barato.

10 preguntas cuyas respuestas viven en disco. Se mide si el recuperador encuentra el
fichero correcto (Recall@1 de la fuente) y si el modelo barato responde el dato exacto.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
PROJ = Path("<PROYECTO>")
sys.path.insert(0, str(PROJ / "SCRIPTS"))
sys.path.insert(0, str(ROOT))
from env_loader import load_env  # noqa: E402
from bench_v51 import call, text_of  # noqa: E402

ENV = load_env()
CORPUS = [PROJ / "memory-bank", PROJ / "SCRIPTS", PROJ / ".agents/skills", PROJ / "providers"]

# (pregunta, patrón de búsqueda, respuesta exacta esperada, fichero que la contiene)
CASES = [
    ("¿Qué IP tiene HP45?", "192.168.1.10", "192.168.1.10", "extra"),
    ("¿Cuántas cuentas NIM usa el proxy?", "rpm_per_account", "4", "health"),
    ("¿Cuál es el factor de allowance de deepseek-v4.1-flash?", "deepseek-v4.1-flash.*factor|factor.*deepseek-v4.1-flash", "0.6", "billing"),
    ("¿Cuántas peticiones por minuto admite cada cuenta NIM?", "rpm_per_account", "33", "health"),
    ("¿Qué timeout de lectura usa el perfil fast del proxy NIM?", "FAST_HINTS|read.*90", "90", "proxy"),
    ("¿Qué modelo usan los slots auxiliares de Hermes?", "glm-5.3-flash", "glm-5.3-flash", "config"),
    ("¿Cuál es la bolsa mensual ponderada de OpenCode Go?", "monthly_weighted_cap_usd", "60", "billing"),
    ("¿Qué porcentaje del mensual representa la ventana semanal?", "semana = 50|weekly_weighted_cap_usd", "50", "billing"),
    ("¿En qué puerto escucha el proxy NIM?", "127.0.0.1:8088|:8088", "8088", "proxy"),
    ("¿Qué código HTTP devuelve kimi-k3 en NIM?", "kimi-k3.*410|410.*kimi-k3", "410", "skill"),
]


def retrieve_semantic(question: str, limit=3):
    """L2/L3 por solapamiento de términos: la consulta manda, no un patrón adivinado."""
    try:
        sys.path.insert(0, str(PROJ / "SCRIPTS"))
        from memory_recall import search
        return [{"file": f, "snippet": p} for f, p, _ in search(question, k=limit)]
    except Exception as e:  # noqa: BLE001
        return [{"file": f"ERROR:{e}", "snippet": ""}]


def retrieve(pattern: str, limit=3):
    """L3: grep acotado, devuelve [(fichero, snippet)] con el contexto del match."""
    hits = []
    for base in CORPUS:
        if not base.exists():
            continue
        try:
            p = subprocess.run(["grep", "-rIl", "-E", "--include=*.md", "--include=*.json",
                                "--include=*.yaml", "--include=*.py", pattern, str(base)],
                               capture_output=True, text=True, timeout=45)
        except subprocess.TimeoutExpired:
            continue
        for f in p.stdout.splitlines()[:limit]:
            try:
                txt = Path(f).read_text(errors="ignore")
            except Exception:  # noqa: BLE001
                continue
            m = re.search(pattern, txt, re.S)
            if not m:
                continue
            s = max(0, m.start() - 200)
            hits.append({"file": f, "snippet": txt[s:m.end() + 200]})
            if len(hits) >= limit:
                return hits
    return hits


def ask(model, source, q, snippet):
    prompt = ("Responde la pregunta usando SOLO este fragmento. Si el dato no está, responde NO_VERIFICADO. "
              "Contesta con el dato exacto y nada más.\n\n"
              f"FRAGMENTO:\n{snippet}\n\nPREGUNTA: {q}")
    # Los razonadores gastan el presupuesto pensando: 120 tokens devuelven content vacío.
    r = call(source, model, [{"role": "user", "content": prompt}], max_tokens=1200, timeout=120)
    txt = (text_of(r) if r["ok"] else "").strip()
    if not txt and r["ok"]:      # segunda oportunidad con presupuesto de razonamiento
        r = call(source, model, [{"role": "user", "content": prompt}], max_tokens=2400, timeout=120)
        txt = (text_of(r) if r["ok"] else "").strip()
    return txt, r["ms"], r.get("error")


def main():
    rows = []
    for q, pat, expect, kind in CASES:
        t0 = time.time()
        hits = retrieve_semantic(q) or retrieve(pat)
        ms_ret = int((time.time() - t0) * 1000)
        ctx = "\n---\n".join(h["snippet"] for h in hits)[:2500]
        row = {"q": q, "pattern": pat, "expect": expect, "kind": kind,
               "hits": [h["file"].replace(str(PROJ) + "/", "") for h in hits],
               "retrieval_ms": ms_ret}
        for mode, model in (("FREE", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"),
                            ("GO", "deepseek-v4.1-flash")):
            ans, ms, err = ask(model, mode, q, ctx) if ctx else ("", 0, "sin_contexto")
            row[f"{mode}_answer"] = ans[:120]
            row[f"{mode}_correct"] = expect.lower() in ans.lower()
            row[f"{mode}_ms"] = ms
            row[f"{mode}_error"] = err
        rows.append(row)
        print(f"{'FREE' if row['FREE_correct'] else 'free:'}{int(row['FREE_correct'])} "
              f"{'GO' if row['GO_correct'] else 'go:'}{int(row['GO_correct'])}  {q}", flush=True)
    n = len(rows)
    summary = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "n": n,
               "retrieval_hit_rate": round(sum(1 for r in rows if r["hits"]) / n, 3),
               "free_recall_at_1": round(sum(r["FREE_correct"] for r in rows) / n, 3),
               "go_recall_at_1": round(sum(r["GO_correct"] for r in rows) / n, 3),
               "rows": rows}
    (OUT / "recall_test.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()
