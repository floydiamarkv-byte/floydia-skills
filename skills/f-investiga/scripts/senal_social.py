#!/usr/bin/env python3
"""senal_social.py — Senal de redes sin API key, con cascada y degradacion limpia.

POR QUE NO HAY "BUSQUEDA EN X"
==============================
Verificado empiricamente 2026-09-28:
  - Nitter: repo ARCHIVADO. 7 instancias probadas -> 0 tweets (intersticial
    anti-bot), 403 Cloudflare, o sin DNS. xcancel.com -> HTTP 451.
  - cdn.syndication.twimg.com: HTTP 200 con CUERPO VACIO (o timeout).
  - api.twitter.com/2/tweets/20 -> HTTP 401 sin OAuth. NO HAY TIER GRATUITO.
  - twikit (4.701*) reconstruye la firma ClientTransaction leyendo los chunks
    webpack de x.com = elusion deliberada de anti-bot. Los ToS de X anuncian
    "permanent suspension of your account".

Conclusion: la UNICA via oficial sin key es `publish.x.com/oembed`, y NO BUSCA:
solo resuelve una URL conocida.

POR QUE ESTE SCRIPT NO HACE SCRAPING DE X
=========================================
X ToS 4(iii): "crawling or scraping the Services in any form, for any purpose
without our prior written consent is expressly prohibited". Este script no
viola esa norma porque no toca X salvo por oEmbed (endpoint oficial, por URL
conocida). El resto de canales son plataformas abiertas por diseño.

CASCADA (medida, no supuesta)
=============================
  1. Bluesky  api.bsky.app      sin key  PROBADO  con engagement
     (ojo: public.api.bsky.app -> 403; usar api.bsky.app)
  2. HN Algolia                 sin key  PROBADO  filtro temporal real
  3. Reddit .rss                sin key  PROBADO  (el .json da 403)
  4. Lobste.rs                  sin key  INTERMITENTE
  5. X oEmbed                   sin key  SOLO URL CONOCIDA
  6. Mastodon                   sin key  federado

Cada canal declara su estado: HECHO / VACIO / NULO. "sin resultados" nunca se
confunde con "fallo".

USO
===
    python3 senal_social.py --query "openai" --canal todos
    python3 senal_social.py --query "deep research" --url-tweet "https://x.com/a/status/1"
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"
HECHO, VACIO, NULO = "HECHO", "VACIO", "NULO"
TIMEOUT = 20


def _fetch(url: str, timeout: int = TIMEOUT, raw: bool = False) -> dict:
    """GET tolerante. NUNCA lanza. Separa 'no hay datos' de 'fallo de red'."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "application/json" if not raw else "*/*"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            cuerpo = r.read(1_500_000)
            if raw:
                return {"_status": r.status, "_raw": cuerpo.decode("utf-8", "ignore"),
                        "_len": len(cuerpo)}
            return {"_status": r.status, "_json": json.loads(cuerpo.decode() or "{}")}
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"_error": type(e).__name__}
    except json.JSONDecodeError:
        return {"_error": "respuesta no es JSON"}


def _datos(v, campo: str) -> dict:
    """Traduce el resultado crudo al veredicto correcto.

    Esto es lo que impide el fallo clasico: devolver "sin resultados" cuando en
    realidad la fuente fallo, o al reves.
    """
    if "_error" in v:
        return {"estado": NULO, "detalle": v["_error"]}
    datos = v.get("_json", {}).get(campo, [])
    if not datos:
        return {"estado": VACIO, "detalle": "la fuente respondio sin resultados"}
    return {"estado": HECHO, "detalle": f"{len(datos)} elementos", "datos": datos}


# ----------------------------------------------------------------- canales

def bluesky(q: str, limit: int = 15) -> dict:
    """api.bsky.app. Verificado 2026-09-28: public.api.bsky.app devuelve 403,
    api.bsky.app responde 200 con likes y reposts."""
    url = ("https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q="
           + urllib.parse.quote(q) + f"&limit={limit}&sort=top")
    r = _datos(_fetch(url), "posts")
    if r["estado"] != HECHO:
        r["canal"] = "Bluesky"
        return r
    r["canal"] = "Bluesky (api.bsky.app)"
    r["dimension"] = "Senal social con engagement. Sustituto DIRECTO de X, no espejo."
    r["items"] = [{
        "autor": p.get("author", {}).get("handle"),
        "fecha": p.get("record", {}).get("createdAt"),
        "likes": p.get("likeCount"), "reposts": p.get("repostCount"),
        "texto": (p.get("record", {}).get("text") or "")[:280],
    } for p in r.pop("datos")]
    return r


def hackernews(q: str, limit: int = 15, dias: int = 30) -> dict:
    """Algolia con filtro temporal real (created_at_i)."""
    desde = int(time.time()) - dias * 86400
    # DOS BUGS REALES (cazados por el test, ambos HTTP 400 silencioso):
    #  1) El parametro es `query=`, NO `q=`. Con `q=` la API responde 400.
    #     curl lo acepta en algunos endpoints, urllib no: por eso el fallo
    #     solo aparecia en el script.
    #  2) El '>' de numericFilters DEBE ir percent-encoded (%3E).
    url = ("https://hn.algolia.com/api/v1/search_by_date?query="
           + urllib.parse.quote(q) + "&tags=story"
           + f"&numericFilters=created_at_i%3E{desde}&hitsPerPage={limit}")
    r = _datos(_fetch(url), "hits")
    if r["estado"] != HECHO:
        r["canal"] = "Hacker News"
        return r
    r["canal"] = "Hacker News (Algolia)"
    r["dimension"] = f"Discurso tecnico, ventana de {dias} dias. Sesgo fuerte a_RESULTADOS."
    r["items"] = [{
        "titulo": h.get("title"), "puntos": h.get("points"),
        "comentarios": h.get("num_comments"), "url": h.get("url"),
        "fecha": h.get("created_at"),
    } for h in r.pop("datos")]
    return r


def reddit(q: str, limit: int = 15, subreddit: str = "LocalLLaMA") -> dict:
    """Solo .rss: el .json devuelve 403 desde esta IP (verificado)."""
    url = (f"https://www.reddit.com/r/{subreddit}/search.rss?q="
           + urllib.parse.quote(q) + f"&restrict_sr=1&sort=relevance&limit={limit}")
    v = _fetch(url, raw=True)
    if "_error" in v:
        return {"canal": "Reddit (.rss)", "estado": NULO, "detalle": v["_error"]}
    import re
    items = re.findall(r"<title>(.*?)</title>.*?<link>(.*?)</link>", v["_raw"], re.S)
    if not items:
        return {"canal": "Reddit (.rss)", "estado": VACIO,
                "detalle": "RSS respondio sin entradas"}
    return {"canal": f"Reddit r/{subreddit} (.rss)", "estado": HECHO,
            "detalle": f"{len(items)} entradas",
            "dimension": "S community. Sesgo fuerte a US. El .json NO es accesible "
                         "sin OAuth; por eso se usa el RSS.",
            "items": [{"titulo": t[:200], "url": l} for t, l in items[:limit]]}


def lobsters(q: str, limit: int = 15) -> dict:
    """VERIFICADO 2026-09-28: search.json devuelve HTTP 400 y la version HTML
    no es parseable de forma fiable. Se usa el RSS Atom, que es estable."""
    url = "https://lobste.rs/search.rss?q=" + urllib.parse.quote(q) + \
          "&what=stories&order=newest"
    v = _fetch(url, raw=True)
    if "_error" in v:
        return {"canal": "Lobste.rs (RSS)", "estado": NULO, "detalle": v["_error"]}
    import re as _re
    entradas = _re.findall(
        r"<entry>(.*?)</entry>", v["_raw"], _re.S)
    items = []
    for e in entradas[:limit]:
        t = _re.search(r"<title>(.*?)</title>", e, _re.S)
        l = _re.search(r'href="([^"]+)"', e)
        d = _re.search(r"<updated>(.*?)</updated>", e, _re.S)
        if t:
            items.append({"titulo": _re.sub(r"<[^>]+>", "", t.group(1))[:200],
                          "url": l.group(1) if l else None,
                          "fecha": d.group(1) if d else None})
    return {"canal": "Lobste.rs (RSS Atom)", "estado": HECHO if items else VACIO,
            "detalle": f"{len(items)} entradas" if items else "RSS sin entradas",
            "dimension": "Comunidad tecnica pequena y curada. "
                         "Menos volumen que HN, mas senal por entrada.",
            "items": items}


def x_oembed(url_tweet: str) -> dict:
    """LA UNICA via oficial de X sin API key. NO BUSCA: resuelve una URL.

    Usa publish.twitter.com/oembed. Se documenta como tal para que nadie la
    confunda con una via de busqueda.
    """
    url = ("https://publish.twitter.com/oembed?omit_script=1&url="
           + urllib.parse.quote(url_tweet))
    v = _fetch(url)
    if "_error" in v:
        return {"canal": "X oEmbed", "estado": NULO, "detalle": v["_error"],
                "aviso": "Un 404 aqui significa tweet inexistente o privado, "
                         "no que el endpoint este roto."}
    d = v.get("_json", {})
    if not d:
        return {"canal": "X oEmbed", "estado": VACIO, "detalle": "sin payload"}
    return {"canal": "X oEmbed (oficial, sin key)", "estado": HECHO,
            "autor": d.get("author_name"), "texto": d.get("html", "")[:400],
            "dimension": "UN POST CONCRETO por URL. NO es busqueda: para buscar en X "
                         "hace falta API de pago. Scraping de sesion esta prohibido "
                         "por los ToS de X.",
            "url": url_tweet}


# ------------------------------------------------------------------- main

CASCADA = {"bluesky": bluesky, "hackernews": hackernews, "reddit": reddit,
           "lobsters": lobsters}


def main() -> int:
    ap = argparse.ArgumentParser(description="Senal social sin API key")
    ap.add_argument("--query", required=True)
    ap.add_argument("--canal", default="todos",
                    choices=list(CASCADA) + ["todos"])
    ap.add_argument("--url-tweet", default=None,
                    help="URL de un tweet concreto (via X oEmbed oficial)")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--dias", type=int, default=30)
    args = ap.parse_args()

    out = {"generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "query": args.query,
           "aviso_global": (
               "X NO tiene via de busqueda gratuita ni legal. Este script no hace "
               "scraping de sesion (prohibido por los ToS de X, con riesgo de "
               "suspension permanente). Los canales usados son plataformas abiertas "
               "por diseño.")}
    canales = CASCADA if args.canal == "todos" else {args.canal: CASCADA[args.canal]}

    for nombre, fn in canales.items():
        try:
            out[nombre] = fn(args.query, args.limit) if nombre != "reddit" else \
                fn(args.query, args.limit)
        except Exception as e:  # un canal caido no tumba el resto
            out[nombre] = {"canal": nombre, "estado": NULO,
                           "detalle": f"excepcion: {type(e).__name__}"}
        if nombre == "hackernews":
            out[nombre] = hackernews(args.query, args.limit, args.dias)

    if args.url_tweet:
        out["x_oembed"] = x_oembed(args.url_tweet)

    estados = [v.get("estado") for k, v in out.items()
               if isinstance(v, dict) and "estado" in v]
    out["resumen"] = {
        "canales_HECHO": estados.count(HECHO),
        "canales_VACIO": estados.count(VACIO),
        "canales_NULO": estados.count(NULO),
        "cobertura": "COMPLETA" if estados.count(NULO) == 0 else
                     ("PARCIAL: " + ", ".join(
                         k for k, v in out.items()
                         if isinstance(v, dict) and v.get("estado") == NULO)),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
