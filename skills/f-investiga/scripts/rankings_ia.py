#!/usr/bin/env python3
"""rankings_ia.py — Rankings de IA, precios y catalogo, verificados en runtime.

POR QUE EXISTE
==============
El objetivo del skill incluye responder "cuales son los ultimos modelos" con
datos ACTUALES. Documentar que LMArena existe no es lo mismo que servir el dato.

REGLA EPISTEMICA CENTRAL (verificada 2026-09-28)
=================================================
NO SE FUSIONAN DIMENSIONES DISTINTAS EN UN UNICO SCORE. Evidencia dura:
  - mismo modelo, Terminal-Bench 4.0: 83.4 % con Codex CLI vs 76.4 % con Terminus 2
    => "modelo" != "modelo + andamiaje"
  - LMArena mide PREFERENCIA HUMANA (Elo), no exactitud
  - Artificial Analysis da Intelligence Index y Elo de media para el mismo slug
  - latencia/throughput es POR ENDPOINT: promediar entre proveedores es invalido
  - puntuacion absoluta entre benchmarks distintos NO es comparable

SALIDAS
=======
  HECHO  -> dato leido de una fuente primaria en ESTA ejecucion
  VACIO  -> la fuente no tiene ese campo (no "no existe")
  NULO   -> la fuente no responde (no es un dato, es un fallo de red)

USO
===
    python3 rankings_ia.py --arena text --top 15
    python3 rankings_ia.py --precios
    python3 rankings_ia.py --agentes
    python3 rankings_ia.py --todo
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0"
HECHO, VACIO, NULO = "HECHO", "VACIO", "NULO"

# Las 22 configs del dataset oficial de LMArena.
LMArena_CONFIGS = [
    "text", "text_factuality", "text_style_control",
    "code", "vision", "document", "search", "search_factuality",
    "webdev", "text_to_image", "image_edit", "text_to_video", "video_edit",
    "agent", "agent_task_outcome_explicit", "agent_praise_complaint",
    "agent_steerability", "agent_tool_hallucination", "agent_bash_recovery_steps",
    "image_to_video", "vision_style_control", "document_style_control",
]


def _get(url: str, timeout: int = 20) -> dict:
    """GET JSON. Nunca lanza: devuelve {"_error": ...} para distinguir fallo
    de dato ausente (que es info distinto)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                  "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"_json": json.loads(r.read().decode() or "{}"), "_status": r.status}
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"_error": type(e).__name__}
    except json.JSONDecodeError:
        return {"_error": "respuesta no es JSON"}


# ------------------------------------------------------------ rankings LMArena

def arena(config: str = "text", top: int = 15) -> dict:
    """Ranking oficial de LMArena via su dataset publico en HuggingFace.

    FUENTE PRIMARIA. LMArena no tiene API REST: su propio blog declara que el
    dataset HF es la via de acceso publico. `robots.txt` prohibe /api/.
    Verificado 2026-09-28: CC-BY-4.0, lastModified 2026-09-28, 52.819 descargas.
    """
    cfg = config if config in LMArena_CONFIGS else "text"
    url = ("https://datasets-server.huggingface.co/rows?dataset="
           "lmarena-ai%2Fleaderboard-dataset"
           f"&config={cfg}&split=latest&offset=0&length={min(top, 100)}")
    r = _get(url)
    if "_error" in r:
        return {"fuente": "LMArena (HF datasets-server)", "config": cfg,
                "estado": NULO, "detalle": r["_error"], "aviso": DIMS["arena"]}
    rows = r["_json"].get("rows", [])
    # HALLAZGO 2026-09-28: el dataset tiene DOS esquemas distintos y mixing
    # them rompe el informe.
    #   configs de texto/vision/etc: rating (Elo), rating_lower/upper, vote_count
    #   configs de AGENTE:           score (0-1), score_ci_lower/upper,
    #                              observation_count, session_count
    out = []
    es_agente = "rating" not in (rows[0].get("row", {}) if rows else {})
    for row in rows:
        x = row.get("row", {})
        if es_agente:
            out.append({
                "rank": x.get("rank"), "modelo": x.get("model_name"),
                "org": x.get("organization"), "licencia": x.get("license"),
                "score": x.get("score"),
                "rango_ic": [x.get("score_ci_lower"), x.get("score_ci_upper")],
                "observaciones": x.get("observation_count"),
                "sesiones": x.get("session_count"),
                "fecha_ranking": x.get("leaderboard_publish_date"),
            })
        else:
            out.append({
                "rank": x.get("rank"), "modelo": x.get("model_name"),
                "org": x.get("organization"), "licencia": x.get("license"),
                "elo": x.get("rating"),
                "rango_ic": [x.get("rating_lower"), x.get("rating_upper")],
                "votos": x.get("vote_count"),
                "fecha_ranking": x.get("leaderboard_publish_date"),
            })
    dim = ("TASA DE EXITO en tareas de agente (score 0-1), no Elo. NO es "
           "comparable con el rating de las configs de texto."
           if es_agente else
           "PREFERENCIA HUMANA (Elo). No es exactitud, no es rendimiento, no es precio.")
    return {"fuente": "LMArena (dataset oficial en HF)", "config": cfg,
            "estado": HECHO if out else VACIO,
            "esquema": "AGENTE (score 0-1)" if es_agente else "TEXTO (Elo)",
            "lecturado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "dimension": dim, "aviso": DIMS["arena"],
            "resultados": out}


# ------------------------------------------------------------------- precios

