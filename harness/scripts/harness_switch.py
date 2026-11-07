#!/usr/bin/env python3
"""Conmutador GO ⇄ FREE del harness, con escritura atómica y medición de latencia.

GO   → opencode-go / deepseek-v4.1-flash        (consume bolsa)
FREE → nim_local   / deepseek-ai/deepseek-v4.1-flash  ($0,00)

Uso:
    python3 SCRIPTS/harness_switch.py --status
    python3 SCRIPTS/harness_switch.py --mode FREE
    python3 SCRIPTS/harness_switch.py --bench 40        # mide P50/P95/P99 y deja GO
"""
from __future__ import annotations

import argparse
import os
import re
import statistics
import sys
import time
from pathlib import Path

CFG = Path.home() / ".hermes/config.yaml"
MODES = {
    "GO": {"default": "deepseek-v4.1-flash", "provider": "opencode-go"},
    "PRO": {"default": "deepseek-v4-pro", "provider": "opencode-go"},
    "FREE": {"default": "deepseek-ai/deepseek-v4.1-flash", "provider": "nim_local"},
}
BLOCK = re.compile(r'(?ms)^model:\n  default: "[^"]*"\n  provider: "[^"]*"\n')


def current() -> tuple[str, str]:
    block = BLOCK.search(CFG.read_text(encoding="utf-8"))
    if block is None:
        raise SystemExit("config sin bloque model: reconocible")
    texto = block.group(0)
    md = re.search(r'default: "([^"]*)"', texto)
    mp = re.search(r'provider: "([^"]*)"', texto)
    if md is None or mp is None:
        raise SystemExit("bloque model: incompleto")
    return md.group(1), mp.group(1)


def switch(mode: str) -> float:
    """Reescribe el bloque model con escritura atómica. Devuelve ms."""
    mode = mode.upper()
    if mode not in MODES:
        raise SystemExit(f"modo inválido: {mode}")
    t0 = time.perf_counter()
    txt = CFG.read_text(encoding="utf-8")
    tgt = MODES[mode]
    if not BLOCK.search(txt):
        raise SystemExit("config sin bloque model: reconocible")
    new = BLOCK.sub(f'model:\n  default: "{tgt["default"]}"\n  provider: "{tgt["provider"]}"\n', txt, count=1)
    tmp = CFG.with_suffix(".yaml.tmp")
    tmp.write_text(new, encoding="utf-8")
    os.replace(tmp, CFG)          # atómico: nunca queda un config a medias
    return (time.perf_counter() - t0) * 1000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--bench", type=int, default=0)
    a = ap.parse_args()
    if a.status or (not a.mode and not a.bench):
        d, p = current()
        m = "GO" if p.startswith("opencode") else ("FREE" if p == "nim_local" else "?")
        print(f"modo={m} default={d} provider={p}")
        return 0
    if a.mode:
        ms = switch(a.mode)
        d, p = current()
        print(f"→ {a.mode.upper()} · {d} @ {p} · {ms:.1f} ms")
        return 0
    if a.bench:
        orig = current()
        lat = []
        for i in range(a.bench):
            for m in ("FREE", "GO") if i % 2 == 0 else ("GO", "FREE"):
                lat.append(switch(m))
        d, p = current()
        if p != MODES["GO"]["provider"]:
            switch("GO")
        lat.sort()
        def pct(q):
            return lat[min(len(lat) - 1, int(round(q * (len(lat) - 1))))]
        res = {"n_switches": len(lat), "p50_ms": round(statistics.median(lat), 2),
               "p95_ms": round(pct(0.95), 2), "p99_ms": round(pct(0.99), 2),
               "max_ms": round(lat[-1], 2), "final": current()}
        import json
        print(json.dumps(res, ensure_ascii=False))
        (Path(__file__).resolve().parent.parent / "scratch/harness_v51/out/switch_bench.json").write_text(
            json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        return 0 if res["p99_ms"] <= 5000 else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
