#!/usr/bin/env python3
"""harness_full_audit — una sola llamada: escanear, evaluar, proponer, revisar, propagar.

Ejecuta el pipeline completo reutilizando los scripts ya probados (no reimplementa nada):
  preflight → registro → contexto → nombres/lint → allowlist → Suite → banco ciego →
  recall → conmutador → ENJAMBRE → REVISIÓN EXTERNA → propuesta → dashboard → informe

Uso:
    python3 SCRIPTS/harness_full_audit.py --run                 # ciclo completo (no aplica)
    python3 SCRIPTS/harness_full_audit.py --run --fast          # sin banco ni recall (~2 min)
    python3 SCRIPTS/harness_full_audit.py --run --apply         # escribe SSOT (exige token)
    python3 SCRIPTS/harness_full_audit.py --run --no-external   # sin consulta a IA externa

Salida: scratch/harness_v51/out/full_audit_<ts>.json + FULL_AUDIT.md
Exit: 0 VERDE · 2 hallazgos duros o deriva · 3 abortado por preflight
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PROJ = Path("<PROYECTO>")
SCRIPTS = PROJ / "SCRIPTS"
H51 = PROJ / "scratch/harness_v51"
OUT = H51 / "out"
TS = time.strftime("%Y%m%d-%H%M%S")
sys.path.insert(0, str(SCRIPTS))

LOG = OUT / f"full_audit_{TS}.log"


def sh(cmd: list[str], timeout=300, env=None) -> dict:
    t0 = time.time()
    e = {**os.environ, **(env or {})}
    try:
        p = subprocess.run(cmd, cwd=str(PROJ), capture_output=True, text=True, timeout=timeout, env=e)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = 124, "", f"timeout {timeout}s"
    ms = int((time.time() - t0) * 1000)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"\n$ {' '.join(cmd)}\n[exit {rc} · {ms} ms]\n{out[-4000:]}\n{err[-2000:]}\n")
    return {"cmd": " ".join(cmd), "exit": rc, "ms": ms, "out": out, "err": err}


def jload(p) -> dict:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


# ─── ENJAMBRE ────────────────────────────────────────────────────────────────
def swarm() -> dict:
    """SSOT de MCP vs lo que cada cliente declara vs lo que responde."""
    ssot_p = Path.home() / ".gemini/config/mcp_config.full.json"
    ssot = {}
    if ssot_p.exists():
        raw = jload(ssot_p)
        ssot = raw.get("mcpServers") or raw.get("servers") or {}
    clientes = {
        "hermes": Path.home() / ".hermes/config.yaml",
        "opencode": Path.home() / ".config/opencode/opencode.jsonc",
        "dsh": Path.home() / ".dsh/profiles/cordis/cordis.patch.yml",
    }
    decl = {}
    for name, p in clientes.items():
        if not p.exists():
            decl[name] = None
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        decl[name] = sum(1 for k in ssot if k in txt)
    status = sh(["hermes", "mcp", "list"], timeout=90)
    down = [l.strip().split()[0] for l in status["out"].splitlines()
            if "✗" in l and "disabled" not in l and l.strip()]
    disabled = [l.strip().split()[0] for l in status["out"].splitlines()
                if "✗ disabled" in l and l.strip()]
    enabled = [l.strip().split()[0] for l in status["out"].splitlines() if "✓ enabled" in l]
    return {"ssot_servers": len(ssot), "clientes_declaran": decl,
            "hermes_enabled": len(enabled), "hermes_down": down, "hermes_disabled": disabled,
            "hermes_list_exit": status["exit"],
            "veredicto": "OK" if not down else "MCP_CAIDOS"}


# ─── REVISIÓN EXTERNA ────────────────────────────────────────────────────────
def external(resumen: dict, timeout=180) -> dict:
    """Consulta adversarial a un modelo externo (NIM local primero, GO después).

    No se finge: si no hay ruta o la respuesta no valida, se marca NO_DISPONIBLE.
    """
    from env_loader import load_env
    env = load_env()
    prompt = ("Eres un revisor adversarial de un harness de inferencia. Te doy un resumen JSON. "
              "Responde SOLO JSON con las claves: veredicto (VERDE|AMARILLO|ROJO), "
              "riesgos (lista de strings, máx 5), y accion (una frase). "
              "REGLA DURA: solo puedes hablar de campos que existan en el resumen; "
              "no menciones métricas ausentes (dispatch, ewma, retries, streams, contadores): "
              "si no están en el JSON, no existen y citarlas es una invención. "
              "Si falta un dato para juzgar, escríbelo como 'sin datos', no lo supongas.\n\nRESUMEN:\n"
              + json.dumps(resumen, ensure_ascii=False)[:6000])
    rutas = [
        ("nim_local", "http://127.0.0.1:8088/v1/chat/completions",
         "deepseek-ai/deepseek-v4.1-flash", {"Content-Type": "application/json"}),
        ("opencode-go", "https://opencode.ai/inference/go/openai/v1/chat/completions",
         "deepseek-v4-pro", {"Authorization": "Bearer " + env.get("C7_OPENCODE_GO", ""),
                             "Content-Type": "application/json", "User-Agent": "opencode/1.4.9 (linux x64)",
                             "x-opencode-session": "harness-full-audit"}),
    ]
    last = "sin ruta"
    for prov, url, model, hdr in rutas:
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=json.dumps(
                {"model": model, "messages": [{"role": "user", "content": prompt}],
                 "max_tokens": 2500, "temperature": 0}).encode(), headers=hdr)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            txt = (d["choices"][0]["message"].get("content") or "").strip()
            i, j = txt.find("{"), txt.rfind("}")
            if i < 0 or j < 0:
                last = f"{prov}: respuesta sin JSON"
                continue
            rev = json.loads(txt[i:j + 1])
            # R12 aplicado al revisor: toda cifra suya debe existir en el resumen enviado
            import re as _re
            blob = json.dumps(resumen, ensure_ascii=False)
            citadas = set(_re.findall(r"\b\d{1,6}(?:\.\d+)?\b", json.dumps(rev, ensure_ascii=False)))
            sin_traza = sorted(n for n in citadas if n not in blob)
            # términos técnicos (snake_case, con dígitos, o claves) que no existen en el payload
            # solo tokens TÉCNICOS: snake_case, camelCase o con dígitos (no palabras normales)
            terminos = set(_re.findall(
                r"\b[A-Za-z]+_[A-Za-z0-9_]+\b|\b[a-z]+[A-Z][A-Za-z0-9]*\b|\b[a-zA-Z]{3,}\d[A-Za-z0-9]*\b",
                json.dumps(rev, ensure_ascii=False)))
            terminos_sin = sorted(t for t in terminos if t.lower() not in blob.lower())[:12]
            return {"status": "OK", "provider": prov, "model": d.get("model") or model,
                    "ms": int((time.time() - t0) * 1000), "review": rev,
                    "cifras_sin_traza": sin_traza[:12],
                    "terminos_sin_traza": terminos_sin,
                    "validado": not sin_traza and not terminos_sin}
        except Exception as e:  # noqa: BLE001
            last = f"{prov}: {type(e).__name__}: {str(e)[:120]}"
    return {"status": "NO_DISPONIBLE", "error": last}


# ─── PIPELINE ────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-external", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.print_help()
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    LOG.write_text(f"harness_full_audit {TS}\n", encoding="utf-8")
    R = {"ts": TS, "fast": a.fast, "apply": a.apply, "stages": {}}
    t0 = time.time()

    # 0 preflight
    try:
        with urllib.request.urlopen("http://127.0.0.1:8088/health", timeout=10) as r:
            health = json.load(r)
    except Exception as e:  # noqa: BLE001
        health = {"status": "down", "error": str(e)}
    R["stages"]["preflight"] = {"proxy": health, "ok": health.get("status") == "ok"}
    print(f"[0] preflight: proxy {health.get('status')} · {health.get('available_accounts')} cuentas")
    if not R["stages"]["preflight"]["ok"]:
        (OUT / f"full_audit_{TS}.json").write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding="utf-8")
        return 3

    pasos = [
        ("registro", [sys.executable, "scratch/harness_v51/model_state_registry.py", "--build"], 240),
        ("contexto", [sys.executable, "SCRIPTS/refresh_ctx_from_catalog.py"], 180),
        ("lint", [sys.executable, "scratch/harness_v51/model_state_registry.py", "--lint"], 180),
        ("nombres", [sys.executable, "SCRIPTS/apply_model_names.py"] + (["--apply"] if a.apply else []), 120),
        ("allowlist", [sys.executable, "SCRIPTS/gen_c7_allowlist.py"], 120),
        ("suite_overlay", [sys.executable, "SCRIPTS/suite_overlay_gen.py"], 120),
        ("suite_cotejo", [sys.executable, "scratch/harness_v51/suite_cotejo.py"], 180),
        ("switch", [sys.executable, "SCRIPTS/harness_switch.py", "--bench", "20"], 180),
        ("dashboard", [sys.executable, "SCRIPTS/harness_dashboard.py"], 120),
    ]
    if not a.fast:
        pasos.insert(7, ("bench_ciego", [sys.executable, "scratch/harness_v51/bench_publicable.py",
                                         "--run", "--evaluate"], 1800))
        pasos.insert(8, ("recall", [sys.executable, "scratch/harness_v51/recall_test.py"], 900))

    for i, (name, cmd, to) in enumerate(pasos, 1):
        r = sh(cmd, timeout=to)
        R["stages"][name] = {"exit": r["exit"], "ms": r["ms"]}
        flag = "OK " if r["exit"] == 0 else f"exit {r['exit']}"
        print(f"[{i}] {name:<14} {flag} · {r['ms']} ms", flush=True)

    # enjambre + revisión externa
    R["stages"]["enjambre"] = swarm()
    print(f"[enjambre] {R['stages']['enjambre']['veredicto']} · "
          f"{R['stages']['enjambre']['ssot_servers']} servidores SSOT · "
          f"caídos {R['stages']['enjambre']['hermes_down'] or 'ninguno'}")
    if not a.no_external:
        R["stages"]["revision_externa"] = external(R["stages"])
        print(f"[externa] {R['stages']['revision_externa']['status']} · "
              f"{R['stages']['revision_externa'].get('provider', R['stages']['revision_externa'].get('error'))}")

    # veredicto
    duros = [n for n, s in R["stages"].items() if isinstance(s, dict) and s.get("exit") not in (None, 0)]
    lint = jload(OUT / "model_names_lint.json")
    cotejo = jload(OUT / "suite_cotejo.json")
    mcp_down = R["stages"]["enjambre"]["hermes_down"]
    R["hallazgos_duros"] = {"etapas_fallidas": duros,
                            "lint": len(lint.get("findings", [])),
                            "suite": cotejo.get("verdict"),
                            "mcp_caidos": mcp_down}
    rojo = (bool(duros) or int(R["hallazgos_duros"]["lint"] or 0) > 0
            or cotejo.get("verdict") == "DERIVA" or bool(mcp_down))
    R["veredicto"] = "ROJO" if rojo else "VERDE"
    R["duracion_s"] = int(time.time() - t0)

    (OUT / f"full_audit_{TS}.json").write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding="utf-8")

    # informe legible
    pub = jload(OUT / "publicable_eval_v2.json") or jload(OUT / "publicable_eval.json")
    md = [f"# Auditoría completa del harness — {TS}", "",
          f"**Veredicto: {R['veredicto']}** · {R['duracion_s']} s · modo {'--fast' if a.fast else 'completo'}"
          f"{' · APLICADO' if a.apply else ' · propuesta (sin aplicar)'}", "",
          "| Etapa | Estado | ms |", "|---|---|---|"]
    for n, s in R["stages"].items():
        if isinstance(s, dict) and "exit" in s:
            md.append(f"| {n} | {'✔' if s['exit']==0 else '✘ exit '+str(s['exit'])} | {s['ms']} |")
        else:
            md.append(f"| {n} | {s.get('veredicto', s.get('status','—'))} | — |")
    if pub:
        md += ["", f"Banco ciego v2: GO **{pub['totals']['GO']['tareas_pass_all']}/8** · "
                    f"FREE **{pub['totals']['FREE']['tareas_pass_all']}/8** · p={pub['mcnemar']['p_exact']}"]
    rev = R["stages"].get("revision_externa") or {}
    if rev.get("status") == "OK":
        md += ["", f"**Revisión externa** ({rev['provider']}/{rev['model']}, {rev['ms']} ms):",
               f"- veredicto: {rev['review'].get('veredicto')}",
               f"- acción: {rev['review'].get('accion')}",
               "- riesgos: " + "; ".join(str(x) for x in (rev['review'].get('riesgos') or []))]
    md += ["", f"Artefacto: `out/full_audit_{TS}.json` · log: `out/full_audit_{TS}.log`"]
    (H51 / "FULL_AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nVEREDICTO {R['veredicto']} · {R['duracion_s']} s → {H51/'FULL_AUDIT.md'}")
    return 0 if R["veredicto"] == "VERDE" else 2


if __name__ == "__main__":
    sys.exit(main())
