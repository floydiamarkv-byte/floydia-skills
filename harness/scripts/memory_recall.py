#!/usr/bin/env python3
"""Recuperación L2/L3 por solapamiento de términos (BM25-lite, determinista, $0.00).

Sustituye al grep por patrón: el patrón lo escribía quien hacía la pregunta, así que
el test de recall medía mi habilidad para adivinar la cadena correcta, no la memoria.
Aquí la consulta se tokeniza y se puntúan PÁRRAFOS (no primeras coincidencias).

Uso:
    from memory_recall import search
    for f, para, score in search('¿cuántas cuentas usa el proxy NIM?', k=3): ...
"""
from __future__ import annotations

import math
import re
from pathlib import Path

PROJ = Path("<PROYECTO>")
BASES = [Path("~/.local/share/floydia/memory-bank/core"),
         PROJ / ".agents/skills",
         Path("~/.local/share/floydia/memory-bank/technical"),
         PROJ / "memory-bank/core", PROJ / "memory-bank/technical",
         PROJ / "SCRIPTS", PROJ / "providers"]
EXTS = {".md", ".json", ".yaml", ".yml"}
STOP = set("""de la el los las un una unos unas que en y o a al del por para con sin sobre
como cual cuales cuanto cuantos cuanta cuantas donde cuando es son esta estan hay usa usan
usa el cual que se su sus lo le les mas menos muy para pero si no ni ya""".split())
SYN = {"cuentas": ["cuenta", "accounts", "available_accounts"], "cuenta": ["accounts"],
       "peticiones": ["rpm", "requests", "rate"], "minuto": ["rpm", "rate"],
       "proxy": ["8088", "nvidia-proxy"], "auxiliares": ["auxiliary", "slot"],
       "bolsa": ["allowance", "cap"], "mensual": ["monthly"], "timeout": ["read", "timeout"]}


def _tokens(q: str) -> list[str]:
    raw = re.findall(r"[a-z0-9_.:/-]{3,}", q.lower())
    out = []
    for t in raw:
        if t in STOP:
            continue
        out.append(t)
        out.extend(SYN.get(t, []))
    return list(dict.fromkeys(out))


def _paras(path: Path) -> list[str]:
    try:
        txt = path.read_text(errors="ignore")
    except Exception:  # noqa: BLE001
        return []
    # bloques por línea en blanco, y dentro de cada bloque, por viñeta/encabezado/fila de tabla:
    # si no, un fichero de bullets se convierte en un párrafo de 10 000 caracteres que se descarta.
    out = []
    for block in re.split(r"\n\s*\n", txt):
        for sub in re.split(r"(?m)^(?=\s*(?:[-*]\s|#{2,4}\s|\|))", block):
            sub = sub.strip()
            if len(sub) >= 40:
                out.append(sub[:900])
    return out


def _corpus():
    docs = []
    seen = set()
    for base in BASES:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.suffix not in EXTS or not p.is_file() or p in seen:
                continue
            if any(x in str(p) for x in ("/out/", "/node_modules/", "/.git/", "/fixtures/", "/.cache/")):
                continue
            if re.fullmatch(r"[0-9a-f]{32,}", p.stem):   # cachés con nombre hash: no son memoria
                continue
            seen.add(p)
            for para in _paras(p):
                docs.append((p, para))
    # el vault está enlazado en dos rutas: deduplicar por contenido, no por ruta
    uniq, h = [], set()
    for path, para in docs:
        key = hash(re.sub(r"\s+", " ", para.lower()).strip())
        if key in h:
            continue
        h.add(key)
        uniq.append((path, para))
    return uniq


def search(query: str, k: int = 3, max_chars: int = 2200):
    terms = _tokens(query)
    docs = _corpus()
    if not terms or not docs:
        return []
    n = len(docs)
    df = {t: sum(1 for _, d in docs if t in d.lower()) for t in terms}
    # términos que aparecen en >35 % del corpus no distinguen nada
    terms = [t for t in terms if df.get(t, 0) <= 0.35 * n] or terms
    scored = []
    for path, para in docs:
        low = para.lower()
        s = 0.0
        hits = 0
        for t in terms:
            if t in low:
                tf = low.count(t)
                idf = math.log(1 + n / (1 + df[t]))
                s += idf * (1 + math.log(tf))
                hits += 1
        if s <= 0 or hits == 0:
            continue
        # longitud: un párrafo largo no vale más solo por ser largo
        s /= math.sqrt(len(low) / 400.0 + 1.0)
        # el nombre del fichero es señal fuerte
        if any(t in path.name.lower() for t in terms):
            s *= 1.35
        # un encabezado o un rótulo no responde nada
        if len(para) < 120 or para.rstrip().endswith(":"):
            s *= 0.55
        scored.append((s, path, para))
    scored.sort(key=lambda x: -x[0])
    out, used = [], 0
    for s, path, para in scored:
        if used + len(para) > max_chars and out:
            break
        out.append((str(path), para[:900], round(s, 2)))
        used += len(para)
        if len(out) >= k:
            break
    return out


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "¿cuántas cuentas usa el proxy NIM?"
    for f, p, s in search(q):
        print(f"--- {s} · {f}\n{p[:300]}\n")
