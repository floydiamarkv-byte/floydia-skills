#!/usr/bin/env python3
"""verify_citations.py — Capa 3: verificar que cada cita existe de verdad.

POR QUÉ EXISTE
===============
El fallo mas caro de un informe de investigación es una cita plausible pero
inventada. Este script distingue DOS casos que se confunden:

  - La URL NUNCA EXISTIO      -> ALUCINACION. La IA se la invento.
  - La URL EXISTE pero CAMBIO  -> la cita es real pero el fragmento puede no estar.

Usa Wayback (`archive.org/wayback/available`) como discriminador, porque responde
`{}` cuando la URL no ha estado nunca archivada, y ademas un fetch directo para
comprobar que la pagina responde hoy.

CLASIFICACION DE AFIRMACIONES
=============================
  HECHO           al menos 1 fuente de tier 1-2 con cita verificada
  INFERENCIA      logica derivada, sin fuente primaria directa
  DISPUTADO       fuentes autorizadas sostienen posturas opuestas
  NO_VERIFICABLE  ninguna cita sobrevive a la verificacion

USO
===
    python3 verify_citations.py findings/*.json
    python3 verify_citations.py --external respuesta_externa.md
    cat findings.json | python3 verify_citations.py -
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"
WAYBACK = "https://archive.org/wayback/available?url="

HECHO, INFERENCIA, DISPUTADO, NO_VERIFICABLE = (
    "HECHO", "INFERENCIA", "DISPUTADO", "NO_VERIFICABLE")

# Dominios que sabemos bloqueados desde esta IP. Marcarlos evita
# "rechazar" una cita buena solo por la red.
KNOWN_BLOCKED = {
    "semanticscholar.org": "429 en pool compartido",
    "public.api.bsky.app": "403; usar api.bsky.app",
    "artificialanalysis.ai": "inalcanzable por TCP desde esta IP",
    "openai.com": "403 Cloudflare",
    "x.com": "Cloudflare; ToS prohiben scraping",
    "twitter.com": "Cloudflare; ToS prohiben scraping",
}

TRACKING_RE = re.compile(r"[?&](utm_[^=]+|ref|fbclid|gclid|mc_cid|mc_eid)=[^&]*", re.I)


def normalize_url(url: str) -> str:
    """Quita parametros de tracking y normaliza. Base del hash de dedup."""
    url = url.strip()
    url = TRACKING_RE.sub("", url)
    url = url.rstrip("/")
    return url.lower()


def dedup_key(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode()).hexdigest()[:16]


def check_wayback(url: str, timeout: int = 15, intentos: int = 3) -> dict:
    """Discrimina ALUCINACION vs URL-QUE-CAMBIÓ.

    REINTENTA antes de declarar 'nunca archivada'. Verificado 2026-09-28: la
    API de Wayback es INCONSISTENTE para la misma URL. Para
    openai.com/policies/row-terms-of-use devolvio snapshot 20260927204534 en la
    ronda anterior y NINGUNO en 5 intentos consecutivos de la siguiente, sin
    que la URL cambiara. Sin reintento, una comprobacion transitoria de un
    tercero se reporta como 'citada alucinada' — el mismo error que la ronda
    anterior me duro a proposito.
    """
    for i in range(intentos):
        try:
            req = Request(WAYBACK + url, headers={"User-Agent": UA})
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode() or "{}")
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
            if i < intentos - 1:
                time.sleep(1.5)
                continue
            return {"wayback": "INDISPONIBLE"}
        snaps = data.get("archived_snapshots") or {}
        closest = snaps.get("closest")
        if closest:
            return {"wayback": "ARCHIVADA", "snapshot": closest.get("timestamp"),
                    "status": closest.get("status")}
        # Sin snapshot. Puede ser "no existe" o una comprobacion incompleta:
        # si la pagina responde 403/429 hay bloqueo de red, no ausencia.
        if i < intentos - 1:
            time.sleep(1.5)
            continue
        return {"wayback": "NUNCA_ARCHIVADA"}
    return {"wayback": "NUNCA_ARCHIVADA"}


def check_live(url: str, timeout: int = 15) -> dict:
    """Comprueba que la pagina responde HOY. Sigue redirects: una 308 que
    acaba en 404 NO es una cita valida."""
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=timeout) as resp:
            return {"live": 200 <= resp.status < 300, "status": resp.status,
                    "final_url": resp.geturl()}
    except HTTPError as exc:
        return {"live": False, "status": exc.code, "final_url": url}
    except (URLError, TimeoutError, OSError) as exc:
        return {"live": False, "nota": type(exc).__name__}


def extract_title(url: str, timeout: int = 15) -> str:
    """Titulo real de la pagina. Detecta ALUCINACION SEMANTICA: una URL puede
    responder 200 y hablar de algo completamente distinto."""
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=timeout) as resp:
            html = resp.read(300_000).decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError, OSError):
        return ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if not m:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()[:200]


# Delata que la URL existe pero NO habla de lo afirmado.
# Probado 2026-09-28: un modelo :free cito arxiv.org/abs/2310.08562 como
# "Plan-and-Solve Prompting"; la pagina real es "Kinetic description and
# convergence analysis of genetic algorithms" -> HTTP 200 y cita falsa a la vez.
SEMANTIC_MISMATCH = re.compile(
    r"kinetic description|genetic algorithm|root finding|partial differential"
    r"|protein folding|clinical trial|photochemical", re.I)


def verify_source(src: dict, deep: bool = False) -> dict:
    url = src.get("url", "")
    out = {
        "url": url,
        "url_normalizada": normalize_url(url),
        "hash": dedup_key(url),
        "tier": src.get("tier"),
        "fecha_publicacion": src.get("published") or src.get("fecha"),
        "quote": (src.get("quote") or src.get("fragmento") or "")[:200],
    }
    if not url.startswith(("http://", "https://")):
        out["veredicto"] = NO_VERIFICABLE
        out["motivo"] = "no es una URL"
        return out

    host = re.sub(r"^www\.", "", (re.split(r"/+", url)[2] if "//" in url else ""))
    if host in KNOWN_BLOCKED:
        out["veredicto"] = DISPUTADO
        out["motivo"] = f"hostKnown-bloqueado: {KNOWN_BLOCKED[host]}"
        out["bloqueado_conocido"] = True

    wb = check_wayback(url)
    live = check_live(url)
    out["wayback"] = wb.get("wayback")
    out["vivo"] = live

    # ALUCINACION SEMANTICA: la URL responde 200 pero habla de otra cosa.
    # Es el fallo que un chequeo de HTTP puro no detecta. Verificado 2026-09-28:
    # un modelo :free cito arxiv.org/abs/2310.08562 ("Plan-and-Solve Prompting")
    # y la pagina real es un paper de algoritmos geneticos.
    if live.get("live"):
        title = extract_title(url)
        if title:
            out["titulo_real"] = title
            if SEMANTIC_MISMATCH.search(title):
                out["veredicto"] = NO_VERIFICABLE
                out["motivo"] = (f"ALUCINACION SEMANTICA: la URL existe pero el titulo "
                                 f"real es '{title[:80]}' y no respalda la afirmacion")
                return out

    # CASO CORREGIDO 2026-09-28: una URL puede estar ARCHIVADA (=> existio de
    # verdad) y a la vez devolver 403 desde esta IP por Cloudflare. Antes eso
    # caia al elif final y se marcaba NO_VERIFICABLE, confundiendo
    # "bloqueada por la red" con "citada alucinada". Verificado: 4 citas de
    # openai.com/developers.openai.com tienen snapshot en Wayback pero dan 403.
    # Una URL que responde 403/429/503 no se puede evaluar por snapshot: hay
    # bloqueo de red por medio. Declararla 'alucinada' seria inventar.
    if (not live.get("live") and live.get("status") in (401, 403, 429, 503)
            and wb.get("wayback") in ("ARCHIVADA", "INDISPONIBLE",
                                      "NUNCA_ARCHIVADA")):
        snap = wb.get("snapshot")
        prueba = (f"existe (snapshot {snap})" if snap else
                  "no se pudo confirmar por Wayback, que es intermitente")
        out["veredicto"] = DISPUTADO
        out["motivo"] = (f"BLOQUEADA POR RED, no alucinada: {prueba}, pero "
                         f"responde HTTP {live.get('status')} desde esta IP. "
                         f"No se puede confirmar ni desmentir aqui; "
                         f"verificable desde otra red.")
    elif wb.get("wayback") == "NUNCA_ARCHIVADA" and not live.get("live"):
        out["veredicto"] = NO_VERIFICABLE
        out["motivo"] = "ALUCINACION PROBABLE: nunca archivada y no responde"
    elif out.get("bloqueado_conocido"):
        pass  # se queda en DISPUTADO con el motivo del bloqueo
    elif live.get("live"):
        out["veredicto"] = HECHO
        out["motivo"] = f"responde HTTP {live.get('status')}"
        if live.get("final_url") and live["final_url"] != url:
            out["motivo"] += f" (redirige a {live['final_url'][:70]})"
        if wb.get("wayback") == "ARCHIVADA":
            out["motivo"] += f" y está archivada desde {wb.get('snapshot')}"
    else:
        out["veredicto"] = NO_VERIFICABLE
        out["motivo"] = f"no responde (HTTP {live.get('status')})"

    if deep and out["veredicto"] == HECHO and out["quote"]:
        out["quote_verificada"] = verify_quote(url, out["quote"])
    return out


def verify_quote(url: str, quote: str, timeout: int = 20) -> dict:
    """Comprueba que el fragmento citado existe literalmente en la pagina."""
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=timeout) as resp:
            html = resp.read(1_500_000).decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError, OSError):
        return {"ok": None, "nota": "no se pudo descargar"}
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    needle = re.sub(r"\s+", " ", quote).strip()[:80]
    if not needle:
        return {"ok": None, "nota": "sin fragmento que verificar"}
    return {"ok": needle.lower() in text.lower(),
            "buscado": needle[:80]}


def load_findings(paths: list[str]) -> list[dict]:
    """Lee findings de .json o de un .md de respuesta externa."""
    out: list[dict] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"[verify] no existe: {p}", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix == ".json":
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    out += [d for d in data if isinstance(d, dict)]
                elif isinstance(data, dict):
                    for k in ("findings", "hallazgos", "items", "respuestas"):
                        if isinstance(data.get(k), list):
                            out += [d for d in data[k] if isinstance(d, dict)]
            except json.JSONDecodeError as exc:
                print(f"[verify] JSON invalido en {p}: {exc}", file=sys.stderr)
        else:
            # Markdown: extraer URLs y tratarlas como fuentes sin afirmacion.
            for url in dict.fromkeys(re.findall(r"https?://[^\s\)\]\"'<>]+", text)):
                out.append({"claim": "(URL suelta en markdown)", "sources": [{"url": url}]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Verificacion de citas")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--deep", action="store_true", help="Verificar fragmentos literales")
    ap.add_argument("--delay", type=float, default=0.4, help="Pausa entre fuentes")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    findings = load_findings(args.paths)
    if not findings:
        print(json.dumps({"error": "SIN_HALLAZGOS", "paths": args.paths}, ensure_ascii=False))
        return 1

    report = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hallazgos": [],
        "resumen": {HECHO: 0, INFERENCIA: 0, DISPUTADO: 0, NO_VERIFICABLE: 0},
        "urls_unicas": 0,
    }
    hashes: set[str] = set()

    for f in findings:
        sources = f.get("sources") or f.get("citas") or []
        if isinstance(sources, dict):
            sources = [sources]
        ver: list[dict] = []
        for s in sources:
            if isinstance(s, str):
                s = {"url": s}
            if not isinstance(s, dict):
                continue
            r = verify_source(s, deep=args.deep)
            ver.append(r)
            hashes.add(r["hash"])
            time.sleep(args.delay)

        vh = [v for v in ver if v["veredicto"] == HECHO]
        dv = [v for v in ver if v["veredicto"] == DISPUTADO]
        if vh:
            estado = HECHO
        elif dv:
            estado = DISPUTADO
        elif ver:
            estado = NO_VERIFICABLE
        else:
            estado = INFERENCIA
        report["resumen"][estado] += 1
        report["hallazgos"].append({
            "id": f.get("id") or f.get("afirmacion_id") or f.get("_origen"),
            "claim": f.get("claim") or f.get("afirmacion"),
            "confidence_declarada": f.get("confidence") or f.get("confianza"),
            "estado": estado,
            "contradicciones_declaradas": f.get("contradicts") or f.get("contradicciones") or [],
            "fuentes": ver,
        })

    report["urls_unicas"] = len(hashes)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"[verify] escrito {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
