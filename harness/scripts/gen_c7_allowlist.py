#!/usr/bin/env python3
"""Genera providers/c7_allowlist.yaml desde el catálogo vivo de OpenRouter.

Regla (v5.1 §5.2): la allowlist es PROYECCIÓN del catálogo, nunca se edita a mano.
Criterios: precio prompt y completion == 0, acepta tools, id no es router.
Uso: python3 SCRIPTS/gen_c7_allowlist.py [--dry-run]
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "SCRIPTS"))
from env_loader import load_env  # noqa: E402

OUT = ROOT / "providers/c7_allowlist.yaml"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"


def main() -> int:
    dry = "--dry-run" in sys.argv
    env = load_env()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": "Bearer " + env["C7_OPENROUTER"], "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)["data"]

    ok, seen = [], set()
    for m in data:
        mid = m["id"]
        p = m.get("pricing") or {}
        if p.get("prompt") not in ("0", "0.0", 0) or p.get("completion") not in ("0", "0.0", 0):
            continue
        if "tools" not in (m.get("supported_parameters") or []):
            continue
        if mid.startswith("openrouter/") or ":nitro" in mid or ":online" in mid:
            continue
        if mid in seen:
            continue
        seen.add(mid)
        ok.append({
            "id": mid,
            "context": int(m.get("context_length") or 0),
            "vision": "image" in (m.get("architecture") or {}).get("input_modalities", []),
        })
    ok.sort(key=lambda x: (-x["context"], x["id"]))

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    lines = [
        "# providers/c7_allowlist.yaml",
        "# GENERADO por SCRIPTS/gen_c7_allowlist.py — NO EDITAR A MANO.",
        f"# fuente: GET https://openrouter.ai/api/v1/models · {ts}",
        "# criterio: pricing.prompt == 0 AND pricing.completion == 0 AND tools AND no-router",
        "",
        'version: "5.1"',
        f'updated_at: "{ts}"',
        'policy: "zero-spend-strict"',
        f"generated_from_catalog_models: {len(data)}",
        f"free_with_tools: {len(ok)}",
        "",
        "allowed_models:",
    ]
    for m in ok:
        lines += [
            f'  - id: "{m["id"]}"',
            f"    context: {m['context']}",
            f"    vision: {'true' if m['vision'] else 'false'}",
            "    free_verified: true",
        ]
    txt = "\n".join(lines) + "\n"
    if dry:
        print(txt[:1200])
        return 0
    OUT.write_text(txt, encoding="utf-8")
    print(f"allowlist: {len(ok)} modelos free con tools de {len(data)} del catálogo → {OUT}")
    for m in ok[:8]:
        print(f"  {m['id']:<45} ctx={m['context']:<8} vision={m['vision']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
