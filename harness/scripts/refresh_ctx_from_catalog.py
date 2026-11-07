#!/usr/bin/env python3
"""Rellena ctx_real del registro desde los catálogos que SÍ publican límites.

GO (/inference/go/openai/v1/models) trae `limit.context`; OpenRouter trae `context_length`.
NIM (:8088) no publica límites → sus entradas quedan sin medir y el lint las excluye.
Uso: python3 SCRIPTS/refresh_ctx_from_catalog.py [--dry-run]
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "scratch/harness_v51/out/model_state_registry.json"
sys.path.insert(0, str(ROOT / "SCRIPTS"))
from env_loader import load_env  # noqa: E402


def main() -> int:
    dry = "--dry-run" in sys.argv
    env = load_env()
    H = {"Authorization": "Bearer " + env["C7_OPENCODE_GO"], "User-Agent": "opencode/1.4.9 (linux x64)",
         "x-opencode-session": "hp15-ctx"}
    with urllib.request.urlopen(urllib.request.Request(
            "https://opencode.ai/inference/go/openai/v1/models", headers=H), timeout=30) as r:
        go = {m["id"]: (m.get("limit") or {}).get("context") for m in json.load(r)["data"]}
    with urllib.request.urlopen(urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": "Bearer " + env["C7_OPENROUTER"],
                     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/131.0"}), timeout=30) as r:
        ora = {m["id"]: m.get("context_length") for m in json.load(r)["data"]}

    # Google publica inputTokenLimit en models.list; NVIDIA y Cerebras no publican nada.
    try:
        g = json.load(urllib.request.urlopen(
            "https://generativelanguage.googleapis.com/v1beta/models?key=" + env.get("C1_GOOGLE_AISTUDIO", ""),
            timeout=25))
        goog = {m["name"].split("/")[-1]: m.get("inputTokenLimit") for m in g.get("models", [])}
    except Exception:  # noqa: BLE001
        goog = {}

    doc = json.loads(REG.read_text())
    filled = upd = 0
    for e in doc["entries"]:
        prov, mid = e["id"].split("/", 1)
        ctx = None
        if prov == "opencode_go":
            ctx = go.get(mid)
        elif prov == "openrouter":
            ctx = ora.get(mid)
        elif prov.startswith("google"):
            ctx = goog.get(mid.split("/")[-1])
        if ctx:
            if e.get("ctx_real") != int(ctx):
                upd += 1
            e["ctx_real"] = int(ctx)
            e["ctx_source"] = "catalogo:" + prov
            e["ctx_status"] = "VERIFIED"
            e["last_verified"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            filled += 1
    unknown = [e["id"] for e in doc["entries"] if not e.get("ctx_real")]
    for e in doc["entries"]:
        if not e.get("ctx_real"):
            e["ctx_status"] = "UNPUBLISHED"   # estado terminal: el proveedor no publica el límite
    doc["ctx_filled"] = filled
    doc["ctx_unknown"] = len(unknown)
    doc["ctx_policy"] = ("VERIFIED = leído del catálogo del proveedor · UNPUBLISHED = el proveedor no "
                         "publica el límite (etiqueta [?] en el nombre, estado terminal, no tarea abierta)")
    print(f"ctx desde catálogo: {filled} modelos ({upd} valores corregidos) · sin medir: {len(unknown)}")
    for u in unknown[:6]:
        print("  sin medir:", u)
    if not dry:
        REG.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
        print("registro actualizado:", REG)
    return 0


if __name__ == "__main__":
    sys.exit(main())
