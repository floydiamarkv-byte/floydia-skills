#!/usr/bin/env python3
"""fanout_models.py — Fan-out multi-modelo a $0.00 vía OpenRouter :free.

POR QUÉ EXISTE
===============
Probado empiricamente el 2026-09-28 contra 8 modelos `:free` con una cuenta
OpenRouter a $0. Los 8 fallaron de forma DISTINTA. Este script existe para que
el fan-out no devuelva basura con apariencia de respuesta.

FALLAS REALES OBSERVADAS (con C6, saldo $0)
---------------------------------------------
  nvidia/nemotron-3-ultra-550b-a55b:free  -> limpio
  dots-studio/dots-3-note-preview:free      -> limpio
  nvidia/nemotron-3.5-lightning:free        -> devuelve el RAZONAMIENTO, no la respuesta
  cohere/north-mini-code:free               -> content=null, solo reasoning
  liquid/lfm-2.5-2.6b:free                  -> content=null, solo reasoning
  poolside/laguna-s-2.1:free                -> "Provider returned error"
  qwen/qwen3.8-27b:free                     -> 429 rate-limited upstream
  thinkingmachines/inkling-small:free       -> "only available on age-verified accounts"

CUEVENTAS:
  - `OPENROUTER_API_KEY`  -> C7. Trátala como la MISMA cuenta que C7.
  - `C7_OPENROUTER`, `C9_OPENROUTER` y `OPENROUTER_API_KEY` son la misma cuenta
    (hash SHA-256 idéntico). No las sumes como capacidad distinta.

GARANTÍAS
=========
  1. ASERCION DURA: solo se llama a modelos que acaban en ':free'. Un modelo de
     pago se ABORTA antes de la llamada (el error de saldo de OpenRouter es opaco:
     devuelve error sin `code` ni mensaje util).
  2. El fan-out NO depende del saldo: el free tier es del endpoint, no de la cuenta.
  3. NUNCA imprime valores de variables. Solo nombres de variable y estado.
  4. Red de seguridad: `SCRIPTS/safe_run_cli.sh` si existe, si no timeout propio.

USO
===
    python3 fanout_models.py --prompt "..." --models m1:free m2:free --max-words 200
    python3 fanout_models.py --prompt "..." --probe        # solo prueba minima
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
CREDITS_ENDPOINT = "https://openrouter.ai/api/v1/credits"

# Variables de cuenta, en orden de rotacion. C9 y OPENROUTER_API_KEY son alias
# de C7: se deduplican por hash abajo.
CANDIDATE_VARS = [
    "C1_OPENROUTER", "C2_OPENROUTER", "C3_OPENROUTER", "C4_OPENROUTER",
    "C5_OPENROUTER", "C6_OPENROUTER", "C7_OPENROUTER", "C9_OPENROUTER",
    "OPENROUTER_API_KEY",
]

# Modelos que devuelven contenido limpio (verificado 2026-09-28).
CLEAN_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "dots-studio/dots-3-note-preview:free",
]

# Modelos que requieren el normalizador (devuelven solo `reasoning`).
REASONING_ONLY_MODELS = [
    "cohere/north-mini-code:free",
    "liquid/lfm-2.5-2.6b:free",
    "nvidia/nemotron-3.5-lightning:free",
]

THINK_RE = re.compile(r"<think>.*?</think>", re.S | re.I)
LEAK_RE = re.compile(r"here'?s a thinking process.*?(?:\n\n|$)", re.S | re.I)


def load_secrets() -> None:
    """Carga el vault de secretos al entorno SIN imprimir nada."""
    path = os.path.expanduser("~/.secrets/antigravity.env")
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                if k and k not in os.environ and v.strip():
                    os.environ[k] = v.strip().strip("'\"")
    except OSError:
        pass


def resolve_accounts() -> list[tuple[str, str]]:
    """Devuelve [(nombre_visible, valor)] deduplicando cuentas alias.

    Deduplicar por hash es CRITICO: C7, C9 y OPENROUTER_API_KEY son la misma
    cuenta. Contarlas por separado infla la capacidad ficticiamente.
    """
    seen: dict[str, str] = {}
    out: list[tuple[str, str]] = []
    for var in CANDIDATE_VARS:
        val = os.environ.get(var, "").strip()
        if not val:
            continue
        digest = hashlib.sha256(val.encode()).hexdigest()[:12]
        if digest in seen:
            continue
        seen[digest] = var
        out.append((var, val))
    return out


def normalize_output(message: dict) -> str:
    """Convierte una respuesta de proveedor en texto usable.

    Cubre las 3 fallas de forma observada:
      - fuga de razonamiento en `content`  -> se recorta
      - `content` nulo                     -> se cae a `reasoning`
      - prefijos "Here's a thinking..."   -> se eliminan
    """
    content = (message.get("content") or "").strip()
    reasoning = (message.get("reasoning") or "").strip()

    if not content:
        if not reasoning:
            return ""
        content = reasoning

    content = THINK_RE.sub("", content).strip()
    content = LEAK_RE.sub("", content).strip()
    # Modelos de razonamiento a veces dejan el step final dentro de content.
    if content.lower().startswith("here's a thinking"):
        idx = content.lower().rfind("</think>")
        if idx != -1:
            content = content[idx + len("</think>"):].strip()
    return content.strip()


def truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " [...]"


def classify_error(msg: str) -> str:
    m = msg.lower()
    if "rate" in m or "429" in m:
        return "RATE_LIMIT"
    if "age" in m or "verif" in m:
        return "AGE_GATED"
    if "insufficient" in m or "credit" in m or "balance" in m:
        return "SIN_SALDO"
    if "provider returned error" in m:
        return "PROVIDER_ERROR"
    return "OTRO"


def call_model(api_key: str, model: str, prompt: str, max_tokens: int, timeout: int) -> dict:
    """Una llamada. Devuelve dict con status/texto/error. Nunca lanza."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        ENDPOINT, data=payload, method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="ignore")
        try:
            msg = json.loads(raw).get("error", {}).get("message", raw)
        except Exception:
            msg = raw
        return {"status": "ERROR", "error": classify_error(str(msg)), "detail": str(msg)[:200]}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"status": "ERROR", "error": "RED", "detail": str(exc)[:200]}

    if body.get("error"):
        msg = str(body["error"].get("message", body["error"]))
        return {"status": "ERROR", "error": classify_error(msg), "detail": msg[:200]}

    try:
        message = body["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return {"status": "ERROR", "error": "ESQUEMA", "detail": "respuesta sin choices[0].message"}

    text = normalize_output(message)
    if not text:
        return {"status": "VACIO", "error": "SIN_CONTENIDO",
                "detail": "content y reasoning ambos vacios tras normalizar"}
    return {"status": "OK", "text": text,
            "usage": body.get("usage", {}).get("total_tokens")}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fan-out multi-modelo $0.00")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--models", nargs="*", default=None,
                    help=f"Default: {CLEAN_MODELS}")
    ap.add_argument("--max-words", type=int, default=250)
    ap.add_argument("--max-tokens", type=int, default=500)
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--probe", action="store_true",
                    help="Prueba minima: 5 palabras, valida el pipeline")
    args = ap.parse_args()

    load_secrets()
    accounts = resolve_accounts()
    if not accounts:
        print(json.dumps({"error": "SIN_CUENTAS",
                          "detalle": "ninguna variable OpenRouter definida"}))
        return 1

    models = args.models or CLEAN_MODELS
    prompt = "Responde solo: OK" if args.probe else args.prompt
    max_words = 5 if args.probe else args.max_words

    # ASERCION DURA: nunca llamar a un modelo de pago (Contrato #9).
    paid = [m for m in models if not m.endswith(":free")]
    if paid:
        print(json.dumps({
            "error": "MODELO_NO_FREE",
            "detalle": "estos modelos no son :free y se aborta antes de llamar; "
                       "el error de saldo de OpenRouter es opaco",
            "modelos_rechazados": paid,
            "cuentas_disponibles": [n for n, _ in accounts],
        }, ensure_ascii=False, indent=2))
        return 2

    findings: list[dict] = []
    for idx, model in enumerate(models):
        var, key = accounts[idx % len(accounts)]
        for attempt in range(1, args.retries + 1):
            result = call_model(key, model, prompt, args.max_tokens, args.timeout)
            if result["status"] == "OK":
                result["intentos"] = attempt
                break
            if result["error"] in ("RATE_LIMIT", "PROVIDER_ERROR", "RED"):
                if attempt < args.retries:
                    time.sleep(2 ** attempt)  # backoff exponencial
                    continue
            result["intentos"] = attempt
            break
        else:
            result = {"status": "ERROR", "error": "REINTENTOS_AGOTADOS"}
        # La cuenta se etiqueta DESPUES del bucle: un reintento sobrescribe
        # `result` y perderiamos de que cuenta vino la respuesta.
        result["model"] = model
        result["cuenta"] = var
        if result["status"] == "OK":
            result["text"] = truncate_words(result["text"], max_words)
            result["word_count"] = len(result["text"].split())
        findings.append(result)

    ok = [f for f in findings if f["status"] == "OK"]
    out = {
        "consultas": len(findings),
        "ok": len(ok),
        "fallidas": len(findings) - len(ok),
        "cuentas_usadas": sorted({f["cuenta"] for f in findings}),
        "cuentas_reales": len(accounts),
        "findings": findings,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
