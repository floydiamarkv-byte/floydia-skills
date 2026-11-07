#!/usr/bin/env python3
"""Genera el overlay que la Suite 2.0 consume para no poseer su propia verdad de modelos.

Salida: FLOYDIA/PUBLIC_REPOS/floydia-suite-desktop/cache/models_overlay.json
  drop    → ids declarados que ya no existen en su catálogo
  context → contexto real para los que sí existen
La Suite aplica el overlay en tiempo de carga (tab_radar.py) y `suite_cotejo.py` lo replica.
Uso: python3 SCRIPTS/suite_overlay_gen.py [--dry-run]
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUITE = ROOT / "FLOYDIA/PUBLIC_REPOS/floydia-suite-desktop"
RADAR = SUITE / "modules/tab_radar.py"
OUT = SUITE / "cache/models_overlay.json"
sys.path.insert(0, str(ROOT / "SCRIPTS"))
from env_loader import load_env  # noqa: E402

UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/131.0"


def main() -> int:
    dry = "--dry-run" in sys.argv
    env = load_env()
    with urllib.request.urlopen(urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": "Bearer " + env["C7_OPENROUTER"], "User-Agent": UA}), timeout=30) as r:
        cat = {m["id"]: m for m in json.load(r)["data"]}
    with urllib.request.urlopen("http://127.0.0.1:8088/v1/models", timeout=20) as r:
        nim = {m["id"] for m in json.load(r)["data"]}

    text = RADAR.read_text(encoding="utf-8")
    entries = []
    for line in text.splitlines():
        if '"id":' not in line or '"provider":' not in line:
            continue
        mid = re.search(r'"id":\s*"([^"]+)"', line)
        prov = re.search(r'"provider":\s*"([^"]+)"', line)
        ctx = re.search(r'"context":\s*(\d+)', line)
        if mid and prov:
            entries.append({"id": mid.group(1), "provider": prov.group(1),
                            "context": int(ctx.group(1)) if ctx else None})

    drop, ctx_map, unverified = [], {}, 0
    for e in entries:
        if e["provider"] == "nvidia":          # mismo upstream que el proxy :8088
            if e["id"] not in nim:
                drop.append(e["id"])
            continue
        if e["provider"] != "openrouter":      # el resto son proveedores directos sin catálogo en la sonda
            unverified += 1
            continue
        m = cat.get(e["id"])
        if not m:
            drop.append(e["id"])
            continue
        real = m.get("context_length")
        if real and e["context"] and abs(real - e["context"]) / real > 0.02:
            ctx_map[e["id"]] = int(real)

    ov = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "GET https://openrouter.ai/api/v1/models",
        "ttl_days": 7,
        "suite_entries": len(entries),
        "openrouter_verified": len(entries) - unverified,
        "unverified_direct_providers": unverified,
        "drop": sorted(set(drop)),
        "context": ctx_map,
    }
    print(f"overlay: drop={len(ov['drop'])} · ctx={len(ctx_map)} · verificados={ov['openrouter_verified']} · "
          f"sin verificar(proveedor directo)={unverified}")
    if dry:
        print(json.dumps(ov, indent=1, ensure_ascii=False)[:900])
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(ov, indent=1, ensure_ascii=False), encoding="utf-8")
    print("escrito:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