def precios(top: int = 20, solo_con_precio: bool = True) -> dict:
    """Catalogo y precios via OpenRouter. SIN API KEY (verificado).

    BUG REAL cazado por la prueba E2E: los modelos ':free' tienen prompt='0' o
    vacio, asi que el filtro `solo_con_precio` los excluia y el contador
    `gratis_disponibles` salia en 0 cuando hay 16. Ahora se(info de ellos
    aparte: son los que permite usar el fan-out a coste $0.00.
    """
    r = _get("https://openrouter.ai/api/v1/models")
    if "_error" in r:
        return {"fuente": "OpenRouter /api/v1/models", "estado": NULO,
                "detalle": r["_error"]}
    data = r["_json"].get("data", [])
    filas, gratis_lista = [], []
    for m in data:
        p = m.get("pricing") or {}
        try:
            prompt = float(p.get("prompt", 0) or 0)
        except (TypeError, ValueError):
            prompt = 0.0
        es_gratis = m.get("id", "").endswith(":free")
        if es_gratis:
            gratis_lista.append({"modelo": m.get("id"),
                                 "contexto": m.get("context_length")})
        if solo_con_precio and prompt <= 0:
            continue
        filas.append({
            "modelo": m.get("id"),
            "contexto": m.get("context_length"),
            "prompt_1M_usd": round(prompt * 1_000_000, 4) if prompt else 0,
            "completion_1M_usd": round(float(p.get("completion", 0) or 0) * 1_000_000, 4),
            "gratis": m.get("id", "").endswith(":free"),
            "hf_id": m.get("hugging_face_id"),
        })
    filas.sort(key=lambda x: x["prompt_1M_usd"])
    return {"fuente": "OpenRouter /api/v1/models (sin key)", "estado": HECHO,
            "lecturado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "aviso": DIMS["precio"],
            "total_modelos": len(data), "modelos_con_precio": len(filas),
            "gratis_disponibles": len(gratis_lista),
            "modelos_gratis": gratis_lista,
            "resultados": filas[:top]}


# ----------------------------------------------------- rankings de agentes

AGENTES_SEGUROS = [
    ("Terminal-Bench 4.0", "https://www.tbench.ai/leaderboard",
     "Agente + modelo + resolucion. OJO: same model != same score."),
    ("METR time horizons", "https://metr.org/time-horizons/",
     "Horas de trabajo autonome antes de degradarse."),
    ("SWE-bench Verified", "https://www.swebench.com/verified.html",
     "500 instancias validadas de resolucion de issues reales."),
    ("LiveCodeBench", "https://livecodebench.github.io/leaderboard.html",
     "Contaminacion controlada por fecha de release."),
    ("Aider polyglot", "https://aider.chat/docs/leaderboards/",
     "Edicion de codigo multi-lenguaje."),
    ("Epoch AI", "https://epoch.ai/benchmarks",
     "Metodologia abierta, datos reproducibles."),
]


def agentes() -> dict:
    """NO extrae cifras: comprueba que cada leaderboard SIGUE VIVO.

    Razon: las cifras de estos sitios cambian y HTML cambia de forma. Extraer
    numeros de una tabla sin API produce verificacion falsa. Este script
    responde "existe y responde", y marca explicitamente que no extrae scores.
    """
    filas = []
    for nombre, url, nota in AGENTES_SEGUROS:
        r = _get(url, timeout=15)
        if "_error" in r:
            filas.append({"leaderboard": nombre, "url": url, "estado": NULO,
                          "detalle": r["_error"], "nota": nota})
        else:
            filas.append({"leaderboard": nombre, "url": url, "estado": HECHO,
                          "http": r.get("_status"), "nota": nota,
                          "cifras": "NO EXTRAIDAS: sin API oficial. Consultar la URL."})
    return {"fuente": "leaderboards de agentes", "estado": HECHO,
            "lecturado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "aviso": "Este script comprueba VIVENCIA, no extrae puntuaciones. "
                     "Un score sacado de HTML sin API es verificacion falsa.",
            "resultados": filas}


# --------------------------------------------------- fuentes NO combinables

DIMS = {
    "arena": "Elo = PREFERENCIA HUMANA. No es exactitud, no es rendimiento, no es precio. "
             "Los intervalos [lower, upper] indican confianza estadistica: si se solapan, "
             "el orden entre ambos modelos NO es significativo.",
    "precio": "Precio por 1M de tokens NO es coste por tarea. El coste real depende de "
              "tokens consumidos y numero de intentos. ':free' significa que el endpoint "
              "no cobra; no que el modelo sea de calidad inferior.",
    "agente": "Un score de agente depende del arnes. El mismo modelo dio 83.4 % con "
              "Codex CLI y 76.4 % con Terminus 2 en la MISMA version de Terminal-Bench 4.0.",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Rankings de IA, precios y agentes")
    ap.add_argument("--arena", metavar="CONFIG", nargs="?", const="text",
                    choices=LMArena_CONFIGS + list(LMArena_CONFIGS),
                    help=f"Config LMArena. Disponibles: {', '.join(LMArena_CONFIGS)}")
    ap.add_argument("--precios", action="store_true")
    ap.add_argument("--agentes", action="store_true")
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    if not any([args.arena, args.precios, args.agentes, args.todo]):
        args.todo = True

    out = {"generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "principio": "Las dimensiones NO se fusionan en un unico score. "
                        "Cada fuente se lee de forma primaria y se etiqueta."}
    if args.todo or args.arena:
        out["arena"] = arena(args.arena or "text", args.top)
    if args.todo or args.precios:
        out["precios"] = precios(args.top)
    if args.todo or args.agentes:
        out["agentes_de_codigo"] = agentes()

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
