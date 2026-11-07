#!/usr/bin/env python3
"""F2 — Frescura: catálogo vivo vs consumidores, allowlist, nombres y skills.

Salida: out/freshness_report.json. Sólo lectura sobre configs; no escribe SSOT.
"""
from __future__ import annotations

import json
import re
import subprocess
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
UA = {"User-Agent": "opencode/1.4.9 (linux x64)", "x-opencode-session": "hp15-f2"}


def jget(url, headers, timeout=25):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def live_catalogs():
    go = jget("https://opencode.ai/inference/go/v1/models",
              {**UA, "Authorization": "Bearer " + ENV["C7_OPENCODE_GO"]})
    nim = jget("http://127.0.0.1:8088/v1/models", {})
    orr = jget("https://openrouter.ai/api/v1/models",
               {"Authorization": "Bearer " + ENV["C7_OPENROUTER"], **UA})
    go_ids = {m["id"] for m in go["data"]}
    nim_ids = {m["id"] for m in nim["data"]}
    or_all = {m["id"]: m for m in orr["data"]}
    or_free = {k: v for k, v in or_all.items() if k.endswith(":free")}
    return {
        "go": go_ids, "nim": nim_ids, "or": set(or_all), "or_free": or_free,
        "or_meta": or_all,
    }


def read_jsonc(path: Path):
    txt = path.read_text(encoding="utf-8")
    txt = re.sub(r"^\s*//.*$", "", txt, flags=re.M)
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    return json.loads(txt)


def collect_refs(cat):
    refs = []  # (consumer, id, provider_hint)

    oc = read_jsonc(Path("~/.config/opencode/opencode.jsonc"))
    for prov, body in (oc.get("provider") or {}).items():
        for mid, meta in (body.get("models") or {}).items():
            refs.append({"consumer": "opencode.jsonc", "provider": prov, "id": mid,
                         "name": meta.get("name"), "ctx_declared": ((meta.get("limit") or {}).get("context")),
                         "attachment": meta.get("attachment")})
    for key in ("model", "small_model"):
        v = oc.get(key)
        if v:
            refs.append({"consumer": f"opencode.jsonc:{key}", "provider": v.split("/")[0],
                         "id": v.split("/", 1)[1]})

    hm = json.loads((PROJ / "SCRIPTS/harness_mode.json").read_text())
    for key in ("default_model", "architect_model", "small_model"):
        v = hm.get(key)
        if v and "/" in v:
            refs.append({"consumer": f"harness_mode:{key}", "provider": v.split("/")[0],
                         "id": v.split("/", 1)[1]})
    for cap, body in (hm.get("routing_policy") or {}).items():
        for key in ("primary", "fallback", "model", "models"):
            v = body.get(key) if isinstance(body, dict) else None
            for item in ([v] if isinstance(v, str) else (v or [])):
                if isinstance(item, str) and "/" in item:
                    refs.append({"consumer": f"harness_mode:routing.{cap}",
                                 "provider": item.split("/")[0], "id": item.split("/", 1)[1]})

    import yaml
    hc = yaml.safe_load(Path("~/.hermes/config.yaml").read_text())
    m = hc.get("model") or {}
    if isinstance(m, dict):
        refs.append({"consumer": "hermes:model", "provider": m.get("provider"),
                     "id": m.get("default")})
    if hc.get("small_model"):
        refs.append({"consumer": "hermes:small_model", "provider": "nim_local", "id": hc["small_model"]})
    for p in (hc.get("fallback_providers") or []):
        if isinstance(p, dict):
            refs.append({"consumer": "hermes:fallback", "provider": p.get("provider"), "id": p.get("model")})
    for k, v in (hc.get("auxiliary") or {}).items():
        if isinstance(v, dict) and v.get("model"):
            refs.append({"consumer": f"hermes:aux.{k}", "provider": v.get("provider"), "id": v["model"]})

    al = yaml.safe_load((PROJ / "providers/c7_allowlist.yaml").read_text())
    for item in al.get("allowed_models") or []:
        refs.append({"consumer": "c7_allowlist", "provider": "openrouter", "id": item.get("id"),
                     "ctx_declared": item.get("context")})
    return refs


