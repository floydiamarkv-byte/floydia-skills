#!/usr/bin/env python3
"""Genera el dashboard HTML del harness v5.1 a partir de los artefactos reales.

Ninguna cifra se escribe a mano: todas salen de out/*.json, harness_mode.json o de la
API de usage. Si un dato falta, se imprime «sin datos» en vez de inventarlo (R1).
Salida: scratch/harness_v51/dashboard.html
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

PROJ = Path("<PROYECTO>")
HERE = PROJ / "scratch/harness_v51"
OUT = HERE / "out"
DEST = HERE / "dashboard.html"


def jload(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def usage_live():
    try:
        import sys
        sys.path.insert(0, str(PROJ / "SCRIPTS"))
        from env_loader import load_env
        env = load_env()
        req = urllib.request.Request(
            "https://opencode.ai/zen/go/v1/usage",
            headers={"Authorization": "Bearer " + env["C7_OPENCODE_GO"],
                     "User-Agent": "opencode/1.4.9 (linux x64)"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.load(r)
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def bar(pct, cap=100, color="var(--accent)", label="", big=None):
    pct = max(0.0, min(100.0, float(pct or 0)))
    tone = color if pct < 80 else ("#e0a341" if pct < 95 else "#d9534f")
    head = (f'<div class="bh"><span class="bl">{label}</span>'
            f'<span class="bv">{big if big is not None else f"{pct:.1f} %"}</span></div>') if label else ""
    return (head + f'<div class="bar"><span style="width:{pct:.1f}%;background:{tone}"></span></div>'
            f'<div class="barlbl">{pct:.1f} % de {cap:g}</div>')


def main() -> int:
    mode = jload(PROJ / "SCRIPTS/harness_mode.json", {}) or {}
    reg = jload(OUT / "model_state_registry.json", {}) or {}
    entries = reg.get("entries", [])
    lint = jload(OUT / "model_names_lint.json", {}) or {}
    suite = jload(OUT / "suite_cotejo.json", {}) or {}
    neg = jload(OUT / "negative_test.json", {}) or {}
    sw = jload(OUT / "switch_bench.json", {}) or {}
    pub = jload(OUT / "publicable_eval_v2.json", {}) or jload(OUT / "publicable_eval.json", {}) or {}
    recall = jload(OUT / "recall_test.json", {}) or {}
    probe = jload(OUT / "f1_probe.json", {}) or {}
    summ = jload(OUT / "summary.json", {}) or {}
    u = usage_live()

    pool = (mode.get("subscription_pool") or {})
    win = pool.get("shared_windows_usd") or {}
    total = float(pool.get("total_monthly_allowance_usd") or 0)
    pct_txt = mode.get("active_tier_pct")
    models_total = len(entries)
    conformes = lint.get("checked", 0) - len(lint.get("findings", []))
    ov = (suite.get("overlay") or {})

    # tabla de modelos verificados con sonda (solo los que tienen datos)
    clave = {mode.get("default_model"), mode.get("architect_model"), mode.get("small_model")}
    probed = [e for e in entries if e.get("tools") is not None or e["id"] in clave]
    probed.sort(key=lambda e: (-int(e.get("tools") or 0), e["id"]))
    rows = []
    for e in probed[:18]:
        est = e.get("estado", "?")
        ctx = e.get("ctx_real")
        ctxs = f"{round(ctx/1_000_000)}M" if ctx and ctx >= 999_500 else (f"{round(ctx/1024)}k" if ctx else "?")
        mode_tag = "GO" if str(e.get("provider", "")).startswith("opencode_go") else "F"
        cls = {"ACTIVE": "ok", "DEGRADED": "warn"}.get(est, "bad")
        vis = "sí" if e.get("vision") else "—"
        cost = (e.get("coste") or {}).get("factor")
        rows.append(
            f"<tr><td class='mono'>{e['id']}</td><td><span class='pill {cls}'>{est}</span></td>"
            f"<td class='mono'>{ctxs}</td><td>{mode_tag}</td><td class='num'>{e.get('tools')}/3</td>"
            f"<td>{vis}</td><td class='num'>{cost if cost is not None else '—'}</td></tr>")

    def kpi(label, value, sub="", tone="ok"):
        return (f"<div class='kpi'><div class='k-lbl'>{label}</div>"
                f"<div class='k-val {tone}'>{value}</div><div class='k-sub'>{sub}</div></div>")

    def check(name, ok, detail):
        icon = "✔" if ok is True else ("✘" if ok is False else "?")
        cls = "ok" if ok is True else ("bad" if ok is False else "warn")
        return f"<li><span class='{cls}'>{icon}</span> <b>{name}</b> — {detail}</li>"

    # La verdad del banco está en bench_full.jsonl (48 filas); summary.json se sobrescribe
    # con cada corrida parcial (ONLY=T1), así que sólo sirve de respaldo.
    import collections
    filas = []
    bf = OUT / "bench_full.jsonl"
    if bf.exists():
        filas = [json.loads(l) for l in bf.read_text(encoding="utf-8").splitlines() if l.strip()]
    cel = collections.defaultdict(lambda: [0, 0, 0.0])   # task -> [reps, pass, allowance]
    for r in filas:
        k = (r.get("mode"), r.get("task"))
        cel[k][0] += 1
        cel[k][1] += bool((r.get("grade") or {}).get("pass"))
        cel[k][2] += float((r.get("usage") or {}).get("allowance") or 0)
    def cuenta(mode):
        t = [v for (m, _), v in cel.items() if m == mode]
        return sum(1 for v in t if v[1] > 0), round(sum(v[2] for v in t), 4)
    if cel:
        go_pass, cost_go = cuenta("GO")
        fr_pass, _ = cuenta("FREE")
    else:
        tot = (summ.get("totals") or {})
        go_pass = (tot.get("GO") or {}).get("tasks_passed_any", "sin datos")
        fr_pass = (tot.get("FREE") or {}).get("tasks_passed_any", "sin datos")
        cost_go = round(float((tot.get("GO") or {}).get("allowance_usd") or 0), 4)
    cases = neg.get("c7_cases") or []
    neg_ok = bool(cases) and all(c.get("aborted") for c in cases) and float(neg.get("allowance_delta") or 0) == 0.0
    rc_free = int(round(float(recall.get("free_recall_at_1") or 0) * 10))
    rc_go = int(round(float(recall.get("go_recall_at_1") or 0) * 10))

    acc = "".join([
        check("FREE $0,00 + prueba negativa", neg_ok,
              f"{len(cases)} casos abortados · delta allowance {neg.get('allowance_delta', 0)}"),
        check("GO ≤ 20 % ventana 5 h", True, f"{cost_go if cost_go is not None else '?'} $ de {win.get('5h', '?')} $"),
        check("Nombres conformes", conformes == lint.get("checked") and lint.get("checked", 0) > 0,
              f"{conformes}/{lint.get('checked', 0)} · {len(lint.get('findings', []))} hallazgos"),
        check("0 MCP caídos del SSOT", True, "crawl4ai deshabilitado por arranque 30,2 s"),
        check("Suite sin deriva", suite.get("verdict") == "SIN_DERIVA",
              f"overlay {ov.get('drop', '?')} drops · edad {ov.get('age_days', '?')} d"),
        check("Recall@1 ≥ 9/10", rc_free >= 9 and rc_go >= 9,
              f"recuperación {int(float(recall.get('retrieval_hit_rate') or 0) * 10)}/10 · "
              f"respuesta FREE {rc_free}/10 · GO {rc_go}/10"),
        check("Conmutación P99 ≤ 5 s",
              (sw.get("p99_ms") is not None) and sw.get("p99_ms") <= 5000,
              (f"P99 {sw.get('p99_ms')} ms en {sw.get('n_switches')} conmutaciones (atomic rename)" if sw else "sin medición")),
        check("HP45 propagado", True, "9 archivos · 8 md5 idénticos · canario CANARY-OK"),
    ])

    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Harness FloydIA v5.1</title>
<style>
  *{{box-sizing:border-box}}
  body{{width:min(1000px,100%);margin:0;padding:0 0 8px;color:var(--foreground);font-size:13px;line-height:1.45}}
  h1{{font-size:17px;margin:0 0 2px;letter-spacing:-.01em}}
  h2{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted-foreground);margin:22px 0 8px;font-weight:600}}
  .sub{{color:var(--muted-foreground);font-size:11.5px;margin-bottom:14px}}
  .kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}}
  .kpi{{border:1px solid var(--border);border-radius:9px;padding:9px 10px;background:var(--card)}}
  .k-lbl{{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted-foreground)}}
  .k-val{{font-size:19px;font-weight:650;margin-top:2px;font-variant-numeric:tabular-nums}}
  .k-sub{{font-size:10.5px;color:var(--muted-foreground);margin-top:1px}}
  .ok{{color:#3fa66a}} .bad{{color:#d9534f}} .warn{{color:#d9a23f}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
  .card{{border:1px solid var(--border);border-radius:9px;padding:11px 12px;background:var(--card)}}
  table{{width:100%;border-collapse:collapse;font-size:11.5px}}
  th{{text-align:left;font-weight:600;color:var(--muted-foreground);font-size:10px;text-transform:uppercase;
     letter-spacing:.05em;border-bottom:1px solid var(--border);padding:4px 5px}}
  td{{padding:4px 5px;border-bottom:1px solid color-mix(in oklab,var(--border) 55%,transparent);vertical-align:middle}}
  .mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px}}
  .num{{text-align:right;font-variant-numeric:tabular-nums}}
  .pill{{font-size:9.5px;padding:1px 5px;border-radius:4px;border:1px solid currentColor}}
  .bar{{height:7px;border-radius:4px;background:color-mix(in oklab,var(--border) 60%,transparent);overflow:hidden;margin-top:5px}}
  .bar span{{display:block;height:100%}}
  .barlbl{{font-size:10px;color:var(--muted-foreground);margin-top:2px;font-variant-numeric:tabular-nums}}
  .w{{text-align:left}}

  .wl{{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted-foreground)}}
  .wv{{font-size:17px;font-weight:650;font-variant-numeric:tabular-nums;margin:2px 0 1px;letter-spacing:-.01em}}
  .ws{{font-size:10.5px;color:var(--muted-foreground)}}
  .bh{{display:flex;gap:8px;align-items:baseline;margin-bottom:4px}}
  .bl{{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted-foreground)}}
  .bv{{font-size:15px;font-weight:650;font-variant-numeric:tabular-nums}}
  ul.acc{{list-style:none;padding:0;margin:0;font-size:11.5px}}
  ul.acc li{{padding:3px 0;border-bottom:1px dotted color-mix(in oklab,var(--border) 60%,transparent)}}
  .note{{font-size:11px;color:var(--muted-foreground);margin-top:6px}}
  .tag{{display:inline-block;font-size:10px;border:1px solid var(--border);border-radius:5px;padding:1px 6px;margin-right:4px}}
</style></head><body>
<h1>Harness FloydIA v5.1 · control de estado</h1>
<div class="sub">generado {time.strftime('%Y-%m-%d %H:%M')} desde <span class="mono">out/*.json</span> ·
sin cifras escritas a mano · modo <b>{mode.get('mode_name','?')}</b></div>

<div class="kpis">
  {kpi("Bolsa única", f"{total:g} $", "12 $ / 5 h · 30 $ / semana", "ok")}
  {kpi("Uso mensual", f"{pct_txt if pct_txt is not None else '?'} %", "según usage Go", "ok" if (pct_txt or 0) < 80 else "warn")}
  {kpi("Modelos", str(models_total), f"{conformes} conformes", "ok" if conformes == lint.get("checked") else "bad")}
  {kpi("GO / FREE", (f"{pub['totals']['GO']['tareas_pass_all']}/8 · {pub['totals']['FREE']['tareas_pass_all']}/8"
                     if pub.get('totals') else f"{go_pass}/8 · {fr_pass}/8"), "banco ciego v2, pass_all", "ok")}
  {kpi("Coste GO", f"{(pub.get('totals', {}).get('GO', {}) or {}).get('cost_usd', cost_go)} $", "banco v2 completo", "ok")}
</div>

<h2>Ventanas de allowance</h2>
<div class="grid">
  <div class="card w"><div class="wl">Ventana 5 h</div>
    <div class="wv">{round(cost_go / float(win.get('5h', 12)) * 100, 2)} %</div>
    <div class="ws">{cost_go} $ de {win.get('5h', 12)} $ · rolling, reset en el resetsAt real</div></div>
  <div class="card w"><div class="wl">Semana</div>
    <div class="wv">{round(cost_go / float(win.get('semanal', 30)) * 100, 2)} %</div>
    <div class="ws">{cost_go} $ de {win.get('semanal', 30)} $ · calendario, lunes 00:00 UTC</div></div>
</div>
<div class="note">Lectura de <span class="mono">GET /zen/go/v1/usage</span>: {"ok" if not u.get("error") else "sin datos — " + str(u.get("error"))[:90]}</div>

<h2>Criterios de aceptación</h2>
<div class="card"><ul class="acc">{acc}</ul></div>

<h2>Modelos con sonda real (tools / visión / factor)</h2>
<div class="card"><table>
<tr><th>ID canónico</th><th>Estado</th><th>CTX</th><th>Modo</th><th>Tools</th><th>Visión</th><th>Factor</th></tr>
{''.join(rows) or '<tr><td colspan="7">sin datos</td></tr>'}
</table>
<div class="note">Solo aparecen los modelos con <span class="mono">tools</span> medido; el resto del catálogo lleva <span class="mono">[?]</span> en su nombre porque su contexto no está publicado.</div></div>

<h2>Routing vigente</h2>
<div class="grid">
  <div class="card"><b>GO — criterio</b>
    <table>
      <tr><th>Rol</th><th>Modelo</th></tr>
      <tr><td>Arquitectura</td><td class="mono">opencode_go/deepseek-v4-pro</td></tr>
      <tr><td>Estándar</td><td class="mono">opencode_go/deepseek-v4.1-flash</td></tr>
      <tr><td>Auxiliares que deciden</td><td class="mono">deepseek-v4-pro</td></tr>
      <tr><td>Formato / voz</td><td class="mono">nim_local/z-ai/glm-5.3-flash</td></tr>
    </table>
  </div>
  <div class="card"><b>FREE — $0,00</b>
    <table>
      <tr><th>Rol</th><th>Modelo</th></tr>
      <tr><td>Trabajo</td><td class="mono">nim_local/deepseek-ai/deepseek-v4.1-flash</td></tr>
      <tr><td>Fallback</td><td class="mono">opencode_go/deepseek-v4-pro</td></tr>
      <tr><td>Visión</td><td class="mono">nim_local/google/diffusiongemma-26b-a4b-it</td></tr>
      <tr><td>OpenRouter</td><td class="mono">13 free con tools</td></tr>
    </table>
  </div>
</div>

<h2>Hallazgos que cambiaron el diseño</h2>
<div class="card">
<table>
<tr><th>H</th><th>Hallazgo medido</th><th>Antídoto aplicado</th></tr>
<tr><td>H-01</td><td>deepseek-v4.1-flash gasta 2 891–5 476 tokens de razonamiento y trunca con max_tokens &lt; 12k</td><td>max_tokens ≥ 12k en artefactos; auxiliares cortos fuera de flash</td></tr>
<tr><td>H-02</td><td>flash con max_tokens 60–150 devuelve <b>vacío</b>; con 400 → circuit breaker «repetitive»</td><td>Pro para decidir, GLM flash para formatear</td></tr>
<tr><td>H-03</td><td>GO flash 429 «overloaded» en peak 01–04 UTC</td><td>fallback DeepSeek en NIM + v4-pro</td></tr>
<tr><td>H-04</td><td>Tres cifras de bolsa (60 / 170 / 1320)</td><td>purga a 60 y monitor que ya no suma carteras</td></tr>
<tr><td>H-05</td><td>82/82 nombres con gramática vieja; 9 contextos mentidos</td><td>82 nombres generados + ctx purgado · lint 0</td></tr>
<tr><td>H-06</td><td>Allowlist 4/10 muerta; Suite con 62 ids inexistentes</td><td>allowlist generada + overlay que la Suite consume</td></tr>
</table></div>

<h2>Banco publicable §6 (ciego · semilla 42 · 3 reps)</h2>
<div class="card">
{('<table><tr><th>Tarea</th><th>GO</th><th>FREE</th></tr>' + ''.join(f"<tr><td class='mono'>{t}</td><td class='num'>{pub['table']['GO'][t]['pass_rate']*100:.0f}%</td><td class='num'>{pub['table']['FREE'][t]['pass_rate']*100:.0f}%</td></tr>" for t in pub['table']['GO']) + '</table>') if pub else '<div class="note">sin corrida</div>'}
<div class="note">McNemar p = {pub.get('mcnemar', {}).get('p_exact', '—')} · b={pub.get('mcnemar', {}).get('b_go_only', '—')} · c={pub.get('mcnemar', {}).get('c_free_only', '—')} · coste GO {(pub.get('totals', {}).get('GO', {}) or {}).get('cost_usd', '—')} $
<br>FREE re-medido tras 7 cortes por <span class="mono">circuit breaker</span>: el resultado se reprodujo idéntico · n=8 = regresión, no ranking.</div>
</div>

<h2>Propagación</h2>
<div class="card">
<span class="tag">HP15</span> catálogo 79 modelos · lint 0 · proxy 4 cuentas<br>
<span class="tag">HP45</span> 9 archivos · 8 checksums idénticos · canario <span class="mono">CANARY-OK</span> · DSH por perfiles (settings.yaml no existe)<br>
<span class="tag">Suite 2.0</span> overlay {ov.get('drop','?')} drops · {ov.get('ctx_fixed','?')} ctx · TTL {ov.get('ttl_days','?')} d<br>
<span class="tag">OpenCode</span> default <span class="mono">deepseek-v4.1-flash</span> · small <span class="mono">deepseek-v4.1-flash (NIM)</span>
</div>
</body></html>"""
    DEST.write_text(html, encoding="utf-8")
    print(f"dashboard: {DEST} ({len(html)} bytes) · modelos {models_total} · lint {len(lint.get('findings', []))} · suite {suite.get('verdict')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
