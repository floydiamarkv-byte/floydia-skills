#!/usr/bin/env python3
"""Banco PUBLICABLE §6: congelado, ciego, aleatorizado, con VCR y McNemar.

Diferencias con `bench_v51.py` (regresión interna):
  1. fixtures congelados en `qa/fixtures/harness_v5/` + manifiesto de hashes
  2. mocks de herramientas servidos desde `mcp_vcr.json` (mismos bytes en GO y FREE)
  3. orden aleatorizado con semilla fija y registrado
  4. frío/caliente medidos por separado (primera llamada de cada modelo = frío)
  5. evaluación CIEGA: el evaluador ve `(anon_id, tarea, texto)`, nunca el modo
  6. rúbrica escrita ANTES de correr (`rubric.json`), graders deterministas
  7. McNemar exacto para comparación pareada GO vs FREE

Uso:
    python3 bench_publicable.py --run          # 8 tareas x 2 modos x 3 reps
    python3 bench_publicable.py --evaluate     # ciego + McNemar + informe
"""
from __future__ import annotations

import argparse
import os
import hashlib
import json
import random
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bench_v51 as B  # noqa: E402

QA = Path(os.environ.get("QA_DIR", str(HERE / "qa/fixtures/harness_v5")))
TAG = os.environ.get("BENCH_TAG", "")
# Presupuesto de salida por tarea (el techo REAL de la tarea, no el del bench antiguo)
MAXTOK = {"T1_hero": 12000, "T2_cls": 8000, "T3_schema": 8000, "T4_onpage": 6000,
          "T5_brief": 4000, "T6_css": 8000, "T7_vision": 2000, "T8_tools": 3000}
OUT = HERE / "out"
REPS = 3
SEED = 42
VCR = QA / "mcp_vcr.json"
RUBRIC = QA / "rubric.json"
MANIFEST = QA / "manifest.json"

# Modelos pinneados por fecha (2026-11-07) según el routing vigente
ARMS = {
    "GO": {"text": "deepseek-v4.1-flash", "vision": "gemini-4-argon"},
    "FREE": {"text": "deepseek-ai/deepseek-v4.1-flash", "vision": "google/diffusiongemma-26b-a4b-it"},
}


def freeze() -> None:
    """Congela fixtures + mocks y escribe la rúbrica ANTES de medir."""
    QA.mkdir(parents=True, exist_ok=True)
    B.build_fixtures()                      # deja los fixtures en B.FIX
    for p in sorted(B.FIX.iterdir()):
        if p.is_file():
            (QA / p.name).write_bytes(p.read_bytes())
    vcr = {"recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "tools": {"get_page_metrics": {k: {"lcp_ms": v} for k, v in B.PAGE_METRICS.items()}},
           "note": "respuestas grabadas; GO y FREE reciben exactamente estos bytes"}
    VCR.write_text(json.dumps(vcr, indent=1, ensure_ascii=False), encoding="utf-8")
    rubric = {"defined_before_running": True, "reps": REPS, "seed": SEED,
              "max_tokens_policy": MAXTOK,
              "tasks": {t["id"]: {"max_tokens": MAXTOK.get(t["id"], t["max_tokens"]), "criterio": t["id"],
                                  "grader": "determinista (bench_v51.g_*)"} for t in B.TASKS},
              "orden": "aleatorizado con random.Random(seed).shuffle"}
    RUBRIC.write_text(json.dumps(rubric, indent=1, ensure_ascii=False), encoding="utf-8")
    man = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(QA.glob("*")) if p.is_file()}
    MANIFEST.write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"congelado: {len(man)} ficheros en {QA}")


def _verify_frozen() -> None:
    man = json.loads(MANIFEST.read_text())
    for name, h in man.items():
        p = QA / name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()[:16] != h:
            raise SystemExit(f"fixture alterado: {name} (el banco deja de ser comparable)")
    print(f"manifiesto OK: {len(man)} ficheros idénticos")


def run() -> None:
    _verify_frozen()
    vcr = json.loads(VCR.read_text())
    B.PAGE_METRICS = {k: v["lcp_ms"] for k, v in vcr["tools"]["get_page_metrics"].items()}
    only = [m for m in ("GO", "FREE") if f"--only {m}" in " ".join(sys.argv)]
    arms = tuple(only) if only else ("GO", "FREE")
    pairs = [(t["id"], m) for t in B.TASKS for m in arms]
    random.Random(SEED).shuffle(pairs)
    (QA / "order.json").write_text(json.dumps(pairs, indent=1), encoding="utf-8")
    by_id = {t["id"]: t for t in B.TASKS}
    seen = set()
    n = 0
    t0 = time.time()
    keep = []
    if only and (OUT / f"publicable_raw{TAG}.jsonl").exists():
        keep = [json.loads(l) for l in (OUT / f"publicable_raw{TAG}.jsonl").read_text(encoding="utf-8").splitlines()
                if l.strip() and json.loads(l)["mode"] not in arms]
    with (OUT / f"publicable_raw{TAG}.jsonl").open("w", encoding="utf-8") as raw:
        for k in keep:
            raw.write(json.dumps(k, ensure_ascii=False) + "\n")
        for tid, mode in pairs:
            base = by_id[tid]
            model = ARMS[mode]["vision" if base.get("vision") else "text"]
            for rep in range(1, REPS + 1):
                cold = (mode, model) not in seen
                seen.add((mode, model))
                task = dict(base)
                task["max_tokens"] = MAXTOK.get(tid, base["max_tokens"])
                task["model"] = {**base["model"], mode: model}
                n += 1
                rec = B.run_task(mode, task, rep, cold)
                if (rec.get("error") or "").lower().find("circuit breaker") >= 0:
                    time.sleep(25)          # el breaker se rearma solo: una espera y un reintento
                    rec = B.run_task(mode, task, rep, cold)
                    rec["retried_breaker"] = True
                rec["anon"] = hashlib.sha256(f"{tid}{mode}{rep}{SEED}".encode()).hexdigest()[:12]
                rec["phase"] = "cold" if cold else "warm"
                rec["text"] = rec.get("text_full") or rec.get("text") or rec.get("final_text") or ""
                raw.write(json.dumps(rec, ensure_ascii=False) + "\n")
                raw.flush()
                print(f"[{n:>2}] {tid:<10} {mode:<4} rep{rep} {'cold' if cold else 'warm'} "
                      f"{rec.get('ms')} ms · {'PASS' if (rec.get('grade') or {}).get('pass') else 'fail'}", flush=True)
    print(f"crudo: {n} llamadas en {int(time.time()-t0)} s")


