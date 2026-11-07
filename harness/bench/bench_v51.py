#!/usr/bin/env python3
"""Harness FloydIA v5.1 — banco congelado de 8 tareas web/SEO (GO vs FREE).

Determinista: temperature=0, seed fija, fixtures generados en disco, mismos bytes
para ambos modos. Escribe JSONL incremental en out/bench.jsonl y resumen en
out/summary.json. No toca SSOT: todo vive en scratch/harness_v51/.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIX = ROOT / "fixtures"
OUT = ROOT / "out"
OUT.mkdir(parents=True, exist_ok=True)
FIX.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, "<PROYECTO>/SCRIPTS")
from env_loader import load_env  # noqa: E402

ENV = load_env()
GO_KEY = ENV["C7_OPENCODE_GO"]
GO_URL = "https://opencode.ai/inference/go/openai/v1/chat/completions"
NIM_URL = "http://127.0.0.1:8088/v1/chat/completions"
GO_HEADERS = {
    "Authorization": "Bearer " + GO_KEY,
    "Content-Type": "application/json",
    "User-Agent": "opencode/1.4.9 (linux x64)",
    "x-opencode-session": "hp15-v51-bench",
}

# ── presupuesto / circuito ────────────────────────────────────────────────
WINDOW_5H_USD = 12.0
CAP_F3_USD = 0.20 * WINDOW_5H_USD   # §11: F3 ≤ 20 % ventana 5 h
SPENT = {"allowance_usd": 0.0, "requests": 0, "errors": 0}


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── fixtures ──────────────────────────────────────────────────────────────
HERO_TOKENS = {
    "bg": "#0B1220",
    "fg": "#F5F7FA",
    "accent": "#1F8FFF",
    "radius": "14px",
    "maxw": "1120px",
}

CLS_HTML = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Taller Kuamikiachi</title>
<link rel="preload" href="/fonts/inter.woff2" as="font" crossorigin>
<style>@font-face{font-family:Inter;src:url(/fonts/inter.woff2) format("woff2")}
body{font-family:Inter,sans-serif;margin:0}.hero{display:grid;gap:1rem}</style></head>
<body><section class="hero"><h1>Taller mecánico en Caracas</h1>
<img src="/img/hero-1600.jpg" alt="Taller">
<p>Diagnóstico computarizado y mantenimiento preventivo.</p>
<img src="/img/banner-promo.jpg" alt="Promoción">
<button>Agendar cita</button>
<img src="/img/logo-cliente.svg" alt="Logo"></section></body></html>"""