def resolve(ref, cat):
    prov = (ref.get("provider") or "").lower()
    mid = ref.get("id") or ""
    if prov.startswith("opencode") or prov.startswith("zen"):
        return ("go", mid in cat["go"])
    if prov in ("nim_local", "nim", "nvidia"):
        return ("nim", mid in cat["nim"])
    if prov in ("openrouter", "or", "c7"):
        return ("or", mid in cat["or"])
    if prov in ("cerebras", "google", "google_c2", "google_c3", "google_c4", "google_c5", "google_c6"):
        return (prov, None)  # proveedor externo: no catálogo aquí
    return (prov or "?", None)


def skills_scan(cat):
    """Lista completa de ids citados en skills que no existen en ningún catálogo vivo."""
    all_ids = cat["go"] | cat["nim"] | cat["or"]
    known_bare = {i.split("/")[-1].split(":")[0] for i in all_ids}
    hits = []
    skills_dir = Path("~/.hermes/skills")
    files = list(skills_dir.rglob("SKILL.md"))
    for f in files:
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        for m in re.finditer(r"\b([a-z0-9][a-z0-9._-]{1,40}/[a-z0-9][a-z0-9._:-]{2,60})\b", txt):
            tok = m.group(1)
            if tok.startswith(("http", "www", "memory-bank", "SCRIPTS", "providers", "design-")):
                continue
            if "/" not in tok or tok.count("/") != 1:
                continue
            if tok in all_ids:
                continue
            if tok.split("/")[1].split(":")[0] in known_bare:
                continue
            # heurística: parece id de modelo si el vendor está en una lista conocida
            vendor = tok.split("/")[0]
            if vendor in {"nvidia", "google", "deepseek-ai", "z-ai", "moonshotai", "minimaxai",
                          "mistralai", "openai", "meta", "cohere", "poolside", "stepfun-ai",
                          "writer", "snowflake", "ibm", "ai21labs", "bigcode", "databricks",
                          "liquid", "recursive", "stealth", "xiaomi", "inclusionai", "xingchen-agi",
                          "dots-studio", "cerebras", "anthropic", "moonshot"}:
                hits.append({"skill": str(f).replace(str(skills_dir) + "/", ""), "id": tok,
                             "line": txt[:m.start()].count("\n") + 1})
    return hits


def main():
    cat = live_catalogs()
    refs = collect_refs(cat)
    resolved = []
    for r in refs:
        src, exists = resolve(r, cat)
        resolved.append({**r, "source": src, "exists": exists,
                         "verdict": "OK" if exists else ("NO_VERIFICADO" if exists is None else "NO_EXISTE")})

    allow = [r for r in resolved if r["consumer"] == "c7_allowlist"]
    allow_rot = [r for r in allow if r["exists"] is False]
    allow_ok = [r for r in allow if r["exists"] is True]

    # gramática de nombres
    names = [r for r in resolved if r.get("name")]
    conform = re.compile(r"^\[(OK|DEGRADED|RETIRED)\]\[[0-9]+[kM]\]\[(GO|F)\]\s")
    bad_names = [r for r in names if not conform.match(r["name"] or "")]

    skills_bad = skills_scan(cat)

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "catalogs": {"go": len(cat["go"]), "nim": len(cat["nim"]),
                     "openrouter_total": len(cat["or"]), "openrouter_free": len(cat["or_free"])},
        "openrouter_free_ids": sorted(cat["or_free"]),
        "refs_total": len(resolved),
        "refs_missing": sorted({(r["consumer"], r["id"]) for r in resolved if r["exists"] is False}),
        "refs_unverified": sorted({(r["consumer"], r["id"]) for r in resolved if r["exists"] is None}),
        "allowlist": {"total": len(allow), "ok": len(allow_ok), "rotten": [r["id"] for r in allow_rot]},
        "names": {"total": len(names), "conforming": len(names) - len(bad_names),
                  "nonconforming": len(bad_names),
                  "sample": [{"consumer": r["consumer"], "id": r["id"], "name": r["name"]} for r in bad_names[:12]]},
        "skill_model_ids_not_in_catalog": skills_bad,
    }
    (OUT / "freshness_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("catalogs", "refs_total", "allowlist", "names")}, indent=1))
    print("refs_missing:", len(report["refs_missing"]), report["refs_missing"][:12])
    print("skills_bad:", len(skills_bad), skills_bad[:10])


if __name__ == "__main__":
    main()
