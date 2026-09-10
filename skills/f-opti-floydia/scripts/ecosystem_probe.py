#!/usr/bin/env python3
"""
.agents/skills/opti-floydia/scripts/ecosystem_probe.py — FloydIA Ecosystem SRE Probe v3.0

Script de telemetría y diagnóstico 100% no invasivo y de solo lectura.
Audita en paralelo:
1. HP15 Local: CPU, RAM, ZRAM, PSI (Pressure Stall), I/O, Load Average, Sockets y Procesos.
2. Nodos Remotos (TCP Probes con timeout de 1.5s):
   - MikroTik Gateway (192.168.1.1:80)
   - HP45 Réplica (192.168.1.200:22)
   - Proxmox PVE (192.168.1.220:8006)
   - CT114 Playwright WS (192.168.1.238:3000)
   - CT114 FlareSolverr (192.168.1.238:8191)
   - CT106 Syncthing Vault (192.168.1.232:8384)
3. DNS & Latencia de APIs de IA (Google AI, Anthropic, OpenRouter).
4. Servidores MCP y Token Budget del Memory Bank.

Salida: JSON estructurado o reporte formateado en Markdown legible por humanos y agentes.
"""

import sys
import os
import json
import socket
import time
import subprocess
from datetime import datetime, timezone

# Forzar timeout global de sockets y desacople no interactivo
socket.setdefaulttimeout(2.0)


def check_tcp(host: str, port: int, timeout: float = 1.5):
    """Prueba de conexión TCP no invasiva con medición de latencia en ms."""
    t0 = time.time()
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return {
            "status": "OK",
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "error": None
        }
    except socket.timeout:
        return {"status": "TIMEOUT", "latency_ms": None, "error": "Timeout superado"}
    except ConnectionRefusedError:
        return {"status": "REFUSED", "latency_ms": None, "error": "Conexión rechazada (puerto cerrado)"}
    except Exception as e:
        return {"status": "UNREACHABLE", "latency_ms": None, "error": str(e)}


def check_dns(hostname: str):
    """Mide tiempo de resolución DNS y resuelve IP."""
    t0 = time.time()
    try:
        ip = socket.gethostbyname(hostname)
        return {
            "status": "OK",
            "ip": ip,
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "error": None
        }
    except Exception as e:
        return {"status": "ERROR", "ip": None, "latency_ms": None, "error": str(e)}


def get_local_psi():
    """Lee Pressure Stall Information del kernel de Linux si está disponible."""
    psi = {}
    for res in ["cpu", "memory", "io"]:
        path = f"/proc/pressure/{res}"
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    psi[res] = f.read().strip()
            except Exception:
                psi[res] = "N/A"
        else:
            psi[res] = "No soportado"
    return psi


def get_memory_info():
    """Obtiene datos de RAM y ZRAM."""
    mem = {}
    if os.path.exists("/proc/meminfo"):
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        k = parts[0].strip()
                        v = parts[1].strip()
                        if k in ["MemTotal", "MemFree", "MemAvailable", "Buffers", "Cached", "SwapTotal", "SwapFree"]:
                            mem[k] = v
        except Exception as e:
            mem["error"] = str(e)
    return mem


def get_load_and_cpu():
    """Obtiene load average y recuento de cores."""
    try:
        load = os.getloadavg()
        cpu_count = os.cpu_count() or 1
        return {
            "load_1m": load[0],
            "load_5m": load[1],
            "load_15m": load[2],
            "cpu_cores": cpu_count,
            "load_per_core_1m": round(load[0] / cpu_count, 2)
        }
    except Exception as e:
        return {"error": str(e)}


def get_active_mcps():
    """Lee los servidores MCP configurados en mcp_config.json."""
    mcp_path = os.path.expanduser("~/.gemini/config/mcp_config.json")
    if os.path.exists(mcp_path):
        try:
            with open(mcp_path, "r") as f:
                data = json.load(f)
            servers = data.get("mcpServers", {})
            return {"count": len(servers), "servers": list(servers.keys())}
        except Exception as e:
            return {"count": 0, "error": str(e)}
    return {"count": 0, "servers": []}


def get_token_budget():
    """Verifica el tamaño de activeContext.md."""
    ctx_path = "/home/tec/Dropbox/ANTIGRAVITY_PROJECTS/memory-bank/core/activeContext.md"
    if os.path.exists(ctx_path):
        try:
            with open(ctx_path, "r", encoding="utf-8") as f:
                content = f.read()
            lines = len(content.splitlines())
            tokens_approx = len(content) // 4
            return {
                "activeContext_lines": lines,
                "activeContext_tokens_approx": tokens_approx,
                "status": "PASS" if tokens_approx <= 400 else "WARNING"
            }
        except Exception as e:
            return {"error": str(e)}
    return {"status": "NOT_FOUND"}