AUDIT_HTML = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Servicio de frenos ABS en Caracas | Taller Kuamikiachi</title>
<meta name="description" content="Servicio de frenos ABS en Caracas con diagnóstico computarizado, repuestos originales y garantía de 90 días. Agenda hoy mismo tu cita.">
<link rel="canonical" href="https://kuamikiachi.example/frenos-abs">
<meta name="robots" content="noindex,follow">
<meta property="og:title" content="Frenos ABS">
</head><body>
<h1>Servicio de frenos ABS</h1>
<h2>Diagnóstico computarizado</h2>
<h3>Precios</h3>
<img src="/img/frenos.jpg">
<p>Texto de relleno.</p>
<a href="/contacto">Contacto</a>
<a href="https://kuamikiachi.example/contacto">Contacto</a>
<h1>Segundo H1 innecesario</h1>
</body></html>"""

CSS_IN = """.btn { color:#fff; background:#1F8FFF; padding:12px 20px; border-radius:14px; }
.card { padding:16px; border-radius:14px; background:#fff; }
.btn { background:#1F8FFF; color:#fff; }
.card { border-radius:14px; padding:16px; }
.hero__title { font-size:2.25rem; line-height:1.15; color:#0B1220; }
.hero__title { color:#0B1220; font-size:2.25rem; }
@media (max-width:768px){ .hero__title { font-size:1.75rem; } }
"""

VOLUMES = [
    {"kw": "frenos abs caracas", "volume": 24900, "kd": 38},
    {"kw": "taller mecanico caracas", "volume": 8100, "kd": 44},
    {"kw": "cambio de pastillas de freno", "volume": 5400, "kd": 22},
    {"kw": "diagnostico computarizado auto", "volume": 3600, "kd": 31},
    {"kw": "reparacion abs precio", "volume": 1900, "kd": 17},
]
TOTAL_VOL = sum(v["volume"] for v in VOLUMES)

AUDIT_GOLD = {
    "title_len_ok": True,       # 61 chars → fuera de 50-60 → False
    "meta_len_ok": True,
    "h1_unique": False,
    "single_h1": False,
    "canonical_present": True,
    "canonical_unique": True,
    "robots_indexable": False,  # noindex
    "img_alt": False,
    "img_dimensions": False,
    "og_title": True,
    "og_image": False,
    "structured_data": False,
    "internal_links_abs": False,
    "heading_order": False,     # h3 tras h2 sin h2->h3 lógico (h3 Precios)
    "lang_attr": True,
    "https_links": True,
}

PAGE_METRICS = {
    "https://kuamikiachi.example/": 1874,
    "https://kuamikiachi.example/frenos-abs": 2210,
    "https://kuamikiachi.example/contacto": 1650,
    "https://kuamikiachi.example/blog/": 1990,
    "https://kuamikiachi.example/tienda/": 2400,
}
SUM_LCP = sum(PAGE_METRICS.values())


def build_fixtures() -> dict:
    from PIL import Image, ImageDraw

    (FIX / "cls.html").write_text(CLS_HTML, encoding="utf-8")
    (FIX / "audit.html").write_text(AUDIT_HTML, encoding="utf-8")
    (FIX / "styles.css").write_text(CSS_IN, encoding="utf-8")
    (FIX / "volumes.json").write_text(json.dumps(VOLUMES, ensure_ascii=False, indent=1), encoding="utf-8")
    img = Image.new("RGB", (460, 200), "white")
    d = ImageDraw.Draw(img)
    d.text((18, 20), "LCP: 1874 ms", fill="black")
    d.text((18, 80), "CLS: 0.021", fill="black")
    d.text((18, 140), "INP: 148 ms", fill="black")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    (FIX / "metrics.png").write_bytes(buf.getvalue())
    sha = {}
    for p in sorted(FIX.iterdir()):
        sha[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    (FIX / "SHA256SUMS.json").write_text(json.dumps(sha, indent=1), encoding="utf-8")
    return sha


# ── transporte ────────────────────────────────────────────────────────────
def call(mode: str, model: str, messages, tools=None, max_tokens=1200, timeout=None):
    body = {"model": model, "messages": messages, "max_tokens": max_tokens,
            "temperature": 0, "seed": 42}
    if tools:
        body["tools"] = tools
    url = GO_URL if mode == "GO" else NIM_URL
    headers = dict(GO_HEADERS) if mode == "GO" else {"Content-Type": "application/json"}
    if timeout is None:
        timeout = 120 if mode == "GO" else 190
    t0 = time.time()
    for attempt in (1, 2):           # R4: segunda llamada antes de declarar muerto
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            ms = int((time.time() - t0) * 1000)
            return {"ok": True, "ms": ms, "attempt": attempt, "json": d}
        except Exception as e:  # noqa: BLE001
            detail = ""
            try:
                detail = e.read().decode()[:300]  # type: ignore[attr-defined]
            except Exception:                 # noqa: BLE001
                detail = str(e)
            if attempt == 2:
                return {"ok": False, "ms": int((time.time() - t0) * 1000),
                        "attempt": attempt, "error": f"{type(e).__name__}: {detail}"}
            time.sleep(2)


def text_of(resp) -> str:
    try:
        m = resp["json"]["choices"][0]["message"]
        return (m.get("content") or "").strip()
    except Exception:  # noqa: BLE001
        return ""


def usage_of(resp) -> dict:
    try:
        u = resp["json"].get("usage") or {}
        oc = u.get("opencode") or {}
        return {"prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
                "list_cost": oc.get("list_cost"), "allowance": oc.get("allowance"),
                "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens")}
    except Exception:  # noqa: BLE001
        return {}


def json_block(s: str):
    """Extrae el primer objeto/array JSON válido del texto."""
    s = s.strip()
    s = re.sub(r"^```(?:json|html|css)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    for pat in (r"\{.*\}", r"\[.*\]"):
        m = re.search(pat, s, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:  # noqa: BLE001
                continue
    return None


# ── graders ───────────────────────────────────────────────────────────────
def g_hero(txt):
    t = txt.lower()
    checks = {
        "html_doc": "<!doctype html" in t or "<html" in t,
        "single_h1": len(re.findall(r"<h1[\s>]", t)) == 1,
        "media_query": "@media" in t,
        "tokens": sum(1 for v in ("#0b1220", "#1f8fff", "#f5f7fa") if v in t) >= 3,
        "cta_link": bool(re.search(r"<a[^>]+href=", t)),
        "no_js": "<script" not in t,
        "bounded": len(txt) < 14000,
    }
    return {"pass": sum(checks.values()) >= 6, "score": sum(checks.values()), "detail": checks}


def g_cls(txt):
    imgs = re.findall(r"<img[^>]*>", txt, re.I)
    dims = sum(1 for i in imgs if re.search(r'width\s*=', i) and re.search(r'height\s*=', i)
               or "aspect-ratio" in i)
    checks = {
        "has_imgs": len(imgs) >= 3,
        "all_dimensioned": len(imgs) >= 3 and dims == len(imgs),
        "font_display": "font-display" in txt and "swap" in txt,
        "preload_kept": "preload" in txt,
    }
    return {"pass": checks["all_dimensioned"] and checks["font_display"],
            "score": sum(checks.values()), "detail": {**checks, "imgs": len(imgs), "dimensioned": dims}}


def g_schema(txt):
    data = json_block(txt)
    if not data:
        return {"pass": False, "score": 0, "detail": {"json": False}}
    nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
    types = {n.get("@type") for n in nodes if isinstance(n, dict)}
    prod = next((n for n in nodes if isinstance(n, dict) and n.get("@type") == "Product"), {})
    bc = next((n for n in nodes if isinstance(n, dict) and n.get("@type") == "BreadcrumbList"), {})
    off = prod.get("offers") or {}
    if isinstance(off, list):
        off = off[0] if off else {}
    items = bc.get("itemListElement") or []
    checks = {
        "product": bool(prod),
        "breadcrumb": bool(bc),
        "name": bool(prod.get("name")),
        "sku": str(prod.get("sku") or "") == "KUA-ABS-01",
        "price": str(off.get("price")) in ("19.99", "19.990", "19.9"),
        "currency": off.get("priceCurrency") == "USD",
        "availability": "InStock" in str(off.get("availability") or ""),
        "crumbs_ge_2": len(items) >= 2 and all("position" in i and "item" in i for i in items),
    }
    return {"pass": all(checks.values()), "score": sum(checks.values()), "detail": {**checks, "types": sorted(map(str, types))}}


def g_audit(txt):
    data = json_block(txt)
    if not isinstance(data, list):
        return {"pass": False, "score": 0, "detail": {"json_list": False}}
    got = {}
    for it in data:
        if isinstance(it, dict):
            k = str(it.get("id") or it.get("requisito") or it.get("requirement") or "").strip().lower()
            v = it.get("pass", it.get("ok", it.get("cumple")))
            if isinstance(v, str):
                v = v.strip().lower() in ("true", "si", "sí", "yes", "ok", "pasa")
            if k:
                got[k] = bool(v)
    hits = sum(1 for k, v in AUDIT_GOLD.items() if got.get(k) == v)
    return {"pass": len(data) == 16 and hits >= 14, "score": hits,
            "detail": {"items": len(data), "matched": hits, "missing": [k for k in AUDIT_GOLD if k not in got]}}


def g_brief(txt):
    nums = set(re.findall(r"\b\d{1,3}(?:[.,]\d{3})+\b|\b\d{4,6}\b", txt))
    norm = {n.replace(".", "").replace(",", "") for n in nums}
    order_ok = bool(re.search(r"frenos abs caracas[\s\S]{0,120}taller mecanico caracas[\s\S]{0,120}cambio de pastillas", txt, re.I))
    checks = {"total_exact": str(TOTAL_VOL) in norm, "top1": "frenos abs caracas" in txt.lower(),
              "order": order_ok}
    return {"pass": checks["total_exact"] and checks["top1"], "score": sum(checks.values()), "detail": checks}


def css_map(s: str):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    out = {}
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", s):
        sel = " ".join(sel.split())
        props = out.setdefault(sel, {})
        for decl in body.split(";"):
            if ":" in decl:
                k, v = decl.split(":", 1)
                props[k.strip().lower()] = " ".join(v.split()).lower().rstrip(";")
    return out


def g_css(txt):
    out = css_map(txt)
    base = css_map(CSS_IN)
    same = out == base
    checks = {"parses": bool(out), "same_declarations": same,
              "selectors_kept": set(base) <= set(out),
              "no_extra_sel": set(out) <= set(base)}
    return {"pass": same, "score": sum(checks.values()), "detail": {**checks, "selectors": len(out)}}


def g_vision(txt):
    n = txt.replace(",", ".") if txt.count(",") == 2 and "." not in txt else txt
    ok = ("1874" in txt) and (("0.021" in txt) or ("0,021" in txt)) and ("148" in txt)
    return {"pass": ok, "score": int(ok), "detail": {"raw": txt[:200]}}


def g_tools(record):
    calls = record["tool_calls"]
    valid = 0
    for c in calls:
        try:
            args = json.loads(c["function"]["arguments"])
            if c["function"]["name"] == "get_page_metrics" and args.get("url") in PAGE_METRICS:
                valid += 1
        except Exception:  # noqa: BLE001
            pass
    answer_ok = str(SUM_LCP) in record["final_text"].replace(".", "").replace(",", "")
    checks = {"five_calls": valid >= 5, "schema_ok": valid == len(calls) and valid > 0,
              "sum_exact": answer_ok}
    return {"pass": all(checks.values()), "score": sum(checks.values()),
            "detail": {**checks, "calls": len(calls), "valid": valid}}


# ── tareas ────────────────────────────────────────────────────────────────
SYS = ("Eres un ingeniero front-end y SEO técnico. Respondes SOLO con el artefacto pedido, "
       "sin explicaciones ni markdown extra cuando se pida código o JSON.")

TASKS = [
    {
        "id": "T1_hero",
        "model": {"GO": "deepseek-v4.1-flash", "FREE": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"},
        "max_tokens": 2000,
        "prompt": ("Genera un hero responsive en un único fichero HTML+CSS embebido para un taller mecánico "
                   "en Caracas. Tokens obligatorios: fondo {bg}, texto {fg}, acento {accent}, radio {radius}, "
                   "ancho máximo {maxw}. Debe tener exactamente un <h1>, un CTA <a href>, y una media query "
                   "para <=768px. Sin JavaScript. Devuelve solo el HTML.").format(**HERO_TOKENS),
        "grader": lambda r: g_hero(r["text"]),
    },
    {
        "id": "T2_cls",
        "model": {"GO": "deepseek-v4.1-flash", "FREE": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"},
        "max_tokens": 2200,
        "prompt": ("Corrige este HTML para eliminar el CLS: todas las <img> deben reservar espacio "
                   "(width+height o aspect-ratio) y la fuente debe usar font-display swap. Conserva el "
                   "contenido y el preload. Devuelve solo el HTML corregido.\n\n" + CLS_HTML),
        "grader": lambda r: g_cls(r["text"]),
    },
    {
        "id": "T3_schema",
        "model": {"GO": "deepseek-v4.1-flash", "FREE": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"},
        "max_tokens": 1200,
        "prompt": ("Devuelve un único bloque JSON-LD (sin HTML alrededor) con @graph que contenga un Product "
                   "y un BreadcrumbList para: nombre 'Kit de frenos ABS', sku KUA-ABS-01, precio 19.99 USD, "
                   "disponibilidad InStock, marca 'Kuamikiachi'. Breadcrumb: Inicio > Frenos > Kit ABS, con "
                   "positions 1..3 y item como URL absoluta https://kuamikiachi.example/..."),
        "grader": lambda r: g_schema(r["text"]),
    },
    {
        "id": "T4_onpage",
        "model": {"GO": "deepseek-v4.1-flash", "FREE": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"},
        "max_tokens": 1800,
        "prompt": ("Audita on-page este HTML con EXACTAMENTE estas 16 claves y valores booleanos en un array "
                   "JSON de objetos {\"id\":..., \"pass\":true|false}: title_len_ok (50-60 chars), meta_len_ok "
                   "(120-155), h1_unique, single_h1, canonical_present, canonical_unique, robots_indexable, "
                   "img_alt, img_dimensions, og_title, og_image, structured_data, internal_links_abs, "
                   "heading_order, lang_attr, https_links. Sin texto adicional.\n\n" + AUDIT_HTML),
        "grader": lambda r: g_audit(r["text"]),
    },
    {
        "id": "T5_brief",
        "model": {"GO": "deepseek-v4-pro", "FREE": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"},
        "max_tokens": 900,
        "prompt": ("Con estos volúmenes REALES (no inventes otros), escribe un brief SEO de 6 líneas que "
                   "incluya el volumen total exacto y el orden de las 3 keywords por volumen descendente. "
                   "Cita las cifras tal cual.\n\n" + json.dumps(VOLUMES, ensure_ascii=False)),
        "grader": lambda r: g_brief(r["text"]),
    },
    {
        "id": "T6_css",
        "model": {"GO": "glm-5.3-flash", "FREE": "nvidia/nemotron-3.5-lightning-30b-a3b"},
        "max_tokens": 1200,
        "prompt": ("Refactoriza este CSS eliminando duplicados sin cambiar NINGUNA declaración efectiva "
                   "(mismo selector -> mismas propiedades y valores, incluida la media query). Devuelve solo "
                   "el CSS.\n\n" + CSS_IN),
        "grader": lambda r: g_css(r["text"]),
    },
    {
        "id": "T7_vision",
        "model": {"GO": "gemini-4-argon", "FREE": "google/diffusiongemma-26b-a4b-it"},
        "max_tokens": 200,
        "vision": True,
        "prompt": "Lee las tres métricas de la imagen y devuélvelas separadas por coma, en orden, sin texto extra.",
        "grader": lambda r: g_vision(r["text"]),
    },
    {
        "id": "T8_tools",
        "model": {"GO": "glm-5.3-flash", "FREE": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"},
        "max_tokens": 500,
        "tools": True,
        "prompt": ("Consulta con la herramienta get_page_metrics cada una de estas 5 URLs, una por turno: "
                   + ", ".join(PAGE_METRICS) +
                   ". Cuando tengas las 5, responde SOLO con la suma total de LCP en ms (número entero)."),
        "grader": None,  # se evalúa tras el bucle
    },
]

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_page_metrics",
        "description": "Devuelve el LCP en ms de una URL del sitio",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    },
}]


def run_task(mode: str, task: dict, rep: int, cold: bool) -> dict:
    override = json.loads(os.environ.get("OVERRIDE_JSON") or "{}")
    tscale = float(os.environ.get("TOKENS_SCALE", "1"))
    task = dict(task)
    if task["id"] in override and mode in override[task["id"]]:
        task["model"] = dict(task["model"])
        task["model"][mode] = override[task["id"]][mode]
    task["max_tokens"] = int(task["max_tokens"] * tscale)
    model = task["model"][mode]
    rec = {"ts": now(), "mode": mode, "task": task["id"], "model": model, "rep": rep,
           "phase": "cold" if cold else "hot", "vision": bool(task.get("vision")),
           "tools": bool(task.get("tools"))}
    if task.get("vision"):
        b64 = base64.b64encode((FIX / "metrics.png").read_bytes()).decode()
        messages = [{"role": "system", "content": SYS},
                    {"role": "user", "content": [
                        {"type": "text", "text": task["prompt"]},
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}]}]
    else:
        messages = [{"role": "system", "content": SYS}, {"role": "user", "content": task["prompt"]}]

    if task.get("tools"):
        calls, transcript = [], list(messages)
        for step in range(7):
            r = call(mode, model, transcript, tools=TOOLS, max_tokens=task["max_tokens"])
            if not r["ok"]:
                rec.update({"ok": False, "error": r.get("error"), "ms": r["ms"]})
                rec["tool_calls"] = []
                rec["final_text"] = ""
                rec["grade"] = g_tools(rec)
                return rec
            m = r["json"]["choices"][0]["message"]
            tc = m.get("tool_calls") or []
            transcript.append(m)
            if tc:
                for c in tc:
                    calls.append(c)
                    try:
                        url = json.loads(c["function"]["arguments"]).get("url")
                    except Exception:  # noqa: BLE001
                        url = None
                    val = PAGE_METRICS.get(url)
                    transcript.append({"role": "tool", "tool_call_id": c["id"],
                                       "content": json.dumps({"url": url, "lcp_ms": val})})
            else:
                rec["final_text"] = (m.get("content") or "").strip()
                break
        rec.update({"ok": True, "ms": 0, "tool_calls": calls, "steps": step + 1})
        rec["grade"] = g_tools(rec)
        return rec

    r = call(mode, model, messages, max_tokens=task["max_tokens"])
    rec["ms"] = r["ms"]
    rec["attempt"] = r.get("attempt")
    if not r["ok"]:
        rec.update({"ok": False, "error": r.get("error"), "grade": {"pass": False, "score": 0, "detail": {"transport": False}}})
        return rec
    txt = text_of(r)
    rec.update({"ok": True, "text_preview": txt[:4000], "text_full": txt, "full_chars": len(txt),
                "usage": usage_of(r)})
    if mode == "GO":
        SPENT["allowance_usd"] += float((rec["usage"] or {}).get("allowance") or 0.0)
    rec["grade"] = task["grader"]({"text": txt, "tool_calls": [], "final_text": txt})
    return rec


def main():
    reps = int(os.environ.get("REPS", "3"))
    only = os.environ.get("ONLY", "")
    sha = build_fixtures()
    meta = {"started_at": now(), "reps": reps, "fixtures_sha": sha,
            "cap_usd": CAP_F3_USD, "tasks": [t["id"] for t in TASKS],
            "models": {t["id"]: t["model"] for t in TASKS}}
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")

    plan = []
    for mode in ("GO", "FREE"):
        for t in TASKS:
            if only and only not in t["id"]:
                continue
            for rep in range(1, reps + 1):
                plan.append((mode, t, rep))
    random.Random(20261106).shuffle(plan)

    seen = set()
    rows = []
    jl = OUT / f"bench_{os.environ.get('TAG','run')}.jsonl"
    with jl.open("w", encoding="utf-8") as fh:
        for mode, task, rep in plan:
            if SPENT["allowance_usd"] >= CAP_F3_USD:
                rec = {"ts": now(), "mode": mode, "task": task["id"], "rep": rep, "ok": False,
                       "error": "CIRCUIT_BREAKER_CAP_F3", "grade": {"pass": False, "score": 0}}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); fh.flush(); rows.append(rec)
                continue
            key = (mode, task["id"], task["model"][mode])
            cold = key not in seen
            seen.add(key)
            t0 = time.time()
            rec = run_task(mode, task, rep, cold)
            rec["wall_s"] = round(time.time() - t0, 2)
            SPENT["requests"] += 1
            if not rec.get("ok"):
                SPENT["errors"] += 1
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); fh.flush()
            rows.append(rec)
            print(f"{mode:4s} {task['id']:10s} r{rep} {rec.get('ms',0):6d}ms "
                  f"{'PASS' if rec['grade']['pass'] else 'FAIL'} "
                  f"{rec['grade']['score']}/{len(rec['grade'].get('detail') or {}) or '-'}", flush=True)

    summary = summarise(rows)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"spent_allowance_usd": round(SPENT["allowance_usd"], 6),
                      "requests": SPENT["requests"], "errors": SPENT["errors"],
                      "jsonl": str(jl)}, indent=1))


def summarise(rows):
    by = {}
    for r in rows:
        by.setdefault((r["mode"], r["task"]), []).append(r)
    out = {"generated_at": now(), "cells": [], "totals": {}}
    for (mode, task), rs in sorted(by.items()):
        passes = [r for r in rs if r.get("grade", {}).get("pass")]
        lat = sorted(r.get("ms") or 0 for r in rs if r.get("ok"))
        cost = sum(float((r.get("usage") or {}).get("allowance") or 0) for r in rs)
        out["cells"].append({
            "mode": mode, "task": task, "model": rs[0].get("model"), "reps": len(rs),
            "pass": len(passes), "pass_rate": round(len(passes) / len(rs), 3),
            "latency_ms_p50": lat[len(lat) // 2] if lat else None,
            "latency_ms_max": lat[-1] if lat else None,
            "allowance_usd": round(cost, 8), "errors": sum(1 for r in rs if not r.get("ok")),
        })
    modes = {}
    for mode in ("GO", "FREE"):
        cells = [c for c in out["cells"] if c["mode"] == mode]
        modes[mode] = {
            "tasks_passed_strict": sum(1 for c in cells if c["pass"] == c["reps"]),
            "tasks_passed_any": sum(1 for c in cells if c["pass"] > 0),
            "cells": len(cells),
            "allowance_usd": round(sum(c["allowance_usd"] for c in cells), 8),
            "errors": sum(c["errors"] for c in cells),
        }
    out["totals"] = modes
    return out


if __name__ == "__main__":
    main()
