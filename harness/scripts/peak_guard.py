#!/usr/bin/env python3
"""Guardia de ventana peak: en las horas pico, el modelo principal baja a v4-pro.

Hecho medido (2026-11-07): en peak (01-04 y 06-10 UTC, L-V) `deepseek-v4.1-flash`
devuelve 429 `overloaded` con frecuencia, mientras `deepseek-v4-pro` responde 200 en
1,9 s. La conmutación es idempotente y deja un estado auditable.

Uso:
    python3 SCRIPTS/peak_guard.py --check    # decisión sin tocar nada
    python3 SCRIPTS/peak_guard.py --apply    # conmuta solo si toca
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ / "SCRIPTS"))
import harness_switch as hs  # noqa: E402

STATE = PROJ / ".session/peak_guard_state.json"
PEAK = [("01:00", "04:00"), ("06:00", "10:00")]   # UTC, lunes a viernes
ON_PEAK = {"default": "deepseek-v4-pro", "provider": "opencode-go"}
OFF_PEAK = {"default": "deepseek-v4.1-flash", "provider": "opencode-go"}


def _in_peak(now: datetime) -> bool:
    if now.weekday() >= 5:          # sábado/domingo
        return False
    hm = now.astimezone(timezone.utc).strftime("%H:%M")
    return any(a <= hm < b for a, b in PEAK)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    peak = _in_peak(now)
    d, p = hs.current()
    target = ON_PEAK if peak else OFF_PEAK
    action = "conmutar" if (d, p) != (target["default"], target["provider"]) else "nada"
    res = {"at": now.isoformat(), "peak": peak, "actual": {"default": d, "provider": p},
           "objetivo": target, "accion": action}
    if a.apply and action == "conmutar":
        modo = "PRO" if peak else "GO"
        ms = hs.switch(modo)
        res["switched"] = True
        res["ms"] = round(ms, 2)
    if a.apply:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
