#!/usr/bin/env python3
"""merge_findings.py — Fan-in determinista: N findings JSON -> 1 indice + consenso.

POR QUÉ
=======
Ocho subagentes que devuelven texto libre revientan el contexto del padre y
producen informes donde no se sabe que respalda cada frase. Este script hace
el fan-in de forma determinista y calcula el CONSENSO de forma explicita.

REGLA EPISTEMICA INNEGOCIABLE
=============================
"Todos de acuerdo" es la senal MAS DEBIL de confianza: significa que todos
recibieron la misma premisa, que puede ser no verificada. Este script lo
reporta explicitamente en vez de venderlo como certeza.

USO
===
    python3 merge_findings.py runs/<slug>/finding-*.json
    python3 merge_findings.py runs/<slug>/finding-*.json --out consensus.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

TRACKING_RE = re.compile(r"[?&](utm_[^=]+|ref|fbclid|gclid|mc_cid|mc_eid)=[^&]*", re.I)


def normalize_url(url: str) -> str:
    return TRACKING_RE.sub("", url.strip()).rstrip("/").lower()


def dedup_key(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode()).hexdigest()[:16]


# Palabras vacias para el calculo de similitud entre afirmaciones.
STOP = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "y", "o", "que", "con", "por", "para", "se", "es", "son", "fue", "como",
    "más", "pero", "su", "sus", "este", "esta", "esto", "eso", "hay", "the",
    "and", "for", "with", "that", "this", "from", "not", "are", "was", "can",
}

# MARCADORES DE DISCREPANCIA.
# Bug real cazado por run_eval.sh 2026-09-28: la similitud Jaccard(fundeva
# afirmaciones CONTRADICTORIAS. "X es la unica via" y "X no es la unica via"
# comparten casi todos los tokens, asi que Jaccard las fusionaba en un cluster
# y devolvia UNANIMIDAD sobre dos posiciones opuestas.
# La negacion es semantica, no lexica: hay que buscarla aparte.
NEGACIONES = re.compile(
    r"\b(no|nunca|jamas|sin|nada|ningun|ninguna|niega|niegan|contradic|"
    r"refuta|rechaza|incorrecto|erroneo|falso|niega|"
    r"never|not|cannot|can't|no longer|without|rejects|refutes|disproves)\b", re.I)
AFIRMACIONES = re.compile(
    r"\b(es|son|permite|puede|debe|funciona|sirve|existe|significa|"
    r"is|are|allows|can|should|works|provides|exists|means)\b", re.I)


def tiene_discrepancia(a: str, b: str) -> bool:
    """Dos afirmaciones sobre el mismo tema se contradicen si una niega y la
    otra afirma, aunque compartan el 90% de sus tokens."""
    na, nb = bool(NEGACIONES.search(a or "")), bool(NEGACIONES.search(b or ""))
    pa, pb = bool(AFIRMACIONES.search(a or "")), bool(AFIRMACIONES.search(b or ""))
    if na and not nb:
        return True
    if nb and not na:
        return True
    if na and nb:
        return False
    return False


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[\wÁÉÍÓÚÑáéíóúñ]{3,}", (text or "").lower())
    return {w for w in words if w not in STOP}


def similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load(paths: list[str]) -> list[dict]:
    out: list[dict] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"[merge] no existe: {p}", file=sys.stderr)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[merge] JSON invalido {p}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, dict):
            data = data.get("findings") or data.get("hallazgos") or [data]
        for d in data:
            if isinstance(d, dict):
                d.setdefault("_origen", path.name)
                out.append(d)
    return out


def get_claim(f: dict) -> str:
    return (f.get("claim") or f.get("afirmacion") or "").strip()


def get_sources(f: dict) -> list[dict]:
    s = f.get("sources") or f.get("citas") or []
    if isinstance(s, dict):
        s = [s]
    return [x if isinstance(x, dict) else {"url": str(x)} for x in s]


def main() -> int:
    ap = argparse.ArgumentParser(description="Fan-in determinista de findings")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default=None)
    ap.add_argument("--min-confidence", type=float, default=0.0)
    args = ap.parse_args()

    findings = load(args.paths)
    if not findings:
        print(json.dumps({"error": "SIN_FINDINGS", "paths": args.paths}, ensure_ascii=False))
        return 1

    findings = [f for f in findings if get_claim(f)
                and float(f.get("confidence") or f.get("confianza") or 0) >= args.min_confidence]

    # --- indice de fuentes deduplicadas ---------------------------------
    fuentes: dict[str, dict] = {}
    for f in findings:
        for s in get_sources(f):
            url = s.get("url") or ""
            if not url.startswith(("http://", "https://")):
                continue
            k = dedup_key(url)
            if k not in fuentes:
                fuentes[k] = {
                    "hash": k, "url": url, "url_normalizada": normalize_url(url),
                    "tier": s.get("tier"), "fecha": s.get("published") or s.get("fecha"),
                    "quote": (s.get("quote") or s.get("fragmento") or "")[:300],
                    "aparece_en": [],
                }
            fuentes[k]["aparece_en"].append(f.get("id") or f.get("_origen"))

    # --- agrupar afirmaciones similares ----------------------------------
    clusters: list[dict] = []
    for f in findings:
        claim = get_claim(f)
        toks = tokenize(claim)
        placed = False
        for c in clusters:
            if similarity(toks, c["_toks"]) < 0.42:
                continue
            # Gate de discrepancia: alta similitud lexica NO basta para
            # fusionar si una de las dos NIEGA lo que la otra AFIRMA.
            if tiene_discrepancia(claim, c["claim"]):
                continue
            c["miembros"].append(f)
            c["_toks"] |= toks
            placed = True
            break
        if not placed:
            clusters.append({"_toks": toks, "miembros": [f], "claim": claim})

    # --- clasificar cada cluster ----------------------------------------
    contradictorias: set[str] = set()
    for f in findings:
        for c in (f.get("contradicts") or f.get("contradicciones") or []):
            if isinstance(c, str):
                contradictorias.add(c)

    for c in clusters:
        miembros = c["miembros"]
        c.pop("_toks", None)
        c["motores"] = [m.get("id") or m.get("_origen") for m in miembros]
        c["n_motores"] = len(miembros)
        c["confianza_media"] = round(
            sum(float(m.get("confidence") or m.get("confianza") or 0) for m in miembros)
            / len(miembros), 3)
        c["confianza_max"] = max(
            float(m.get("confidence") or m.get("confianza") or 0) for m in miembros)
        c["afirmaciones"] = [get_claim(m) for m in miembros]
        c["fuentes"] = sorted({s.get("url") for m in miembros for s in get_sources(m)
                               if s.get("url", "").startswith("http")})
        c["en_conflicto"] = sorted({x for x in c["motores"] if x in contradictorias})

    clusters.sort(key=lambda x: (-x["n_motores"], -x["confianza_max"]))

    # --- CONSENSO: explicito, con la advertencia de premisa comun --------
    n = len(clusters)
    breakdown = Counter(c["n_motores"] for c in clusters)
    preamble = (
        "ADVERTENCIA EPISTEMICA: que varios motores coincidan prueba que COMPARTEN "
        "PREMISA, no que la premisa sea verdadera. El consenso sube la confianza "
        "sobre lo especifico, nunca sobre la premisa no verificada."
    )
    if n == 1 and clusters[0]["n_motores"] > 1:
        veredicto = "UNANIMIDAD_SOBRE_PREMISA_NO_VERIFICADA"
    elif clusters and clusters[0]["n_motores"] >= 3:
        veredicto = "CONSENSO"
    elif clusters and clusters[0]["n_motores"] == 2:
        veredicto = "MAYORIA_2"
    else:
        veredicto = "SIN_CONSENSO"

    # Indice de disidencia: proporcion de motores que sostienen una posicion
    # DISTINTA a la ganadora. Un solo cluster con todos los motores => 0.0.
    # Varios clusters => hay posiciones en conflicto, aunque una gane.
    n_members = len(findings)
    top = clusters[0]["n_motores"] if clusters else 0
    if n_members == 0:
        divergencia = 1.0
    elif len(clusters) == 1:
        divergencia = 0.0
    else:
        divergencia = round((n_members - top) / n_members, 3)

    report = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "entradas": len(findings),
        "motores_unicos": len({m.get("id") or m.get("_origen") for m in findings}),
        "clusters": clusters,
        "fuentes": sorted(fuentes.values(), key=lambda x: -len(x["aparece_en"])),
        "urls_unicas": len(fuentes),
        "distribucion_motores": dict(breakdown),
        "consenso": {
            "veredicto": veredicto,
            "cluster_ganador": clusters[0]["claim"][:200] if clusters else None,
            "votos_ganador": clusters[0]["n_motores"] if clusters else 0,
            "divergencia": round(divergencia, 3),
            "advertencia": preamble,
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"[merge] escrito {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
