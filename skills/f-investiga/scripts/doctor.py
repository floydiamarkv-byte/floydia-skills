#!/usr/bin/env python3
"""doctor.py — Capa 1: inventario de herramientas de investigación.

PRINCIPIO RECTOR
================
"No confundas archivos encontrados con herramientas instaladas, ni configuración
con funcionamiento comprobado."

SEIS ESTADOS (nunca binarios)
=============================
  ENCONTRADO  el archivo/binario existe
  CONFIGURADO la variable está definida (se reporta SOLO EL NOMBRE)
  PROBADO     se ejecutó una consulta mínima real y respondió
  PROBADO_CON_INTERMITENCIA  responde, pero solo en parte de los intentos
                              (medido: DuckDuckGo ~1 de cada 4)
  FALLA       configurado pero la prueba mínima falla
  ARCHIVADO   existe en _archive, fuera del catálogo
  AUSENTE     no se encuentra

SEGURIDAD
=========
  - NUNCA lee ni imprime el VALOR de una variable. Solo nombre + booleano.
  - NUNCA escribe fuera de `runs/<slug>/`.
  - Las pruebas de red son pasivas y acotadas (timeout duro).

USO
===
    python3 doctor.py --workspace /home/tec/Dropbox/ANTIGRAVITY_PROJECTS
    python3 doctor.py --json-only
    python3 doctor.py --no-network
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ENCONTRADO, CONFIGURADO, PROBADO, FALLA, ARCHIVADO, AUSENTE = (
    "ENCONTRADO", "CONFIGURADO", "PROBADO", "FALLA", "ARCHIVADO", "AUSENTE")

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"

# Un HTTP 200 con cuerpo trivial NO es una fuente funcional. Medido 2026-09-28:
# X syndication responde 200 con cuerpo vacio -> inutil aunque "no falle".
MIN_USEFUL_BYTES = 200
# Suficiente para decidir si es JSON sin truncar respuestas grandes
# (OpenRouter /models ~750 KB: truncar a 400 KB rompe el parseo completo).
MAX_BYTES = 2_000_000


# ---------------------------------------------------------------- utilidades

def probe_http(url: str, timeout: int = 12, method: str = "GET",
               headers: dict | None = None, expect_json: bool = False) -> dict:
    """Sonda HTTP pasiva. NUNCA escribe, NUNCA autenticada salvo que se le pase key."""
    hdrs = {"User-Agent": UA, "Accept": "application/json" if expect_json else "*/*"}
    if headers:
        hdrs.update(headers)
    req = Request(url, method=method, headers=hdrs)
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read(MAX_BYTES)
            status = resp.status
    except HTTPError as exc:
        return {"ok": False, "status": exc.code, "nota": "respuesta HTTP con error"}
    except (URLError, TimeoutError, socket.timeout, OSError) as exc:
        return {"ok": False, "status": None, "nota": type(exc).__name__}

    out = {"ok": 200 <= status < 300, "status": status, "bytes": len(body)}
    if not out["ok"]:
        return out
    # HTTP 200 NO basta: una respuesta vacia o un cuerpo de error no es una
    # fuente funcional. Comprobamos que hay contenido real.
    if len(body) < MIN_USEFUL_BYTES:
        out["ok"] = False
        out["nota"] = f"HTTP {status} pero cuerpo vacio o trivial ({len(body)} B)"
        return out
    if expect_json:
        # NO parseamos el cuerpo entero: algunas respuestas son enormes
        # (OpenRouter ~750 KB) y truncar rompe el JSON. Basta con confirmar
        # que la cabecera del cuerpo es un objeto/array JSON.
        head = body[:MAX_BYTES].lstrip()
        if not head[:1] in (b"{", b"["):
            out["ok"] = False
            out["nota"] = "HTTP 200 pero la respuesta no parece JSON"
    return out


def probe_tcp(host: str, port: int, timeout: int = 4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


# ---------------------------------------------------------------- inventario

def scan_clis() -> list[dict]:
    candidatos = [
        "agy", "gh", "jq", "curl", "chromium", "codex", "claude", "gemini",
        "grok", "kimi", "firecrawl", "crawl4ai", "yt-dlp", "ollama", "nitter",
    ]
    out = []
    for c in candidatos:
        p = shutil.which(c)
        out.append({"tipo": "cli", "nombre": c, "estado": ENCONTRADO if p else AUSENTE,
                    "ruta": p})
    return out


def scan_skills(workspace: Path) -> list[dict]:
    base = workspace / ".agents" / "skills"
    out = []
    if not base.is_dir():
        return [{"tipo": "skill", "nombre": "(directorio)", "estado": AUSENTE}]
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        if d.name == "_archive":
            for a in sorted(d.iterdir()):
                if a.is_dir():
                    out.append({"tipo": "skill", "nombre": f"_archive/{a.name}",
                                "estado": ARCHIVADO,
                                "tiene_skill_md": (a / "SKILL.md").exists()})
            continue
        out.append({"tipo": "skill", "nombre": d.name,
                    "estado": ENCONTRADO if (d / "SKILL.md").exists() else ENCONTRADO,
                    "tiene_skill_md": (d / "SKILL.md").exists()})
    return out


def scan_env() -> list[dict]:
    """SOLO nombres y presencia. Jamás el valor."""
    pat = re.compile(
        r"OPENROUTER|TAVILY|EXA|BRAVE|SERP|FIRECRAWL|XAI|GROK|OPENAI|ANTHROPIC"
        r"|PERPLEXITY|NOTEBOOKLM|REDDIT|JINA|ARENA|ARTIFICIAL|SCRAPECREATORS"
        r"|PARALLEL|APIFY", re.I)
    vault = Path(os.path.expanduser("~/.secrets/antigravity.env"))
    names: set[str] = set()
    if vault.exists():
        try:
            for line in vault.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k = line.split("=", 1)[0].strip()
                    if pat.search(k):
                        names.add(k)
        except OSError:
            pass
    for k in os.environ:
        if pat.search(k):
            names.add(k)
    return [{"tipo": "variable", "nombre": n,
             "estado": CONFIGURADO if os.environ.get(n) else CONFIGURADO,
             "valor_expuesto": False} for n in sorted(names)]


def scan_infra() -> list[dict]:
    out = []
    for label, host, port in [("CT114 Playwright", "192.168.1.238", 3000),
                              ("CT114 FlareSolverr", "192.168.1.238", 8191)]:
        ok = probe_tcp(host, port)
        out.append({"tipo": "infra", "nombre": label,
                    "estado": PROBADO if ok else FALLA,
                    "detalle": f"{host}:{port}"})
    chromium = Path("/usr/bin/chromium")
    if chromium.exists():
        ver = ""
        try:
            ver = subprocess.run([str(chromium), "--version"], capture_output=True,
                                 text=True, timeout=8).stdout.strip()
        except (subprocess.SubprocessError, OSError):
            pass
        out.append({"tipo": "infra", "nombre": "chromium", "estado": PROBADO,
                    "detalle": ver})
    else:
        out.append({"tipo": "infra", "nombre": "chromium", "estado": AUSENTE})
    return out


def scan_sources(network: bool) -> list[dict]:
    """Fuentes HTTP sin clave. Cada una con evidencia real, no de memoria."""
    if not network:
        return [{"tipo": "fuente", "nombre": "(red deshabilitada)", "estado": AUSENTE}]

    specs = [
        ("HN Algolia", "https://hn.algolia.com/api/v1/search?query=test&hitsPerPage=1",
         "signal", True),
        ("OpenRouter models", "https://openrouter.ai/api/v1/models", "precios", True),
        ("LMArena dataset HF", "https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset",
         "rankings", True),
        ("OpenAlex", "https://api.openalex.org/works?search=test&per-page=1", "academico", True),
        ("arXiv", "https://export.arxiv.org/api/query?search_query=all:test&max_results=1",
         "academico", False),
        ("Jina Reader", "https://r.jina.ai/https://example.com", "lectura", False),
        ("Bluesky api.bsky.app", "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=test&limit=1",
         "social", True),
        ("Bluesky public.api (⚠️ rota)", "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=test&limit=1",
         "social", True),
        ("DuckDuckGo html (⚠️ bloqueada)", "https://html.duckduckgo.com/html/?q=test", "busqueda", False),
        ("Reddit .json (⚠️ bloqueada)", "https://www.reddit.com/search.json?q=test&limit=1", "social", True),
        ("Reddit .rss", "https://www.reddit.com/r/LocalLLaMA/.rss", "social", False),
        ("Wikipedia API", "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srsearch=test",
         "academico", True),
        ("X syndication (⚠️ muerta)", "https://cdn.syndication.twimg.com/timeline/profile?screen_name=elonmusk",
         "social", False),
    ]
    out = []
    for name, url, canal, as_json in specs:
        r = probe_http(url, expect_json=as_json)
        estado = PROBADO if r.get("ok") else FALLA
        det = f"HTTP {r.get('status')}"
        if r.get("bytes"):
            det += f", {r['bytes']} B"
        if r.get("nota"):
            det += f" ({r['nota']})"
        out.append({"tipo": "fuente", "nombre": name, "canal": canal,
                    "estado": estado, "url": url, "detalle": det})
    return out


def scan_serper() -> list[dict]:
    """Serper = Google real con CUOTA. La unica fuente que consume.

    Verificado 2026-09-28 con C7_SERPER_API: /search, /news e /images
    responden. El campo `credits: 1` es un CONTADOR POR CONSULTA, no el saldo.
    """
    vault = Path(os.path.expanduser("~/.secrets/antigravity.env"))
    if not vault.exists():
        return [{"tipo": "fuente", "nombre": "Serper (Google, CUOTA)",
                 "estado": AUSENTE}]
    found = None
    try:
        for line in vault.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() in ("C7_SERPER_API", "SERPER_API",
                                 "SERPER_API_KEY", "C7_SERPER") and v.strip():
                    found = k.strip()
                    break
    except OSError:
        pass
    if not found:
        return [{"tipo": "fuente", "nombre": "Serper (Google, CUOTA)",
                 "estado": AUSENTE,
                 "detalle": "sin key (C7_SERPER_API / SERPER_API / ...)"}]
    return [{"tipo": "fuente", "nombre": "Serper (Google, CUOTA)",
             "estado": CONFIGURADO, "canal": "busqueda-web",
             "detalle": f"key via {found}. CONSUME 1 CREDITO por consulta. "
                        f"Usar con cache y solo cuando la keyless no cubra."}]


def scan_web_search_habilitado() -> list[dict]:
    """web_search del harness apunta a la cuenta de CHAT de DeepSeek.

    Verificado 2026-09-28: devuelve HTTP 402 "Insufficient Balance" porque es
    saldo, NO un bug de configuracion. No se puede arreglar sin gasto, asi que
    se registra como conocido y NO como fallo de configuracion, para que nadie
    lo re-diagnostique cada ronda.
    """
    return [{
        "tipo": "herramienta", "nombre": "web_search (DSH)", "estado": FALLA,
        "detalle": "HTTP 402 Insufficient Balance: apunta a api.deepseek.com "
                   "(cuenta de chat, sin saldo). NO es bug de config.",
        "es_bloqueante": False,
        "alternativa": "7 fuentes keyless verificadas (HN, OpenAlex, arXiv, "
                       "Wikipedia, Bluesky, LMArena, Jina Reader). El skill NO "
                       "depende de web_search.",
    }]


def scan_intermitentes(repeticiones: int = 3) -> list[dict]:
    """Detecta fuentes que dependen del humor de la red.

    MEDIDO 2026-09-28 (10+ intentos): DuckDuckGo HTML esta DEGRADADO, no
    bloqueado de forma permanente. Devuelve HTTP 202 con 0 resultados en la
    mayoria de intentos, pero funciono una vez con 40 enlaces. No sirve como
    fuente unica, pero tampoco debe marcarse como 'roto' de forma absoluta.
    """
    out = []
    for name, url, marcador in [
        ("DuckDuckGo html (degradado)", "https://html.duckduckgo.com/html/?q=swarm+research", "uddg="),
        ("Wikipedia API", "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srsearch=test", "totalhits"),
    ]:
        aciertos = 0
        detalle = ""
        for _ in range(repeticiones):
            r = probe_http(url, timeout=12, expect_json=(marcador != "uddg="))
            if marcador == "uddg=":
                try:
                    req = Request(url, headers={"User-Agent": UA})
                    with urlopen(req, timeout=12) as resp:
                        cuerpo = resp.read(400_000).decode("utf-8", "ignore")
                    util = cuerpo.count(marcador)
                    detalle = f"{util} enlaces"
                    if util > 0:
                        aciertos += 1
                except Exception:
                    detalle = "sin respuesta"
            else:
                if r.get("ok"):
                    aciertos += 1
            time.sleep(2)
        ratio = aciertos / repeticiones
        if ratio >= 0.99:
            estado = PROBADO
        elif ratio > 0:
            estado = "PROBADO_CON_INTERMITENCIA"
            detalle = f"acierta {aciertos}/{repeticiones} intentos; {detalle}"
        else:
            estado = FALLA
        out.append({"tipo": "fuente", "nombre": name, "canal": "busqueda",
                    "estado": estado, "url": url, "detalle": detalle})
    return out


def probe_credits(api_key: str, timeout: int = 12) -> dict:
    """Consulta el saldo de una cuenta OpenRouter.

    Funcion propia (no reutiliza probe_http) porque aqui SI necesitamos el
    cuerpo parseado: son unos pocos KB. NUNCA imprime la clave: reporta solo
    los numeros de la cuenta.
    """
    req = Request("https://openrouter.ai/api/v1/credits",
                  headers={"Authorization": f"Bearer {api_key}", "User-Agent": UA,
                           "Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read(200_000).decode() or "{}")
    except HTTPError as exc:
        return {"ok": False, "status": exc.code}
    except (URLError, TimeoutError, socket.timeout, OSError, json.JSONDecodeError):
        return {"ok": False, "status": None}
    d = data.get("data", data)
    tot, used = d.get("total_credits"), d.get("total_usage")
    if not isinstance(tot, (int, float)):
        return {"ok": False, "status": 200, "nota": "respuesta sin total_credits"}
    return {"ok": True, "status": 200, "total": tot,
            "restante": round(tot - (used or 0), 4)}


def scan_openrouter_accounts() -> list[dict]:
    """Consulta /credits por variable. Reporta TOTAL/USADO, nunca la clave."""
    import hashlib
    vault = Path(os.path.expanduser("~/.secrets/antigravity.env"))
    if not vault.exists():
        return []
    env_map: dict[str, str] = {}
    for line in vault.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env_map[k.strip()] = v.strip().strip("'\"")
    os.environ.update({k: v for k, v in env_map.items() if k not in os.environ})

    seen: dict[str, str] = {}
    out = []
    for var in ["C1_OPENROUTER", "C2_OPENROUTER", "C3_OPENROUTER", "C4_OPENROUTER",
                "C5_OPENROUTER", "C6_OPENROUTER", "C7_OPENROUTER", "C9_OPENROUTER",
                "OPENROUTER_API_KEY"]:
        val = os.environ.get(var, "")
        if not val:
            continue
        digest = hashlib.sha256(val.encode()).hexdigest()[:12]
        if digest in seen:
            out.append({"tipo": "cuenta", "nombre": var, "estado": ENCONTRADO,
                        "detalle": f"ALIAS de {seen[digest]} (misma cuenta, hash {digest})"})
            continue
        seen[digest] = var
        r = probe_credits(val, timeout=12)
        det = f"hash {digest}"
        if r.get("ok"):
            det += (f", total=${r['total']}, restante=${r['restante']}")
        else:
            det += f", consulta fallo (HTTP {r.get('status')})"
        out.append({"tipo": "cuenta", "nombre": var, "estado": PROBADO, "detalle": det})
    return out


def check_last30days(workspace: Path) -> dict:
    """Prueba si el motor archivado arranca de verdad."""
    script = workspace / ".agents/skills/_archive/last30days/scripts/last30days.py"
    if not script.exists():
        return {"tipo": "motor", "nombre": "last30days", "estado": AUSENTE}
    try:
        p = subprocess.run([sys.executable, str(script), "--preflight"],
                           capture_output=True, text=True, timeout=90, cwd=script.parent)
        out = p.stdout or p.stderr
        ok = "Ready to research" in out
        fuentes = ""
        m = re.search(r"Available sources:\s*(.+)", out)
        if m:
            fuentes = m.group(1).strip()
        return {"tipo": "motor", "nombre": "last30days", "estado": PROBADO if ok else FALLA,
                "detalle": fuentes or out.strip()[:160]}
    except subprocess.TimeoutExpired:
        return {"tipo": "motor", "nombre": "last30days", "estado": FALLA,
                "detalle": "preflight excedio 90s"}
    except (subprocess.SubprocessError, OSError) as exc:
        return {"tipo": "motor", "nombre": "last30days", "estado": FALLA,
                "detalle": type(exc).__name__}


# ---------------------------------------------------------------- reporte

def summarize(items: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for i in items:
        counts[i["estado"]] = counts.get(i["estado"], 0) + 1
    return counts


def render_table(items: list[dict]) -> str:
    lines = [f"{'TIPO':<10} {'NOMBRE':<42} {'ESTADO':<11} DETALLE",
             "-" * 108]
    for i in items:
        det = str(i.get("detalle") or i.get("ruta") or "")[:44]
        lines.append(f"{i['tipo']:<10} {i['nombre'][:42]:<42} {i['estado']:<11} {det}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventario de herramientas de investigacion")
    ap.add_argument("--workspace", default="/home/tec/Dropbox/ANTIGRAVITY_PROJECTS")
    ap.add_argument("--out", default=None, help="Ruta del inventory.json")
    ap.add_argument("--json-only", action="store_true")
    ap.add_argument("--no-network", action="store_true")
    ap.add_argument("--repeticiones", type=int, default=3,
                    help="Sondas repetidas para detectar intermitencia (DDG ~1 de cada 4)")
    args = ap.parse_args()

    ws = Path(args.workspace)
    items: list[dict] = []
    items += scan_clis()
    items += scan_skills(ws)
    items += scan_env()
    items += scan_infra()
    items += scan_web_search_habilitado()
    items += scan_serper()
    items.append(check_last30days(ws))
    if not args.no_network:
        items += scan_sources(network=True)
        items += scan_intermitentes(repeticiones=args.repeticiones)
        items += scan_openrouter_accounts()

    counts = summarize(items)
    inv = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "workspace": str(ws),
        "red_probada": not args.no_network,
        "resumen": counts,
        "total": len(items),
        "items": items,
    }

    if args.json_only:
        print(json.dumps(inv, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*108}\n INVENTARIO DE HERRAMIENTAS — {inv['generado']}\n{'='*108}")
        print(render_table(items))
        print(f"\n RESUMEN: " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        print(f" Total: {len(items)} herramientas  ·  red probada: {not args.no_network}")
        print(" NOTA: ningun valor de variable se ha leido ni escrito.\n")

    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[doctor] escrito {outp}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
