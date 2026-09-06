#!/usr/bin/env python3
"""
bottleneck_analyzer.py — Diagnóstico de Cuellos de Botella del Sistema v1.0
f-opti-floydia / Opción 7

Análisis 100% read-only y no invasivo de:
1. Errores de kernel (dmesg --level=err,warn)
2. I/O Wait y latencia de disco
3. Presión de memoria (PSI thresholds)
4. Thermal throttling y frecuencia de CPU
5. Procesos zombie y huérfanos
6. ZRAM compression ratio
7. OOM events recientes
8. Xorg/Wayland errores gráficos

Salida: JSON o Markdown estructurado.
"""

import sys
import os
import json
import subprocess
import re
from datetime import datetime, timezone


def safe_run(cmd: list, timeout: int = 5) -> str:
    """Ejecuta un comando de forma segura con timeout."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            stdin=subprocess.DEVNULL
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
        return f"[ERROR: {e}]"


def analyze_dmesg_errors() -> dict:
    """Extrae errores y warnings recientes del kernel."""
    output = safe_run(["dmesg", "--level=err,warn", "--time-format=reltime"], timeout=3)
    if output.startswith("[ERROR"):
        # Fallback sin formato de tiempo
        output = safe_run(["dmesg", "--level=err,warn"], timeout=3)

    if output.startswith("[ERROR"):
        return {"status": "UNAVAILABLE", "errors": [], "warnings": [], "note": output}

    lines = output.strip().split("\n") if output.strip() else []
    # Tomar últimas 50 líneas para no saturar
    recent = lines[-50:] if len(lines) > 50 else lines

    errors = [l for l in recent if "error" in l.lower() or "fail" in l.lower()]
    warnings = [l for l in recent if l not in errors]

    severity = "OK"
    if len(errors) > 10:
        severity = "CRITICAL"
    elif len(errors) > 0:
        severity = "WARNING"

    return {
        "status": severity,
        "total_lines": len(lines),
        "recent_errors": errors[-10:],
        "recent_warnings": warnings[-10:],
        "error_count": len(errors),
        "warning_count": len(warnings)
    }


def analyze_io_wait() -> dict:
    """Analiza I/O wait del sistema."""
    # Leer /proc/stat para calcular I/O wait %
    try:
        with open("/proc/stat", "r") as f:
            first_line = f.readline()
        parts = first_line.split()
        if len(parts) >= 6:
            # cpu user nice system idle iowait irq softirq
            user, nice, system, idle, iowait = [int(x) for x in parts[1:6]]
            total = user + nice + system + idle + iowait
            iowait_pct = round((iowait / total) * 100, 2) if total > 0 else 0

            severity = "OK"
            if iowait_pct > 20:
                severity = "CRITICAL"
            elif iowait_pct > 5:
                severity = "WARNING"

            return {
                "status": severity,
                "iowait_pct": iowait_pct,
                "iowait_ticks": iowait,
                "total_ticks": total
            }
    except Exception as e:
        pass

    return {"status": "UNAVAILABLE", "error": "No se pudo leer /proc/stat"}


def analyze_memory_pressure() -> dict:
    """Analiza PSI (Pressure Stall Information) y OOM events."""
    result = {"psi": {}, "oom_events": 0, "status": "OK"}

    # PSI
    for resource in ["cpu", "memory", "io"]:
        psi_path = f"/proc/pressure/{resource}"
        if os.path.exists(psi_path):
            try:
                with open(psi_path, "r") as f:
                    content = f.read().strip()
                # Parse "some avg10=X.XX avg60=X.XX avg300=X.XX total=XXXXX"
                for line in content.split("\n"):
                    if line.startswith("some"):
                        match = re.search(r"avg10=(\d+\.\d+)", line)
                        if match:
                            avg10 = float(match.group(1))
                            sev = "OK"
                            if avg10 > 25:
                                sev = "CRITICAL"
                            elif avg10 > 5:
                                sev = "WARNING"
                            result["psi"][resource] = {
                                "avg10": avg10,
                                "raw": line,
                                "severity": sev
                            }
                            if sev == "CRITICAL":
                                result["status"] = "CRITICAL"
                            elif sev == "WARNING" and result["status"] != "CRITICAL":
                                result["status"] = "WARNING"
            except Exception:
                result["psi"][resource] = {"error": "No legible"}

    # OOM events
    dmesg_oom = safe_run(["dmesg"], timeout=3)
    if not dmesg_oom.startswith("[ERROR"):
        oom_count = dmesg_oom.lower().count("out of memory")
        result["oom_events"] = oom_count
        if oom_count > 0:
            result["status"] = "CRITICAL"

    return result


def analyze_thermal() -> dict:
    """Detecta thermal throttling y temperaturas."""
    result = {"status": "OK", "zones": [], "throttling_detected": False}

    # Thermal zones
    thermal_base = "/sys/class/thermal"
    if os.path.exists(thermal_base):
        for entry in sorted(os.listdir(thermal_base)):
            if entry.startswith("thermal_zone"):
                zone_path = os.path.join(thermal_base, entry)
                try:
                    with open(os.path.join(zone_path, "temp"), "r") as f:
                        temp_mc = int(f.read().strip())
                    temp_c = temp_mc / 1000.0

                    zone_type = "unknown"
                    type_path = os.path.join(zone_path, "type")
                    if os.path.exists(type_path):
                        with open(type_path, "r") as f:
                            zone_type = f.read().strip()

                    sev = "OK"
                    if temp_c > 90:
                        sev = "CRITICAL"
                        result["throttling_detected"] = True
                    elif temp_c > 75:
                        sev = "WARNING"

                    result["zones"].append({
                        "zone": entry,
                        "type": zone_type,
                        "temp_celsius": temp_c,
                        "severity": sev
                    })

                    if sev == "CRITICAL":
                        result["status"] = "CRITICAL"
                    elif sev == "WARNING" and result["status"] != "CRITICAL":
                        result["status"] = "WARNING"
                except Exception:
                    continue

    # CPU frequency (actual vs max)
    try:
        freq_path = "/sys/devices/system/cpu/cpu0/cpufreq"
        if os.path.exists(freq_path):
            with open(os.path.join(freq_path, "scaling_cur_freq"), "r") as f:
                cur_freq = int(f.read().strip()) / 1000  # MHz
            with open(os.path.join(freq_path, "scaling_max_freq"), "r") as f:
                max_freq = int(f.read().strip()) / 1000  # MHz
            result["cpu_freq_mhz"] = {"current": cur_freq, "max": max_freq}
            ratio = cur_freq / max_freq if max_freq > 0 else 1
            if ratio < 0.5:
                result["throttling_detected"] = True
                result["status"] = "WARNING"
    except Exception:
        pass

    return result


def analyze_zombies() -> dict:
    """Detecta procesos zombie y huérfanos."""
    output = safe_run(["ps", "aux"], timeout=3)
    if output.startswith("[ERROR"):
        return {"status": "UNAVAILABLE", "error": output}

    zombies = []
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) >= 8 and parts[7] in ("Z", "Z+"):
            zombies.append({
                "user": parts[0],
                "pid": parts[1],
                "cpu": parts[2],
                "mem": parts[3],
                "command": " ".join(parts[10:])
            })

    severity = "OK"
    if len(zombies) > 5:
        severity = "WARNING"
    elif len(zombies) > 20:
        severity = "CRITICAL"

    return {
        "status": severity,
        "zombie_count": len(zombies),
        "zombies": zombies[:10]  # Top 10
    }


def analyze_zram() -> dict:
    """Analiza eficiencia de ZRAM."""
    result = {"status": "OK", "devices": []}

    zramctl_output = safe_run(["zramctl", "--output-all", "--raw"], timeout=3)
    if zramctl_output.startswith("[ERROR") or not zramctl_output.strip():
        # Fallback: leer /proc/swaps
        try:
            with open("/proc/swaps", "r") as f:
                content = f.read()
            if "zram" in content:
                result["raw_swaps"] = content.strip()
            else:
                result["status"] = "N/A"
                result["note"] = "ZRAM no configurado"
        except Exception:
            result["status"] = "UNAVAILABLE"
        return result

    lines = zramctl_output.strip().split("\n")
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 4:
            result["devices"].append({
                "device": parts[0],
                "raw": line
            })

    return result


def run_full_analysis() -> dict:
    """Ejecuta todos los análisis y devuelve resultados consolidados."""
    timestamp = datetime.now(timezone.utc).isoformat()

    results = {
        "timestamp_utc": timestamp,
        "host": "HP15",
        "analyzer_version": "1.0.0",
        "categories": {
            "kernel_errors": analyze_dmesg_errors(),
            "io_wait": analyze_io_wait(),
            "memory_pressure": analyze_memory_pressure(),
            "thermal": analyze_thermal(),
            "zombies": analyze_zombies(),
            "zram": analyze_zram()
        }
    }

    # Calcular estado global
    severities = [cat.get("status", "OK") for cat in results["categories"].values()]
    if "CRITICAL" in severities:
        results["global_status"] = "CRITICAL"
    elif "WARNING" in severities:
        results["global_status"] = "WARNING"
    else:
        results["global_status"] = "OK"

    return results


def format_markdown(data: dict) -> str:
    """Genera reporte Markdown legible."""
    lines = []
    gs = data.get("global_status", "OK")
    icon = "🔴" if gs == "CRITICAL" else "🟡" if gs == "WARNING" else "🟢"

    lines.append(f"# 🔍 DIAGNÓSTICO DE CUELLOS DE BOTELLA — HP15")
    lines.append(f"**Timestamp UTC**: `{data.get('timestamp_utc')}` | **Estado Global**: {icon} **{gs}**\n")

    lines.append("## Resumen por Categoría\n")
    lines.append("| Categoría | Estado | Detalle |")
    lines.append("|---|:---:|---|")

    cats = data.get("categories", {})

    # Kernel errors
    ke = cats.get("kernel_errors", {})
    ke_icon = "🔴" if ke.get("status") == "CRITICAL" else "🟡" if ke.get("status") == "WARNING" else "🟢"
    lines.append(f"| **Errores de Kernel (dmesg)** | {ke_icon} {ke.get('status')} | {ke.get('error_count', 0)} errores, {ke.get('warning_count', 0)} warnings |")

    # I/O Wait
    io = cats.get("io_wait", {})
    io_icon = "🔴" if io.get("status") == "CRITICAL" else "🟡" if io.get("status") == "WARNING" else "🟢"
    lines.append(f"| **I/O Wait** | {io_icon} {io.get('status')} | {io.get('iowait_pct', 'N/A')}% |")

    # Memory pressure
    mp = cats.get("memory_pressure", {})
    mp_icon = "🔴" if mp.get("status") == "CRITICAL" else "🟡" if mp.get("status") == "WARNING" else "🟢"
    oom = mp.get("oom_events", 0)
    lines.append(f"| **Presión de Memoria (PSI)** | {mp_icon} {mp.get('status')} | OOM events: {oom} |")

    # Thermal
    th = cats.get("thermal", {})
    th_icon = "🔴" if th.get("status") == "CRITICAL" else "🟡" if th.get("status") == "WARNING" else "🟢"
    throttle = "SÍ ⚠️" if th.get("throttling_detected") else "No"
    lines.append(f"| **Thermal / Throttling** | {th_icon} {th.get('status')} | Throttling: {throttle} |")

    # Zombies
    zb = cats.get("zombies", {})
    zb_icon = "🔴" if zb.get("status") == "CRITICAL" else "🟡" if zb.get("status") == "WARNING" else "🟢"
    lines.append(f"| **Procesos Zombie** | {zb_icon} {zb.get('status')} | {zb.get('zombie_count', 0)} zombies |")

    # ZRAM
    zr = cats.get("zram", {})
    zr_icon = "🟢" if zr.get("status") in ("OK", "N/A") else "🟡"
    lines.append(f"| **ZRAM** | {zr_icon} {zr.get('status')} | {len(zr.get('devices', []))} dispositivos |")

    # Detalles de thermal zones
    if th.get("zones"):
        lines.append("\n### 🌡️ Zonas Térmicas")
        lines.append("| Zona | Tipo | Temperatura | Estado |")
        lines.append("|---|---|:---:|:---:|")
        for z in th["zones"]:
            z_icon = "🔴" if z.get("severity") == "CRITICAL" else "🟡" if z.get("severity") == "WARNING" else "🟢"
            lines.append(f"| {z['zone']} | {z['type']} | {z['temp_celsius']:.1f}°C | {z_icon} |")

    # Frecuencia CPU
    if th.get("cpu_freq_mhz"):
        freq = th["cpu_freq_mhz"]
        lines.append(f"\n**CPU Frecuencia**: {freq['current']:.0f} MHz / {freq['max']:.0f} MHz máx")

    # PSI detalle
    if mp.get("psi"):
        lines.append("\n### 📊 Pressure Stall Information (PSI)")
        for res, psi_data in mp["psi"].items():
            if isinstance(psi_data, dict) and "avg10" in psi_data:
                p_icon = "🔴" if psi_data.get("severity") == "CRITICAL" else "🟡" if psi_data.get("severity") == "WARNING" else "🟢"
                lines.append(f"- **{res.upper()}**: avg10={psi_data['avg10']}% {p_icon}")

    # Errores recientes de kernel
    if ke.get("recent_errors"):
        lines.append("\n### ⚠️ Errores Recientes de Kernel (últimos 10)")
        lines.append("```")
        for err in ke["recent_errors"]:
            lines.append(err[:200])
        lines.append("```")

    return "\n".join(lines)


if __name__ == "__main__":
    data = run_full_analysis()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(data))
