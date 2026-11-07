#!/usr/bin/env python3
"""Despacha la suite de verificación v32 a los 4 agentes y coteja sus respuestas.

Cada agente corre SU prompt por su propio CLI headless:
  hermes      → hermes -z "<prompt>"
  opencode    → opencode run "<prompt>"
  dsh         → dsh --profile headless "<prompt>"
  antigravity → python3 SCRIPTS/agy_acp_delegate.py "<prompt>" --timeout 600

Salidas: scratch/harness_v51/out/agent_suite/<agente>_raw.txt · <agente>.json · COTEJO.md
Uso:
    python3 SCRIPTS/run_agent_suite.py --list
    python3 SCRIPTS/run_agent_suite.py --run --only hermes
    python3 SCRIPTS/run_agent_suite.py --run            # los cuatro
    python3 SCRIPTS/run_agent_suite.py --cotejo         # recolecta y compara lo ya corrido
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

PROJ = Path("/home/tec/Dropbox/ANTIGRAVITY_PROJECTS")
SUITE = PROJ / "memory-bank/prompts/SUITE_VERIFICACION_HARNESS_4_AGENTES_V32.md"
OUT = PROJ / "scratch/harness_v51/out/agent_suite"
TS = time.strftime("%Y%m%d-%H%M%S")

AGENTES = {
    "antigravity": {"titulo": "ANTIGRAVITY IDE", "timeout": 900},
    "opencode": {"titulo": "OPENCODE DESKTOP", "timeout": 900},
    "dsh": {"titulo": "DEEPSEEK HARNESS", "timeout": 900},
    "hermes": {"titulo": "HERMES DESKTOP", "timeout": 900},
}


def prompts() -> dict[str, str]:
    """Extrae el bloque ```markdown``` de cada '## PROMPT n — ...'."""
    txt = SUITE.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"## PROMPT (\d) — ([^\n]+)\n+```markdown\n(.*?)```", txt, re.S):
        num, titulo, cuerpo = m.group(1), m.group(2), m.group(3)
        if "ANTIGRAVITY" in titulo.upper():
            key = "antigravity"
        elif "OPENCODE" in titulo.upper():
            key = "opencode"
        elif "DEEPSEEK" in titulo.upper() or "DSH" in titulo.upper():
            key = "dsh"
        else:
            key = "hermes"
        out[key] = cuerpo.replace("<PROYECTO>", str(PROJ))
    return out


def cmd_for(agent: str, prompt: str) -> list[str]:
    if agent == "hermes":
        return ["hermes", "-z", prompt]
    if agent == "opencode":
        return ["opencode", "run", prompt]
    if agent == "dsh":
        return ["dsh", "--profile", "headless", prompt]
    if agent == "antigravity":
        return [sys.executable, "SCRIPTS/agy_acp_delegate.py", prompt, "--timeout", "600"]
    raise SystemExit(f"agente desconocido: {agent}")


def extract_json(text: str) -> dict | None:
    """Último objeto JSON equilibrado del texto (los agentes a veces narran antes)."""
    best, depth, start = None, 0, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    cand = json.loads(text[start:i + 1])
                    if isinstance(cand, dict) and ("agente" in cand or "veredicto" in cand):
                        best = cand
                except Exception:  # noqa: BLE001
                    pass
    return best


def run(agent: str) -> dict:
    p = prompts().get(agent)
    if not p:
        return {"agente": agent, "status": "SIN_PROMPT"}
    OUT.mkdir(parents=True, exist_ok=True)
    cmd = cmd_for(agent, p)
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=str(PROJ), capture_output=True, text=True,
                           timeout=AGENTES[agent]["timeout"])
        rc, out, err = r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        def _dec(x):
            if x is None:
                return ""
            return x.decode("utf-8", "replace") if isinstance(x, bytes) else str(x)
        rc, out, err = 124, _dec(e.stdout), _dec(e.stderr) + "\n[timeout del despachador]"
    ms = int((time.time() - t0) * 1000)
    (OUT / f"{agent}_raw.txt").write_text(
        f"$ {' '.join(cmd[:4])} …\n[exit {rc} · {ms} ms]\n\n--- STDOUT ---\n{out}\n\n--- STDERR ---\n{err}",
        encoding="utf-8")
    data = extract_json(out + "\n" + err)
    if data:
        (OUT / f"{agent}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"agente": agent, "exit": rc, "ms": ms, "json": bool(data),
            "chars": len(out), "preview": (out or err).strip()[:160]}


def cotejo() -> int:
    """Compara los JSON disponibles y escribe COTEJO.md."""
    filas, datos = [], {}
    for a in AGENTES:
        f = OUT / f"{a}.json"
        if f.exists():
            try:
                datos[a] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                datos[a] = None
    campos = [
        ("version_arnes", lambda d: d.get("version_arnes")),
        ("modelos.catalogo", lambda d: (d.get("modelos") or {}).get("catalogo")),
        ("modelos.default", lambda d: (d.get("modelos") or {}).get("default")),
        ("modelos.small", lambda d: (d.get("modelos") or {}).get("small")),
        ("mcp.ssot", lambda d: (d.get("mcp") or {}).get("ssot")),
        ("mcp.cliente", lambda d: (d.get("mcp") or {}).get("cliente")),
        ("mcp.caidos", lambda d: (d.get("mcp") or {}).get("caidos")),
        ("veredicto.artefacto", lambda d: (d.get("veredicto") or {}).get("artefacto")),
        ("veredicto.entorno", lambda d: (d.get("veredicto") or {}).get("entorno")),
    ]
    md = [f"# Cotejo de la suite de verificación — {TS}", "",
          f"Agentes con JSON válido: **{len([d for d in datos.values() if d])}/4**", "",
          "| Campo | " + " | ".join(AGENTES[a]["titulo"].split()[0] for a in AGENTES) + " |",
          "|---|" + "---|" * len(AGENTES)]
    for nombre, getter in campos:
        vals = []
        for a in AGENTES:
            d = datos.get(a)
            vals.append(str(getter(d)) if d else "—")
        md.append(f"| {nombre} | " + " | ".join(vals) + " |")
    # discrepancias sobre el valor mayoritario
    disc = []
    for nombre, getter in campos:
        vals = {a: getter(datos[a]) for a in AGENTES if datos.get(a)}
        limpios = [v for v in vals.values() if v not in (None, "", "None")]
        if len(set(map(str, limpios))) > 1:
            disc.append((nombre, {a: str(v) for a, v in vals.items()}))
    md += ["", "## Discrepancias", ""]
    md += [f"- **{n}**: " + " · ".join(f"{a}={v}" for a, v in d.items()) for n, d in disc] or ["- ninguna"]
    md += ["", "## Sin JSON (revisar raw)", ""]
    md += [f"- `{a}_raw.txt`" for a in AGENTES if not datos.get(a)] or ["- ninguno"]
    (OUT / "COTEJO.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"cotejo: {OUT/'COTEJO.md'} · {len([d for d in datos.values() if d])}/4 con JSON · {len(disc)} discrepancias")
    for n, d in disc:
        print(f"  ! {n}: " + " · ".join(f"{a}={v}" for a, v in d.items()))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--only", choices=list(AGENTES))
    ap.add_argument("--cotejo", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--prompt-file", help="sustituye el prompt de --only por el de este fichero")
    a = ap.parse_args()
    if a.list:
        for k, p in prompts().items():
            print(f"{k:<12} {len(p):>5} chars · {AGENTES[k]['timeout']} s")
        return 0
    if a.run:
        objetivo = [a.only] if a.only else list(AGENTES)
        if a.prompt_file and a.only:
            _orig = prompts
            extra = Path(a.prompt_file).read_text(encoding="utf-8")
            globals()["prompts"] = lambda: {**_orig(), a.only: extra}
        for ag in objetivo:
            print(f"→ {ag} …", flush=True)
            r = run(ag)
            print(f"  {ag}: exit {r.get('exit')} · {r.get('ms')} ms · json={r.get('json')} · {r.get('preview','')[:80]}", flush=True)
    if a.cotejo or a.run:
        return cotejo()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