def evaluate() -> None:
    rows = [json.loads(l) for l in (OUT / f"publicable_raw{TAG}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    by_id = {t["id"]: t for t in B.TASKS}
    # 1) desidentificar: el evaluador solo ve (anon, tarea, texto)
    blind = [{"anon": r["anon"], "task": r["task"], "text": r.get("text") or r.get("final_text") or "",
              "tool_calls": r.get("tool_calls") or []} for r in rows]
    (OUT / f"publicable_blind{TAG}.jsonl").write_text(
        "\n".join(json.dumps(b, ensure_ascii=False) for b in blind), encoding="utf-8")

    # 2) evaluar a ciegas con la rúbrica determinista
    verdicts = {}
    for b in blind:
        try:
            if b["task"] == "T8_tools":
                g = B.g_tools({"tool_calls": b.get("tool_calls") or [], "final_text": b["text"]})
            else:
                g = by_id[b["task"]]["grader"]({"text": b["text"]})
            verdicts[b["anon"]] = {"pass": bool(g.get("pass")), "score": g.get("score"), "detail": g.get("detail")}
        except Exception as e:  # noqa: BLE001
            verdicts[b["anon"]] = {"pass": False, "error": f"{type(e).__name__}: {e}"}

    # 3) desvelar y agregar
    tasks = sorted({r["task"] for r in rows})
    modes = ("GO", "FREE")
    table = {}
    for m in modes:
        for t in tasks:
            reps = [r for r in rows if r["mode"] == m and r["task"] == t]
            ps = [verdicts[r["anon"]]["pass"] for r in reps]
            table.setdefault(m, {})[t] = {
                "pass_any": any(ps), "pass_all": all(ps), "reps": len(ps),
                "pass_rate": round(sum(ps) / len(ps), 2) if ps else 0.0,
                "ms_p50": (int(statistics.median([r["ms"] for r in reps if r.get("ms") is not None]))
                           if any(r.get("ms") is not None for r in reps) else None),
                "cost_usd": round(sum(float((r.get("usage") or {}).get("allowance") or 0) for r in reps), 6),
                "phases": sorted({r["phase"] for r in reps}),
            }

    # 4) McNemar exacto sobre pares (tarea): pass_all
    b = sum(1 for t in tasks if table["GO"][t]["pass_all"] and not table["FREE"][t]["pass_all"])
    c = sum(1 for t in tasks if table["FREE"][t]["pass_all"] and not table["GO"][t]["pass_all"])
    n = b + c
    if n == 0:
        p = 1.0
    else:
        from math import comb
        p = min(1.0, 2 * sum(comb(n, k) for k in range(0, min(b, c) + 1)) / (2 ** n))

    res = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "blind": True, "seed": SEED, "reps": REPS,
           "table": table,
           "mcnemar": {"b_go_only": b, "c_free_only": c, "p_exact": round(p, 4),
                       "n_pares": len(tasks),
                       "nota": "n=8 es regresión, no ranking; p<0,05 solo con discordancia suficiente"},
           "totals": {m: {"tareas_pass_all": sum(table[m][t]["pass_all"] for t in tasks),
                          "cost_usd": round(sum(table[m][t]["cost_usd"] for t in tasks), 6)} for m in modes}}
    (OUT / f"publicable_eval{TAG}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")

    md = ["# Banco publicable §6 — resultado", "",
          f"Semilla {SEED} · {REPS} reps · evaluación ciega · rúbrica congelada antes de correr", "",
          "| Tarea | GO | FREE | GO pass_all | FREE pass_all |", "|---|---|---|---|---|"]
    for t in tasks:
        g, f = table["GO"][t], table["FREE"][t]
        md.append(f"| {t} | {g['pass_rate']:.0%} ({g['ms_p50']} ms) | {f['pass_rate']:.0%} ({f['ms_p50']} ms) | "
                  f"{'✔' if g['pass_all'] else '✘'} | {'✔' if f['pass_all'] else '✘'} |")
    md += ["", f"McNemar: b(GO solo)={b} · c(FREE solo)={c} · p={p:.4f} sobre {len(tasks)} pares",
           f"Coste GO: {res['totals']['GO']['cost_usd']} $ · FREE: {res['totals']['FREE']['cost_usd']} $"]
    (OUT / f"publicable_report{TAG}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(res["totals"], ensure_ascii=False), "· McNemar p =", round(p, 4))
    for t in tasks:
        print(f"  {t:<10} GO {table['GO'][t]['pass_rate']:.0%} · FREE {table['FREE'][t]['pass_rate']:.0%}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--evaluate", action="store_true")
    ap.add_argument("--only", choices=["GO", "FREE"])
    a = ap.parse_args()
    if a.freeze:
        freeze()
    if a.run:
        run()
    if a.evaluate:
        evaluate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
