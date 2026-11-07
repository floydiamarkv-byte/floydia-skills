#!/usr/bin/env python3
"""F1 — Inventario con sonda realista: tools (3/3), visión y trampa aritmética.

Escribe out/f1_probe.json (clave "<source>:<id>") y out/f1_probe.jsonl.
No aplica nada: alimenta el registro de estado (§8).
"""
from __future__ import annotations

import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIX = ROOT / "fixtures"
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
PROJ = Path("<PROYECTO>")
sys.path.insert(0, str(PROJ / "SCRIPTS"))
from env_loader import load_env  # noqa: E402

ENV = load_env()
GO_URL = "https://opencode.ai/inference/go/openai/v1/chat/completions"
NIM_URL = "http://127.0.0.1:8088/v1/chat/completions"
GO_H = {"Authorization": "Bearer " + ENV["C7_OPENCODE_GO"], "Content-Type": "application/json",
        "User-Agent": "opencode/1.4.9 (linux x64)", "x-opencode-session": "hp15-f1"}

# (source, id, ¿declara visión?)
TARGETS = [
    ("opencode_go", "deepseek-v4-pro", False),
    ("opencode_go", "deepseek-v4.1-flash", False),
    ("opencode_go", "glm-5.3-flash", False),
    ("opencode_go", "gemini-4-argon", True),
    ("opencode_go", "kimi-k3.1-pro", False),
    ("nim", "nvidia/nemotron-3.5-lightning-30b-a3b", False),
    ("nim", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", True),
    ("nim", "nvidia/nemotron-3-ultra-550b-a55b", False),
    ("nim", "google/diffusiongemma-26b-a4b-it", True),
    ("nim", "z-ai/glm-5.3-flash", False),
    ("nim", "nvidia/nemotron-3.5-bolt-e4b", False),
]

TOOLS = [
    {"type": "function", "function": {"name": "get_title", "description": "Título de una URL",
     "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "get_h1", "description": "H1 de una URL",
     "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "get_status", "description": "HTTP status de una URL",
     "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
]

TRAP = ("Un coche recorre 20 km en 3 minutos. ¿Cuál es su velocidad media en km/h? "
        "Responde SOLO con el número entero.")


def call(source, model, messages, tools=None, max_tokens=600, timeout=None):
    body = {"model": model, "messages": messages, "max_tokens": max_tokens,
            "temperature": 0, "seed": 42}
    if tools:
        body["tools"] = tools
    url = GO_URL if source == "opencode_go" else NIM_URL
    headers = GO_H if source == "opencode_go" else {"Content-Type": "application/json"}
    timeout = timeout or (150 if source == "opencode_go" else 190)
    t0 = time.time()
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(),
                                                               headers=headers), timeout=timeout) as r:
                return {"ok": True, "ms": int((time.time() - t0) * 1000), "json": json.load(r), "attempt": attempt}
        except Exception as e:  # noqa: BLE001
            try:
                detail = e.read().decode()[:200]  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                detail = str(e)
            if attempt == 2:
                return {"ok": False, "ms": int((time.time() - t0) * 1000), "error": f"{type(e).__name__}: {detail}"}
            time.sleep(2)


def msg_of(r):
    try:
        return r["json"]["choices"][0]["message"]
    except Exception:  # noqa: BLE001
        return {}


def probe(source, model, vision_expected=True):
    key = f"{source}:{model}"
    rec = {"id": model, "source": source, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    r = call(source, model, [{"role": "user", "content":
             "Llama a las TRES herramientas para https://kuamikiachi.example/ (title, h1 y status) en este turno."}], TOOLS)
    m = msg_of(r)
    calls = m.get("tool_calls") or []
    ok_calls = 0
    names = set()
    for c in calls:
        try:
            json.loads(c["function"]["arguments"])
            names.add(c["function"]["name"])
            ok_calls += 1
        except Exception:  # noqa: BLE001
            pass
    rec.update({"tools_ok": r["ok"], "tools": ok_calls, "tools_names": sorted(names),
                "tools_ms": r["ms"], "tools_error": r.get("error")})

    if not vision_expected:
        rec.update({"vision_ok": None, "vision": False, "vision_ms": None,
                    "vision_text": "", "vision_error": "no_declara_vision_no_probado"})
        r = {"ok": False, "ms": 0}
    else:
        b64 = base64.b64encode((FIX / "metrics.png").read_bytes()).decode()
        r = call(source, model, [{"role": "user", "content": [
            {"type": "text", "text": "Lee las tres cifras de la imagen. Devuelve solo los tres números separados por coma."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}]}], None, 200, timeout=75)
    txt = (msg_of(r).get("content") or "")
    vision = bool(r["ok"] and ("1874" in txt) and ("148" in txt) and ("0.021" in txt or "0,021" in txt))
    if vision_expected:
        rec.update({"vision_ok": r["ok"], "vision": vision, "vision_ms": r["ms"],
                    "vision_text": txt[:120], "vision_error": r.get("error")})

    r = call(source, model, [{"role": "user", "content": TRAP}], None, 6000, timeout=240)
    txt = (msg_of(r).get("content") or "").strip()
    rec.update({"trap_ok": r["ok"], "trap_text": txt[:80], "trap_correct": "400" in txt,
                "trap_ms": r["ms"], "trap_error": r.get("error")})
    rec["estado"] = "ACTIVE" if (rec["tools_ok"] or rec["vision_ok"] or rec["trap_ok"]) else "DEGRADED"
    return key, rec


def main():
    store = {}
    jl = OUT / "f1_probe.jsonl"
    only = sys.argv[1] if len(sys.argv) > 1 else None
    with jl.open("a", encoding="utf-8") as fh:
        for source, model, vis in TARGETS:
            if only and only not in model:
                continue
            key, rec = probe(source, model, vis)
            store[key] = rec
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"{source:12s} {model:52s} tools={rec['tools']}/3 vision={int(bool(rec['vision']))} "
                  f"trap={int(bool(rec['trap_correct']))} ({rec['tools_ms']}/{rec['vision_ms']}/{rec['trap_ms']} ms)",
                  flush=True)
    p = OUT / "f1_probe.json"
    if p.exists():
        old = json.loads(p.read_text())
        old.update(store)
        store = old
    p.write_text(json.dumps(store, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(store)} modelos en {p}")


if __name__ == "__main__":
    main()
