#!/usr/bin/env python3
"""Aplica la gramática [ESTADO][CTX][MODO] a los display names de opencode.jsonc.

Los campos ESTADO y CTX salen del registro con TTL, nunca se teclean (§8).
Uso: python3 SCRIPTS/apply_model_names.py [--apply]
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = Path.home() / ".config/opencode/opencode.jsonc"
REG = ROOT / "scratch/harness_v51/out/model_state_registry.json"
TAG = re.compile(r"^(?:\[[^\]]*\]\s*)+")   # varias etiquetas seguidas


def ctx_tag(v: int) -> str:
    """Etiqueta canónica: 1M para 1 000 000/1 048 576; k exacta si es múltiplo de 1000."""
    if v >= 999_500:
        return f"{round(v / 1_000_000)}M"
    if v % 1000 == 0:
        return f"{round(v / 1000)}k"
    return f"{round(v / 1024)}k"


def base_name(old: str, mid: str) -> str:
    return TAG.sub("", old).strip() or mid.split("/")[-1].replace("-", " ").title()


def main() -> int:
    apply = "--apply" in sys.argv
    reg = {}
    for e in json.loads(REG.read_text())["entries"]:
        reg[e["id"]] = e
        if e["id"].startswith("nim/"):
            reg["nim_local/" + e["id"][4:]] = e
    lines = CFG.read_text(encoding="utf-8").splitlines()
    prov = mid = None
    out, changed, missing, in_models, pending, purgado = [], 0, [], False, [], []
    pending_ctx = None
    for ln in lines:
        mp = re.match(r'^    "([a-z0-9_]+)":\s*\{$', ln)
        if mp:
            prov, in_models, mid = mp.group(1), False, None
        if re.match(r'^      "models":\s*\{$', ln):
            in_models = True
        mk = re.match(r'^        "([^"]+)":\s*\{$', ln)
        if in_models and mk:
            mid = mk.group(1)
            pending_ctx = None   # un "context" huérfano no debe caer en el modelo siguiente
        mn = re.match(r'^(\s+"name": ")(.*)("(,?))$', ln)
        if mn and mid and prov:
            key = f"{prov}/{mid}"
            e = reg.get(key)
            if not e:
                missing.append(key)
                out.append(ln)
                continue
            real, decl = e.get("ctx_real"), e.get("ctx_declarado")
            if not real:
                if e.get("existe") is False:
                    estado = "RETIRED"
                elif e.get("existe") is None:
                    estado = "?"
                else:
                    estado = "OK" if e.get("estado") == "ACTIVE" else e.get("estado", "DEGRADED")
                mode = "GO" if prov.startswith("opencode_go") else "F"
                new = f"{mn.group(1)}[{estado}][?][{mode}] {base_name(mn.group(2), mid)}{mn.group(3)}"
                changed += 1
                out.append(new)
                pending_ctx = None
                continue
            if decl and ctx_tag(int(real)) != ctx_tag(int(decl)) and abs(int(real) - int(decl)) / int(real) > 0.02:
                purgado.append((key, int(decl), int(real)))
            if e.get("existe") is False:
                estado = "RETIRED"
            elif e.get("existe") is None:
                estado = "?"          # existencia no verificada: no se afirma ni se retira
            else:
                estado = "OK" if e.get("estado") == "ACTIVE" else e.get("estado", "DEGRADED")
            mode = "GO" if prov.startswith("opencode_go") else "F"
            new = f"{mn.group(1)}[{estado}][{ctx_tag(int(e.get('ctx_real') or 0))}][{mode}] {base_name(mn.group(2), mid)}{mn.group(3)}"
            pending_ctx = int(real)
            if new != ln:
                changed += 1
                if changed <= 6:
                    print(f"  {key}\n    antes : {mn.group(2)}\n    después: {new.strip()}")
            out.append(new)
            continue
        mc = re.match(r'^(\s+"context": )(\d+)(,?)$', ln)
        if mc and pending_ctx:
            out.append(f'{mc.group(1)}{pending_ctx}{mc.group(3)}')
            pending_ctx = None
            continue
        out.append(ln)
    print(f"\nmodelos con nombre reescrito: {changed} · sin registro: {len(missing)} · pendientes de decisión: {len(pending)}")
    for k, d, r in purgado:
        print(f"  ctx purgado {k}: {d} → {r}")
    if missing[:5]:
        print("  sin registro:", missing[:5])
    if not apply:
        print("(dry-run; usa --apply)")
        return 0
    bak = CFG.with_suffix(f".jsonc.bak-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(CFG, bak)
    CFG.write_text("\n".join(out) + "\n", encoding="utf-8")
    # validación sintáctica: quitar comentarios de línea y parsear
    raw = CFG.read_text(encoding="utf-8")
    stripped = "\n".join(re.sub(r'^\s*//.*$', '', l) for l in raw.splitlines())
    json.loads(stripped)
    print(f"APLICADO · backup {bak.name} · JSONC válido · {len(out)} líneas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
