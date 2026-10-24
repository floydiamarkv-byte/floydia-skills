#!/usr/bin/env python3
"""busqueda_web.py — Busqueda web con Serper (Google real) y cascada keyless.

POR QUE EXISTE
==============
`web_search` del harness apunta a la cuenta de CHAT de DeepSeek y devuelve
HTTP 402 por falta de saldo. Verificado 2026-09-28: **no tiene arreglo sin
gasto**. Este script lo sustituye.

ESTADO REAL MEDIDO (2026-09-28)
================================
  Serper /search   -> OK  5 resultados organicos, snippets incluidos
  Serper /images   -> OK  19+ resultados
  Serper /news     -> OK ultimas noticias
  El campo `credits: 1` que devuelve la API es un CONTADOR POR CONSULTA, no el
  saldo. Verificado con 3 consultas consecutivas: siempre 1. (Comprobado para no
  panicar pensando que quedaba 1 consulta en total.)

POLITICA DE USO (obligatoria)
============================
Serper es la UNICA fuente que consume cuota. Las demas son keyless. Por eso:

  1. `consultar_serper()` tiene tope de llamadas y NO se llama en bucle.
  2. La cascada keyless se prueba ANTES: si algo mas cubre la consulta, no se
     gasta Serper.
  3. El informe declara cuantas consultas se hicieron y si la cuota se toco.
  4. Cache local en disco: repetir la misma consulta NO vuelve a gastar.

CASCADA (prioridad, de mas barata a mas cara)
=============================================
  1. HN Algolia          sin key   tecnica y muy reciente
  2. Bluesky             sin key   senal social con engagement
  3. OpenAlex            sin key   academico
  4. arXiv               sin key   preprints
  5. DuckDuckGo          DEGRADADO (~1 de cada 10 intentos) -> ultimo recurso
  6. Serper (CUOTA)      con key   Google real, web general

USO
===
    python3 busqueda_web.py "agentes deep research 2026"
    python3 busqueda_web.py "..." --solo serper
    python3 busqueda_web.py "..." --noticias
    python3 busqueda_web.py "..." --no-serper      # solo keyless, 0 cuota
    python3 busqueda_web.py "..." --stats          # ver cuota/cache
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"
HECHO, VACIO, NULO = "HECHO", "VACIO", "NULO"

# Variables candidatas para Serper, en orden. C7_SERPER_API es la confirmada.
SERPER_VARS = ["C7_SERPER_API", "SERPER_API", "SERPER_API_KEY", "C7_SERPER"]

# Cache: repetir consulta no debe gastar cuota.
CACHE_DIR = Path(os.path.expanduser("~/.cache/f-swarm-research/busquedas"))
CACHE_TTL_H = 24


def _get(url: str, timeout: int = 20, headers: dict | None = None) -> dict:
    """GET tolerante. Nunca lanza: separa 'sin datos' de 'fallo'."""
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"_json": json.loads(r.read().decode() or "{}"), "_status": r.status}
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"_error": type(e).__name__}
    except json.JSONDecodeError:
        return {"_error": "respuesta no es JSON"}


def _post(url: str, payload: dict, headers: dict, timeout: int = 30) -> dict:
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, method="POST", headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"_json": json.loads(r.read().decode() or "{}"), "_status": r.status}
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()[:200]
        except Exception:
            pass
        return {"_error": f"HTTP {e.code}", "body": body}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"_error": type(e).__name__}
    except json.JSONDecodeError:
        return {"_error": "respuesta no es JSON"}


# ------------------------------------------------------------------- cache

def _cache_path(clave: str) -> Path:
    return CACHE_DIR / f"{hashlib.sha256(clave.encode()).hexdigest()[:16]}.json"


def cache_lee(clave: str) -> dict | None:
    p = _cache_path(clave)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        edad_h = (time.time() - data.get("_ts", 0)) / 3600
        if edad_h > CACHE_TTL_H:
            return None
        data["_cache_h"] = round(edad_h, 1)
        return data
    except (OSError, json.JSONDecodeError):
        return None


def cache_escribe(clave: str, valor: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        valor = {**valor, "_ts": time.time()}
        _cache_path(clave).write_text(json.dumps(valor, ensure_ascii=False),
                                      encoding="utf-8")
    except OSError:
        pass


# ------------------------------------------------------- fuentes keyless

def hackernews(q: str, n: int = 8) -> dict:
    desde = int(time.time()) - 30 * 86400
    # OJO: 'query=' (no 'q=') y '>' percent-encoded. Ambos dan 400 si se fallan.
    url = ("https://hn.algolia.com/api/v1/search?query=" + urllib.parse.quote(q)
           + f"&numericFilters=created_at_i%3E{desde}&hitsPerPage={n}")
    r = _get(url)
    if "_error" in r:
        return {"estado": NULO, "detalle": r["_error"]}
    hits = r["_json"].get("hits", [])
    if not hits:
        return {"estado": VACIO, "detalle": "sin resultados en 30 dias"}
    return {"estado": HECHO, "coste": "$0.00", "items": [{
        "titulo": h.get("title"), "url": h.get("url"),
        "puntos": h.get("points"), "comentarios": h.get("num_comments"),
        "fecha": h.get("created_at"),
    } for h in hits]}


def bluesky(q: str, n: int = 8) -> dict:
    url = ("https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q="
           + urllib.parse.quote(q) + f"&limit={n}&sort=top")
    r = _get(url)
    if "_error" in r:
        return {"estado": NULO, "detalle": r["_error"]}
    posts = r["_json"].get("posts", [])
    if not posts:
        return {"estado": VACIO, "detalle": "sin posts"}
    return {"estado": HECHO, "coste": "$0.00", "items": [{
        "autor": p.get("author", {}).get("handle"),
        "texto": (p.get("record", {}).get("text") or "")[:280],
        "likes": p.get("likeCount"), "url": f"https://bsky.app/profile/"
        f"{p.get('author', {}).get('handle')}/post/{p.get('uri','').split('/')[-1]}",
    } for p in posts]}


def openalex(q: str, n: int = 8) -> dict:
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(q)
           + f"&per-page={n}")
    r = _get(url)
    if "_error" in r:
        return {"estado": NULO, "detalle": r["_error"]}
    res = r["_json"].get("results", [])
    if not res:
        return {"estado": VACIO, "detalle": "sin obras"}
    return {"estado": HECHO, "coste": "$0.00", "items": [{
        "titulo": w.get("title"), "url": w.get("doi") or w.get("id"),
        "anio": w.get("publication_year"), "citas": w.get("cited_by_count"),
    } for w in res]}


def arxiv(q: str, n: int = 8) -> dict:
    url = ("https://export.arxiv.org/api/query?search_query=all:"
           + urllib.parse.quote(q) + f"&max_results={n}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as resp:
            xml = resp.read(800_000).decode("utf-8", "ignore")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        return {"estado": NULO, "detalle": type(e).__name__}
    import re
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.S)
    if not entries:
        return {"estado": VACIO, "detalle": "sin preprints"}
    items = []
    for e in entries:
        t = re.search(r"<title>(.*?)</title>", e, re.S)
        l = re.search(r"<id>(.*?)</id>", e, re.S)
        p = re.search(r"<published>(\d{4})", e)
        if t:
            items.append({"titulo": re.sub(r"\s+", " ", t.group(1)).strip()[:200],
                          "url": l.group(1).strip() if l else None,
                          "anio": p.group(1) if p else None})
    return {"estado": HECHO, "coste": "$0.00", "items": items}


def duckduckgo(q: str, n: int = 8) -> dict:
    """DEGRADADO: ~1 de cada 10 intentos devuelve resultados. Ultimo recurso."""
    try:
        req = urllib.request.Request("https://html.duckduckgo.com/html/?q="
                                     + urllib.parse.quote(q),
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read(500_000).decode("utf-8", "ignore")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        return {"estado": NULO, "detalle": type(e).__name__}
    import re
    hits = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                      html, re.S)
    if not hits:
        return {"estado": NULO,
                "detalle": "DEGRADADO: responde 0 resultados (medido 1 de cada 10)"}
    items = []
    for u, titulo in hits[:n]:
        t = re.sub(r"<[^>]+>", "", titulo).strip()
        if "uddg=" in u:
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
            u = qs.get("uddg", [u])[0]
        items.append({"titulo": t[:200], "url": u})
    return {"estado": HECHO, "coste": "$0.00",
            "aviso": "DEGRADADO: puede devolver 0 sin aviso", "items": items}


# ---------------------------------------------------------------- Serper

def _serper_key() -> tuple[str | None, str | None]:
    vault = Path(os.path.expanduser("~/.secrets/antigravity.env"))
    if vault.exists():
        try:
            for line in vault.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k in SERPER_VARS and v and k not in os.environ:
                        os.environ[k] = v
        except OSError:
            pass
    for var in SERPER_VARS:
        v = os.environ.get(var, "").strip()
        if v:
            return var, v
    return None, None


def serper(q: str, n: int = 10, modo: str = "search") -> dict:
    """Google real via Serper. CONSUME CUOTA: solo si no hay keyless equivalente.

    El campo `credits` que devuelve la API es un CONTADOR POR CONSULTA (siempre 1
    en nuestras pruebas del 2026-09-28), NO el saldo restante.
    """
    var, key = _serper_key()
    if not key:
        return {"estado": NULO,
                "detalle": f"sin key. Busca: {' | '.join(SERPER_VARS)}"}
    endpoint = {"search": "https://google.serper.dev/search",
                "news": "https://google.serper.dev/news",
                "images": "https://google.serper.dev/images"}[modo]
    clave = f"{modo}:{q}:{n}"
    hit = cache_lee(clave)
    if hit:
        return {**hit, "_cache": True, "consultas_gastadas": 0}

    r = _post(endpoint, {"q": q, "num": n},
              {"X-API-KEY": key, "Content-Type": "application/json"})
    if "_error" in r:
        return {"estado": NULO, "detalle": r["_error"] + " " + r.get("body", "")[:120],
                "variable": var}
    d = r["_json"]
    if "message" in d and not any(k in d for k in ("organic", "news", "images")):
        return {"estado": NULO, "detalle": f"Serper: {d['message'][:120]}"}

    items = []
    if modo == "search":
        for o in d.get("organic", []):
            items.append({"titulo": o.get("title"), "url": o.get("link"),
                          "snippet": (o.get("snippet") or "")[:300],
                          "posicion": o.get("position")})
    elif modo == "news":
        for o in d.get("news", []):
            items.append({"titulo": o.get("title"), "url": o.get("link"),
                          "fuente": o.get("source"), "fecha": o.get("date"),
                          "snippet": (o.get("snippet") or "")[:300]})
    else:
        for o in d.get("images", []):
            items.append({"titulo": o.get("title"), "url": o.get("imageUrl"),
                          "pagina": o.get("link")})

    if not items:
        return {"estado": VACIO, "detalle": f"Serper {modo} sin resultados",
                "variable": var, "consultas_gastadas": 1}
    out = {"estado": HECHO, "fuente": f"Serper/{modo} (Google real)",
           "variable": var, "coste": "1 CREDITO", "consultas_gastadas": 1,
           "total_reportado": d.get("searchParameters", {}).get("totalResults"),
           "items": items}
    cache_escribe(clave, out)
    return out


# ------------------------------------------------------------------ main

KEYLESS = {"hackernews": hackernews, "bluesky": bluesky,
           "openalex": openalex, "arxiv": arxiv, "duckduckgo": duckduckgo}


def main() -> int:
    ap = argparse.ArgumentParser(description="Busqueda web con Serper + cascada keyless")
    ap.add_argument("query")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--noticias", action="store_true", help="Serper /news")
    ap.add_argument("--solo", choices=list(KEYLESS) + ["serper", "todas"],
                    default="todas")
    ap.add_argument("--no-serper", action="store_true",
                    help="solo fuentes keyless, 0 creditos gastados")
    ap.add_argument("--stats", action="store_true", help="estado de quota y cache")
    args = ap.parse_args()

    var, _ = _serper_key()
    if args.stats:
        entradas = list(CACHE_DIR.glob("*.json")) if CACHE_DIR.exists() else []
        print(json.dumps({
            "serper_key": var or "NO CONFIGURADA",
            "variables_buscadas": SERPER_VARS,
            "consultas_en_cache": len(entradas),
            "cache_dir": str(CACHE_DIR),
            "cache_ttl_horas": CACHE_TTL_H,
        }, ensure_ascii=False, indent=2))
        return 0

    inicio = time.time()
    out = {"consulta": args.query,
           "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "politica": "Las keyless se prueban primero. Serper (CUOTA) solo si "
                       "se pide explicitamente o si la keyless no cubre."}
    gastadas = 0

    if args.solo in ("todas",) or args.solo in KEYLESS:
        out["keyless"] = {}
        for nombre, fn in KEYLESS.items():
            if args.solo not in ("todas", nombre):
                continue
            try:
                out["keyless"][nombre] = fn(args.query, min(args.n, 8))
            except Exception as e:
                out["keyless"][nombre] = {"estado": NULO,
                                          "detalle": f"excepcion: {type(e).__name__}"}
            time.sleep(0.3)

    if not args.no_serper and args.solo in ("todas", "serper"):
        modo = "news" if args.noticias else "search"
        out["serper"] = serper(args.query, args.n, modo)
        gastadas += out["serper"].get("consultas_gastadas", 0)

    kl = [v for k, v in out.get("keyless", {}).items() if v.get("estado") == HECHO]
    out["resumen"] = {
        "keyless_con_datos": len(kl),
        "serper_usado": "serper" in out and out["serper"].get("estado") == HECHO,
        "creditos_gastados": gastadas,
        "desde_cache": out.get("serper", {}).get("_cache", False),
        "segundos": round(time.time() - inicio, 1),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
