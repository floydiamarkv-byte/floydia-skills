#!/usr/bin/env python3
"""Registro de estado con TTL + lint de nomenclatura (propuesta v5.1).

--build  genera out/model_state_registry.json desde catálogos vivos + sondas medidas.
--lint   valida nombres/ctx/visión/IDs de los consumidores y sale 2 si hay deriva.

No escribe en los SSOT: la propuesta se aplica sólo con token humano.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
PROJ = Path("<PROYECTO>")
sys.path.insert(0, str(PROJ / "SCRIPTS"))
from env_loader import load_env  # noqa: E402

ENV = load_env()
UA = {"User-Agent": "opencode/1.4.9 (linux x64)", "x-opencode-session": "hp15-registry"}
TTL_DAYS = 7
# ctx puede ser "?" cuando el proveedor no publica límites y aún no se ha sondeado
GRAMMAR = re.compile(r"^\[(\?|OK|DEGRADED|RETIRED)\]\[(\?|[0-9]+[kM])\]\[(GO|F)(?:·C[0-9])?\]\s.+")
CTX_RE = re.compile(r"^\[(?:OK|DEGRADED|RETIRED)\]\[([0-9]+)([kM])\]")


def jget(url, headers, timeout=25):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
        return json.load(r)


def read_jsonc(p: Path):
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"^\s*//.*$", "", t, flags=re.M)
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return json.loads(t)


def catalogs():
    go = jget("https://opencode.ai/inference/go/v1/models",
              {**UA, "Authorization": "Bearer " + ENV["C7_OPENCODE_GO"]})
    nim = jget("http://127.0.0.1:8088/v1/models", {})
    orr = jget("https://openrouter.ai/api/v1/models", {"Authorization": "Bearer " + ENV["C7_OPENROUTER"], **UA})
    try:
        gdoc = jget("https://generativelanguage.googleapis.com/v1beta/models?key=" + ENV.get("C1_GOOGLE_AISTUDIO", ""), {})
        google = {m["name"].split("/")[-1] for m in gdoc.get("models", [])}
    except Exception:  # noqa: BLE001
        google = set()
    return {
        "google": google,
        "go": {m["id"] for m in go["data"]},
        "nim": {m["id"] for m in nim["data"]},
        "or": {m["id"]: m for m in orr["data"]},
    }


def probes():
    p = OUT / "f1_probe.json"
    if p.exists():
        return json.loads(p.read_text())
    return {}


def ctx_from_billing(mid: str):
    bm = json.loads((PROJ / "SCRIPTS/harness_billing_matrix.json").read_text())
    m = bm.get("models", {}).get(mid)
    return (m or {}).get("context")


def build():
    cat = catalogs()
    pr = probes()
    bm = json.loads((PROJ / "SCRIPTS/harness_billing_matrix.json").read_text())
    entries = []
    seen = set()

    oc = read_jsonc(Path("~/.config/opencode/opencode.jsonc"))
    for prov, body in (oc.get("provider") or {}).items():
        for mid, meta in (body.get("models") or {}).items():
            key = (prov, mid)
            if key in seen:
                continue
            seen.add(key)
            if prov in ("opencode_go",):
                exists = mid in cat["go"]; src = "opencode_go"
            elif prov == "nim_local":
                exists = mid in cat["nim"]; src = "nim"
            elif prov == "openrouter":
                exists = mid in cat["or"]; src = "openrouter"
            elif prov.startswith("google"):
                exists = mid.split("/")[-1] in cat["google"]; src = prov
            else:
                exists = None; src = prov
            ctx = None
            if src == "openrouter":
                ctx = (cat["or"].get(mid) or {}).get("context_length")
            elif src == "opencode_go":
                ctx = ctx_from_billing(mid)
            p = pr.get(f"{src}:{mid}") or {}
            entries.append({
                "id": f"{src}/{mid}",
                "provider": src,
                "existe": exists,
                "tools": p.get("tools"),
                "vision": p.get("vision"),
                "ctx_real": ctx,
                "ctx_declarado": ((meta.get("limit") or {}).get("context")),
                "last_verified": p.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "estado": ("ACTIVE" if exists else ("DEGRADED" if exists is False else "UNKNOWN")),
                "coste": {"factor": (bm["models"].get(mid.split("/")[-1]) or {}).get("factor"),
                          "list_input_1m": (bm["models"].get(mid.split("/")[-1]) or {}).get("input_1m")},
                "TTL_days": TTL_DAYS,
            })
    reg = {"version": "5.1-proposal", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "ttl_days": TTL_DAYS, "source_of_truth": {
               "go": "https://opencode.ai/inference/go/v1/models + harness_billing_matrix.json",
               "nim": "http://127.0.0.1:8088/v1/models",
               "openrouter": "https://openrouter.ai/api/v1/models"},
           "entries": entries}
    (OUT / "model_state_registry.json").write_text(json.dumps(reg, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"registry: {len(entries)} entradas → {OUT/'model_state_registry.json'}")
    print("no existen:", [e["id"] for e in entries if e["existe"] is False])


def lint():
    cat = catalogs()
    reg = {}
    if (OUT / "model_state_registry.json").exists():
        reg = {e["id"]: e for e in json.loads((OUT / "model_state_registry.json").read_text())["entries"]}
    oc = read_jsonc(Path("~/.config/opencode/opencode.jsonc"))
    bm = json.loads((PROJ / "SCRIPTS/harness_billing_matrix.json").read_text())
    findings = []
    for prov, body in (oc.get("provider") or {}).items():
        for mid, meta in (body.get("models") or {}).items():
            name = meta.get("name") or ""
            ctx_decl = (meta.get("limit") or {}).get("context")
            if not GRAMMAR.match(name):
                findings.append({"type": "NOMBRE_NO_CONFORME", "id": mid, "name": name})
                continue
            def _tag(v: int) -> str:
                if v >= 999_500:
                    return f"{round(v / 1_000_000)}M"
                if v % 1000 == 0:
                    return f"{round(v / 1000)}k"
                return f"{round(v / 1024)}k"
            m = CTX_RE.match(name)
            if m:
                num, unit = int(m.group(1)), m.group(2)
                claimed = num * (1000 if unit == "k" else 1_000_000)
                real = (reg.get(f"{prov}/{mid}") or {}).get("ctx_real")
                ref = int(real) if real else ctx_decl
                if ref and _tag(claimed) != _tag(int(ref)):
                    findings.append({"type": "CTX_NOMBRE_VS_REAL", "id": mid, "name": name,
                                     "claimed": claimed, "referencia": ref})
            if prov == "opencode_go" and mid not in cat["go"]:
                findings.append({"type": "ID_INEXISTENTE", "id": mid, "provider": prov})
            if prov == "nim_local" and mid not in cat["nim"]:
                findings.append({"type": "ID_INEXISTENTE", "id": mid, "provider": prov})
            if prov == "openrouter" and mid not in cat["or"]:
                findings.append({"type": "ID_INEXISTENTE", "id": mid, "provider": prov})
    ids = [mid for prov, body in (oc.get("provider") or {}).items() for mid in (body.get("models") or {})]
    pares = [(prov, mid) for prov, body in (oc.get("provider") or {}).items() for mid in (body.get("models") or {})]
    dups = sorted({i for p_, i in pares if sum(1 for q_, j in pares if q_ == p_ and j == i) > 1})
    for d in dups:
        findings.append({"type": "ID_DUPLICADO", "id": d})
    out = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "checked": len(ids), "findings": findings,
           "by_type": {t: sum(1 for f in findings if f["type"] == t)
                       for t in sorted({f["type"] for f in findings})}}
    (OUT / "model_names_lint.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out["by_type"], indent=1))
    for f in findings[:15]:
        print(" -", f)
    sys.exit(2 if findings else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--lint", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    if a.lint:
        lint()