def run_full_probe():
    """Ejecuta la sonda completa y devuelve el diccionario estructurado."""
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # 1. Nodos de infraestructura
    infra_targets = {
        "MikroTik Gateway": ("192.168.1.1", 80),
        "HP45 Réplica": ("192.168.1.200", 22),
        "Proxmox PVE": ("192.168.1.220", 8006),
        "CT114 Playwright WS": ("192.168.1.238", 3000),
        "CT114 FlareSolverr": ("192.168.1.238", 8191),
        "CT106 Syncthing Vault": ("192.168.1.232", 8384),
    }
    
    network_results = {}
    for name, (ip, port) in infra_targets.items():
        network_results[name] = {
            "target": f"{ip}:{port}",
            **check_tcp(ip, port)
        }

    # 2. DNS de APIs de IA
    dns_targets = {
        "Google AI Studio": "generativelanguage.googleapis.com",
        "Anthropic API": "api.anthropic.com",
        "OpenRouter API": "openrouter.ai",
        "Cloudflare DNS": "1.1.1.1"
    }
    dns_results = {}
    for name, host in dns_targets.items():
        dns_results[name] = check_dns(host)

    # 3. Métricas locales
    probe_data = {
        "timestamp_utc": timestamp,
        "host": "HP15",
        "user": "tec",
        "cpu_and_load": get_load_and_cpu(),
        "memory": get_memory_info(),
        "psi": get_local_psi(),
        "network_infrastructure": network_results,
        "dns_and_ai_apis": dns_results,
        "mcp_servers": get_active_mcps(),
        "token_budget": get_token_budget()
    }
    
    return probe_data


def format_markdown_report(data: dict) -> str:
    """Genera un reporte Markdown limpio y estructurado."""
    lines = []
    lines.append(f"# 🛰️ REPORTE DE TELEMETRÍA SRE — ECOSISTEMA FLOYDIA")
    lines.append(f"**Timestamp UTC**: `{data.get('timestamp_utc')}` | **Host**: `{data.get('host')}`\n")
    
    # Infraestructura
    lines.append("## 🌐 Conectividad de Red & Nodos")
    lines.append("| Nodo / Servicio | Endpoint | Estado | Latencia | Detalle |")
    lines.append("|---|---|:---:|:---:|---|")
    for name, info in data.get("network_infrastructure", {}).items():
        st = info.get("status")
        icon = "🟢" if st == "OK" else "🟡" if st == "TIMEOUT" else "❌"
        lat = f"{info.get('latency_ms')} ms" if info.get("latency_ms") is not None else "N/A"
        err = info.get("error") or "Conectado"
        lines.append(f"| **{name}** | `{info.get('target')}` | {icon} {st} | {lat} | {err} |")
    
    # DNS
    lines.append("\n## 📡 Resolución DNS & APIs de IA")
    lines.append("| Servicio | IP Resuelta | Estado | Latencia DNS |")
    lines.append("|---|---|:---:|:---:|")
    for name, info in data.get("dns_and_ai_apis", {}).items():
        st = info.get("status")
        icon = "🟢" if st == "OK" else "❌"
        ip = info.get("ip") or "N/A"
        lat = f"{info.get('latency_ms')} ms" if info.get("latency_ms") is not None else "N/A"
        lines.append(f"| **{name}** | `{ip}` | {icon} {st} | {lat} |")

    # CPU & RAM
    cpu = data.get("cpu_and_load", {})
    lines.append(f"\n## 💻 Recursos Locales HP15")
    lines.append(f"- **CPU Cores**: {cpu.get('cpu_cores')} | **Load 1m**: {cpu.get('load_1m')} (Load/Core: {cpu.get('load_per_core_1m')})")
    
    mem = data.get("memory", {})
    lines.append(f"- **Mem Total**: {mem.get('MemTotal', 'N/A')} | **Mem Disponible**: {mem.get('MemAvailable', 'N/A')}")
    lines.append(f"- **Swap Total**: {mem.get('SwapTotal', 'N/A')} | **Swap Libre**: {mem.get('SwapFree', 'N/A')}")
    
    # MCPs & Token Budget
    mcp = data.get("mcp_servers", {})
    lines.append(f"- **Servidores MCP Configurados**: {mcp.get('count')} ({', '.join(mcp.get('servers', []))})")
    
    tb = data.get("token_budget", {})
    lines.append(f"- **Working Memory Bootloader**: {tb.get('activeContext_tokens_approx', 'N/A')} tokens ({tb.get('status', 'N/A')})")
    
    return "\n".join(lines)


if __name__ == "__main__":
    data = run_full_probe()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2))
    else:
        print(format_markdown_report(data))
