#!/usr/bin/env python3
"""
env_loader.py — Parser UNIFORME y ROBUSTO del SSOT `.env` del workspace.

CONTEXTO
--------
El SSOT es `~/.secrets/antigravity.env` (symlink `.env` del workspace).
Desde 2026-10-20 las variables de API llevan un comentario inline
`# endpoint: <base_url>` al final de la linea.

PROBLEMA QUE RESUELVE
---------------------
Los parsers ingenuos del tipo:

    k, v = line.split("=", 1)
    v = v.strip().strip('"').strip("'")

rompen con comentarios inline: se quedan con `[REDACTED]" # endpoint: url`.

Este modulo implementa la semantica de shell (bash/dotenv):
  · valor entre comillas  -> se respeta el contenido literal hasta la comilla
  · valor sin comillas     -> el comentario empieza en '#' precedido de espacio
  · `export` opcional, espacios alrededor de '='
  · lineas vacias / comentarios se ignoran
  · NO se imprimen valores: solo se devuelven para uso en memoria.

USO
---
    import sys; sys.path.insert(0, "<PROYECTO>/SCRIPTS")
    from env_loader import load_env, env_line
    env = load_env()          # dict[str, str]
    k, v = env_line(raw_line) # (clave, valor_limpio)
"""
from __future__ import annotations

import os
from pathlib import Path

ENV_SSOT = Path("~/.secrets/antigravity.env")
ENV_WORKSPACE = Path("<PROYECTO>/.env")

__all__ = ["ENV_SSOT", "ENV_WORKSPACE", "env_line", "load_env", "env_value", "iter_env"]


def env_value(raw: str) -> str:
    """Limpia el valor de una asignacion `KEY=VALUE` tolerando comentarios inline.

    - `KEY="v" # comentario`  -> `v`
    - `KEY=v # comentario`    -> `v`
    - `KEY='v'`               -> `v`
    - `KEY=v#nospace`         -> `v#nospace`  (shell no trata '#' sin espacio como comentario)
    """
    s = raw.strip()
    if not s:
        return ""
    if s[0] in "\"'":
        quote = s[0]
        end = s.find(quote, 1)
        if end != -1:
            return s[1:end]
        # comilla sin cerrar: se toma el resto tal cual
        return s[1:]
    # sin comillas: comentario inline solo si '#' va precedido de espacio/tab
    for i, ch in enumerate(s):
        if ch == "#" and i > 0 and s[i - 1] in " \t":
            return s[:i].rstrip()
    return s


def env_line(raw: str) -> tuple[str, str]:
    """Devuelve (clave, valor_limpio) de una linea `KEY=VALUE`.

    Si la linea no es una asignacion valida devuelve ('', '').
    """
    s = raw.strip()
    if not s or s.startswith("#"):
        return "", ""
    if s.startswith("export "):
        s = s[7:].lstrip()
    if "=" not in s:
        return "", ""
    k, v = s.split("=", 1)
    k = k.strip()
    if not k or not (k[0].isalpha() or k[0] == "_"):
        return "", ""
    return k, env_value(v)


def iter_env(path: str | os.PathLike | None = None):
    """Itera (clave, valor) sobre el fichero .env indicado (SSOT por defecto)."""
    p = Path(path) if path else ENV_SSOT
    if not p.exists():
        p = ENV_WORKSPACE
    with p.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            k, v = env_line(raw)
            if k:
                yield k, v


def load_env(path: str | os.PathLike | None = None) -> dict[str, str]:
    """Carga el .env como dict. La ultima aparicion de una clave prevalece."""
    env: dict[str, str] = {}
    for k, v in iter_env(path):
        if v:
            env[k] = v
    return env


if __name__ == "__main__":
    import hashlib
    import json
    import sys

    env = load_env()
    fp = {k: hashlib.sha256(v.encode()).hexdigest()[:12] for k, v in sorted(env.items())}
    if "--json" in sys.argv:
        print(json.dumps(fp, indent=1))
    else:
        print(f"claves cargadas: {len(fp)}")
        for k, h in fp.items():
            print(f"{k:44s} {h}")
