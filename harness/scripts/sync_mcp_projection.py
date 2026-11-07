#!/usr/bin/env python3
"""Regenera las proyecciones MCP por cliente desde el SSOT del enjambre.

SSOT  : ~/.gemini/config/mcp_config.full.json   (catálogo canónico, 21 servidores)
Reglas: ~/.gemini/config/mcp_clients.json       (allow/deny por cliente, '*' = todo)
Salida: ~/.gemini/config/mcp_config.json        (proyección que lee el cockpit y AGY)

Regla dura: si la proyección no cuadra con allow/deny, el cockpit muestra un subconjunto
y el operador cree que faltan servidores. Este script la reconstruye, nunca la edita a mano.

Uso: python3 SCRIPTS/sync_mcp_projection.py [--dry-run] [--client antigravity]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

CFG = Path.home() / ".gemini/config"
SSOT = CFG / "mcp_config.full.json"
CLIENTS = CFG / "mcp_clients.json"
PROJ = CFG / "mcp_config.json"
TS = time.strftime("%Y%m%d-%H%M%S")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="exit 2 si la proyección no cuadra con el SSOT")
    ap.add_argument("--client", default="antigravity")
    a = ap.parse_args()

    full = json.loads(SSOT.read_text(encoding="utf-8")).get("mcpServers") or {}
    rules = (json.loads(CLIENTS.read_text(encoding="utf-8")).get("clients") or {})
    rule = rules.get(a.client) or {}
    allow, deny = rule.get("allow", "*"), set(rule.get("deny") or [])

    if allow == "*":
        seleccion = {k: v for k, v in full.items() if k not in deny}
    else:
        seleccion = {k: full[k] for k in allow if k in full and k not in deny}

    faltan_en_ssot = [k for k in (allow if allow != "*" else []) if k not in full]

    # comparación con la proyección actual
    actual = {}
    if PROJ.exists():
        try:
            actual = json.loads(PROJ.read_text(encoding="utf-8")).get("mcpServers") or {}
        except Exception:  # noqa: BLE001
            actual = {}
    añadir = sorted(set(seleccion) - set(actual))
    quitar = sorted(set(actual) - set(seleccion))
    cambiar = sorted(k for k in set(seleccion) & set(actual) if seleccion[k] != actual[k])

    print(f"SSOT {len(full)} · cliente {a.client}: allow={allow} deny={sorted(deny)} → {len(seleccion)} servidores")
    print(f"proyección actual {len(actual)} · añadir {len(añadir)} {añadir[:6]} · quitar {len(quitar)} {quitar[:6]} · cambiar {len(cambiar)}")
    if faltan_en_ssot:
        print(f"  ! allow menciona servidores que no están en el SSOT: {faltan_en_ssot}")

    if a.check:
        desvio = bool(añadir or quitar or cambiar or faltan_en_ssot)
        if desvio:
            print(f"DERIVA: la proyección no cuadra con el SSOT (añadir {len(añadir)}, quitar {len(quitar)}, cambiar {len(cambiar)})")
        else:
            print(f"proyección coherente: {len(seleccion)} servidores")
        return 2 if desvio else 0
    if a.dry_run:
        return 0

    if PROJ.exists():
        shutil.copy2(PROJ, CFG / f"mcp_config.json.bak-{TS}")
    nuevo = {"mcpServers": dict(sorted(seleccion.items()))}
    tmp = CFG / "mcp_config.json.tmp"
    tmp.write_text(json.dumps(nuevo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, PROJ)
    print(f"escrito {PROJ} con {len(seleccion)} servidores · backup mcp_config.json.bak-{TS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
