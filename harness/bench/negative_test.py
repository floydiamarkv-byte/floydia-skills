#!/usr/bin/env python3
"""Prueba negativa del coste cero (§5.6) — criterio de aceptación.

1) modelo de pago por el cortafuegos C7  -> debe abortar (exit 2), no degradar.
2) ID muerto en NIM                       -> 404 ruidoso, sin fallback silencioso.
3) allowlist podrida                      -> exit 2.
4) sin delta de allowance en GET /usage durante la corrida.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
PROJ = Path("<PROYECTO>")
sys.path.insert(0, str(PROJ / "SCRIPTS"))
sys.path.insert(0, str(ROOT))

from c7_free_client import (get_c7_client, C7SyntaxViolationError,  # noqa: E402
                            C7AllowlistViolationError, C7VetoViolationError)


def usage():
    r = subprocess.run([sys.executable, str(PROJ / "SCRIPTS/opencode_go_usage_api.py"), "--json"],
                       capture_output=True, text=True, timeout=60)
    d = json.loads(r.stdout)
    return {w["window"]: w["percent"] for w in d["windows"]}, r.returncode


def dead_id_probe():
    body = {"model": "nvidia/nemotron-3-super-120b-a12b",
            "messages": [{"role": "user", "content": "ping"}], "max_tokens": 8}
    req = urllib.request.Request("http://127.0.0.1:8088/v1/chat/completions",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.load(r)
        served = (d.get("model") or "")
        return {"http": 200, "served": served, "silent_fallback": served != body["model"],
                "ms": int((time.time() - t0) * 1000)}
    except Exception as e:  # noqa: BLE001
        code = getattr(e, "code", None)
        detail = ""
        try:
            detail = e.read().decode()[:300]  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            detail = str(e)
        return {"http": code, "loud": code is not None and code >= 400, "body": detail,
                "ms": int((time.time() - t0) * 1000)}


def main():
    before, rc1 = usage()
    res = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "usage_before": before, "usage_cmd_rc": rc1}

    client = get_c7_client()
    cases = [
        ("pago_sin_free", "openai/gpt-4o", C7SyntaxViolationError),
        ("sufijo_nitro", "meta-llama/llama-3.3-70b-instruct:nitro", C7SyntaxViolationError),
        ("free_fuera_allowlist", "deepseek/deepseek-r1:free", C7AllowlistViolationError),
    ]
    results = []
    for name, model, exc in cases:
        try:
            client.validate_model_syntax(model)
            if exc is C7AllowlistViolationError:
                client.validate_allowlist(model)
            results.append({"case": name, "aborted": False, "model": model,
                            "verdict": "FALLO: no abortó"})
        except exc as e:  # noqa: PERF203
            results.append({"case": name, "aborted": True, "model": model, "error": str(e)[:200]})
        except Exception as e:  # noqa: BLE001
            results.append({"case": name, "aborted": True, "model": model,
                            "error": f"{type(e).__name__}: {e}"[:200]})
    res["c7_cases"] = results
    res["exit_code_paid_model"] = 0 if all(r["aborted"] for r in results) else 2

    res["dead_id"] = dead_id_probe()
    after, rc2 = usage()
    res["usage_after"] = after
    res["usage_delta"] = {k: round(after[k] - before.get(k, 0), 3) for k in after}
    res["pass"] = (res["exit_code_paid_model"] == 0 and res["dead_id"].get("loud")
                   and all(v == 0 for v in res["usage_delta"].values()))
    (OUT / "negative_test.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))
    sys.exit(0 if res["pass"] else 2)


if __name__ == "__main__":
    main()
