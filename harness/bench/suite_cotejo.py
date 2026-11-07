#!/usr/bin/env python3
"""Cotejo Suite 2.0 vs SSOT (propuesta §9). exit 2 ante cualquier deriva.

La Suite CONSUME: su lista de modelos en modules/tab_radar.py y su caché de proveedores
deben ser proyección del catálogo, no fuente. Este script lo verifica.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
PROJ = Path("<PROYECTO>")
sys.path.insert(0, str(PROJ / "SCRIPTS"))
from env_loader import load_env  # noqa: E402

ENV = load_env()
UA = {"User-Agent": "opencode/1.4.9 (linux x64)"}
RADAR = PROJ / "FLOYDIA/PUBLIC_REPOS/floydia-suite-desktop/modules/tab_radar.py"
CACHE = Path("~/.hermes/provider_models_cache.json")


def jget(url, headers):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as r:
        return json.load(r)


def main():
    go = {m["id"] for m in jget("https://opencode.ai/inference/go/v1/models",
                                {**UA, "Authorization": "Bearer " + ENV["C7_OPENCODE_GO"]})["data"]}
    nim = {m["id"] for m in jget("http://127.0.0.1:8088/v1/models", {})["data"]}
    orr = {m["id"]: m for m in jget("https://openrouter.ai/api/v1/models",
                                    {"Authorization": "Bearer " + ENV["C7_OPENROUTER"], **UA})["data"]}
    live = go | nim | set(orr)

    text = RADAR.read_text(encoding="utf-8")
    models = []
    for line in text.splitlines():
        if '"id":' not in line or '"context":' not in line:
            continue
        mid = re.search(r'"id":\s*"([^"]+)"', line)
        name = re.search(r'"name":\s*"([^"]*)"', line)
        ctx = re.search(r'"context":\s*(\d+)', line)
        prov = re.search(r'"provider":\s*"([^"]+)"', line)
        if mid and ctx:
            models.append({"id": mid.group(1), "name": (name.group(1) if name else ""),
                           "context": int(ctx.group(1)), "provider": (prov.group(1) if prov else "?")})

    # Overlay generado: la Suite lo aplica al cargar (tab_radar.py) y aquí se replica.
    ov_path = PROJ / "FLOYDIA/PUBLIC_REPOS/floydia-suite-desktop/cache/models_overlay.json"
    ov, ov_age = {}, None
    if ov_path.exists():
        ov = json.loads(ov_path.read_text(encoding="utf-8"))
        ov_age = round((time.time() - ov_path.stat().st_mtime) / 86400.0, 2)
        _drop = set(ov.get("drop") or [])
        _ctx = ov.get("context") or {}
        models = [m for m in models if m["id"] not in _drop]
        for m in models:
            if m["id"] in _ctx:
                m["context"] = int(_ctx[m["id"]])

    drift, unverified = [], []
    for m in models:
        if m["provider"] not in ("openrouter", "opencode_go", "nim_local", "nvidia"):
            unverified.append({"id": m["id"], "provider": m["provider"],
                               "why": "catálogo directo del proveedor no incluido en la sonda"})
            continue
        if m["id"] not in live:
            drift.append({"type": "MODELO_INEXISTENTE", "id": m["id"], "name": m["name"]})
            continue
        real = None
        if m["provider"] == "openrouter" and m["id"] in orr:
            real = orr[m["id"]].get("context_length")   # solo OpenRouter publica contexto
        if real and abs(real - m["context"]) / real > 0.02:
            drift.append({"type": "CTX_DISTINTO", "id": m["id"], "suite": m["context"], "real": real})
        if "•Free" in m["name"] and m["id"] not in orr:
            drift.append({"type": "BADGE_FREE_SIN_FREE", "id": m["id"], "name": m["name"]})

    # caché de proveedores de Hermes: ids que ya no existen
    cache_drift = []
    if CACHE.exists():
        try:
            cd = json.loads(CACHE.read_text())
            ids = set()
            def walk(o):
                if isinstance(o, dict):
                    for k, v in o.items():
                        if k in ("id", "model") and isinstance(v, str):
                            ids.add(v)
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(cd)
            cache_drift = sorted(i for i in ids if "/" in i and i not in live and not i.startswith(("http", "opencode")))
        except Exception as e:  # noqa: BLE001
            cache_drift = [f"ERROR_LECTURA: {e}"]

    res = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "suite_file": str(RADAR).replace(str(PROJ) + "/", ""),
        "suite_models": len(models),
        "live_catalog": {"go": len(go), "nim": len(nim), "openrouter": len(orr)},
        "overlay": {"applied": bool(ov), "age_days": ov_age,
                    "ttl_days": ov.get("ttl_days"), "drop": len(ov.get("drop") or []),
                    "ctx_fixed": len(ov.get("context") or {}),
                    "stale": bool(ov and ov_age is not None and ov.get("ttl_days") and ov_age > float(ov["ttl_days"]))},
        "drift": drift,
        "unverified": unverified[:20],
        "unverified_count": len(unverified),
        "hermes_cache_missing": cache_drift,
        "verdict": "DERIVA" if (drift or cache_drift) else "SIN_DERIVA",
    }
    (OUT / "suite_cotejo.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "drift"}, indent=1, ensure_ascii=False))
    for d in drift[:15]:
        print(" -", d)
    sys.exit(2 if (drift or cache_drift) else 0)


if __name__ == "__main__":
    main()
