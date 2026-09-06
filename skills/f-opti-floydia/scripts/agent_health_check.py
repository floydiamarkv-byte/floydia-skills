#!/usr/bin/env python3
"""
agent_health_check.py — Auditoría de Agentes & Harness Engineering v1.0
f-opti-floydia / Opción 8

Análisis 100% read-only y no invasivo de:
1. Procesos de agentes activos (Antigravity, OpenCode, Hermes, DeepSeek)
2. Integridad de symlinks de skills entre agentes
3. MCPs configurados y su estado
4. Logs de errores recientes de agentes
5. Estado del Harness Workflow
6. Paridad multi-agente

Salida: JSON o Markdown estructurado.
"""

import sys
import os
import json
import subprocess
import glob
from datetime import datetime, timezone
from pathlib import Path


WORKSPACE = ""
SKILLS_SOURCE = os.path.join(WORKSPACE, ".agents/skills")
OPENCODE_SKILLS = os.path.expanduser("~/.opencode/skills")
HERMES_SKILLS = os.path.expanduser("~/.hermes/skills")
MCP_CONFIG = os.path.expanduser("~/.gemini/config/mcp_config.json")
BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-ide/brain")

AGENT_PATTERNS = {
    "Antigravity IDE": ["antigravity", "gemini"],
    "OpenCode CLI": ["opencode"],
    "Hermes CLI": ["hermes"],
    "DeepSeek": ["deepseek"],
    "Claude Code": ["claude"],
}


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


def check_agent_processes() -> dict:
    """Detecta procesos de agentes activos y sus consumos."""
    ps_output = safe_run(["ps", "aux"], timeout=3)
    if ps_output.startswith("[ERROR"):
        return {"status": "UNAVAILABLE", "error": ps_output}

    agents = {}
    for agent_name, patterns in AGENT_PATTERNS.items():
        agent_procs = []
        for line in ps_output.split("\n"):
            line_lower = line.lower()
            if any(p in line_lower for p in patterns) and "grep" not in line_lower:
                parts = line.split()
                if len(parts) >= 11:
                    agent_procs.append({
                        "user": parts[0],
                        "pid": parts[1],
                        "cpu_pct": parts[2],
                        "mem_pct": parts[3],
                        "vsz_kb": parts[4],
                        "rss_kb": parts[5],
                        "command": " ".join(parts[10:])[:120]
                    })

        agents[agent_name] = {
            "active": len(agent_procs) > 0,
            "process_count": len(agent_procs),
            "processes": agent_procs[:5],  # Top 5 por agente
            "total_cpu": sum(float(p.get("cpu_pct", 0)) for p in agent_procs),
            "total_mem": sum(float(p.get("mem_pct", 0)) for p in agent_procs),
        }

    return {"status": "OK", "agents": agents}


def check_skills_symlinks() -> dict:
    """Verifica integridad de symlinks de skills entre agentes."""
    result = {
        "source_skills": [],
        "opencode": {"total": 0, "valid": 0, "broken": [], "missing": []},
        "hermes": {"total": 0, "valid": 0, "broken": [], "missing": []},
        "status": "OK"
    }

    # Listar skills fuente
    if os.path.exists(SKILLS_SOURCE):
        for entry in sorted(os.listdir(SKILLS_SOURCE)):
            skill_path = os.path.join(SKILLS_SOURCE, entry)
            if os.path.isdir(skill_path) and entry.startswith("f-"):
                result["source_skills"].append(entry)

    # Verificar cada destino
    for dest_name, dest_path in [("opencode", OPENCODE_SKILLS), ("hermes", HERMES_SKILLS)]:
        if not os.path.exists(dest_path):
            result[dest_name]["note"] = f"Directorio {dest_path} no existe"
            result["status"] = "WARNING"
            continue

        # Listar symlinks existentes
        for entry in os.listdir(dest_path):
            full_path = os.path.join(dest_path, entry)
            if os.path.islink(full_path):
                result[dest_name]["total"] += 1
                if os.path.exists(full_path):
                    result[dest_name]["valid"] += 1
                else:
                    result[dest_name]["broken"].append(entry)
                    result["status"] = "WARNING"

        # Verificar skills faltantes
        for skill in result["source_skills"]:
            skill_link = os.path.join(dest_path, skill)
            if not os.path.exists(skill_link):
                result[dest_name]["missing"].append(skill)

        if result[dest_name]["missing"]:
            result["status"] = "WARNING"

    return result


def check_mcps() -> dict:
    """Verifica MCPs configurados y su disponibilidad."""
    result = {"status": "OK", "total": 0, "servers": []}

    if not os.path.exists(MCP_CONFIG):
        return {"status": "WARNING", "total": 0, "error": f"{MCP_CONFIG} no encontrado"}

    try:
        with open(MCP_CONFIG, "r") as f:
            config = json.load(f)

        servers = config.get("mcpServers", {})
        result["total"] = len(servers)

        for name, server_config in servers.items():
            server_info = {
                "name": name,
                "type": "stdio" if "command" in server_config else "sse" if "url" in server_config else "unknown",
            }

            # Verificar si el comando existe
            if "command" in server_config:
                cmd = server_config["command"]
                cmd_exists = os.path.exists(cmd) if os.path.isabs(cmd) else bool(safe_run(["which", cmd], timeout=2))
                server_info["command"] = cmd
                server_info["command_exists"] = not cmd_exists.startswith("[ERROR") if isinstance(cmd_exists, str) else cmd_exists

            result["servers"].append(server_info)

    except (json.JSONDecodeError, IOError) as e:
        result["status"] = "ERROR"
        result["error"] = str(e)

    return result


def check_harness_state() -> dict:
    """Verifica estado del Harness Workflow."""
    result = {
        "status": "OK",
        "init_script_exists": False,
        "active_harnesses": 0,
        "recent_conversations": 0
    }

    # Verificar init_harness.sh
    init_script = os.path.join(WORKSPACE, "SCRIPTS/init_harness.sh")
    result["init_script_exists"] = os.path.exists(init_script)
    if result["init_script_exists"]:
        result["init_script_executable"] = os.access(init_script, os.X_OK)

    # Contar conversaciones recientes en brain/
    if os.path.exists(BRAIN_DIR):
        conversations = [d for d in os.listdir(BRAIN_DIR) if os.path.isdir(os.path.join(BRAIN_DIR, d))]
        result["recent_conversations"] = len(conversations)

    # Verificar archivos de harness workflow
    harness_skill = os.path.join(WORKSPACE, ".agents/skills/f-harness-workflow/SKILL.md")
    result["harness_skill_exists"] = os.path.exists(harness_skill)

    return result


def check_recent_errors() -> dict:
    """Busca errores recientes en logs de agentes."""
    result = {"status": "OK", "errors": []}

    # journalctl de usuario (últimas 2 horas)
    journal_output = safe_run(
        ["journalctl", "--user", "-p", "err", "--since", "2 hours ago", "--no-pager", "-n", "20"],
        timeout=5
    )
    if not journal_output.startswith("[ERROR") and journal_output.strip():
        lines = journal_output.strip().split("\n")
        agent_errors = [l for l in lines if any(
            p in l.lower() for patterns in AGENT_PATTERNS.values() for p in patterns
        )]
        if agent_errors:
            result["errors"].extend(agent_errors[-10:])
            result["status"] = "WARNING"

    return result


def run_full_audit() -> dict:
    """Ejecuta auditoría completa de agentes."""
    timestamp = datetime.now(timezone.utc).isoformat()

    audit = {
        "timestamp_utc": timestamp,
        "host": "HP15",
        "analyzer_version": "1.0.0",
        "sections": {
            "agent_processes": check_agent_processes(),
            "skills_symlinks": check_skills_symlinks(),
            "mcp_servers": check_mcps(),
            "harness_state": check_harness_state(),
            "recent_errors": check_recent_errors()
        }
    }

    # Estado global
    statuses = [s.get("status", "OK") for s in audit["sections"].values()]
    if "ERROR" in statuses or "CRITICAL" in statuses:
        audit["global_status"] = "CRITICAL"
    elif "WARNING" in statuses:
        audit["global_status"] = "WARNING"
    else:
        audit["global_status"] = "OK"

    return audit


def format_markdown(data: dict) -> str:
    """Genera reporte Markdown legible."""
    lines = []
    gs = data.get("global_status", "OK")
    icon = "🔴" if gs in ("CRITICAL", "ERROR") else "🟡" if gs == "WARNING" else "🟢"

    lines.append(f"# 🛸 AUDITORÍA DE AGENTES & HARNESS ENGINEERING")
    lines.append(f"**Timestamp UTC**: `{data.get('timestamp_utc')}` | **Estado Global**: {icon} **{gs}**\n")

    sections = data.get("sections", {})

    # === Agentes ===
    ap = sections.get("agent_processes", {})
    lines.append("## 🤖 Procesos de Agentes Activos\n")
    lines.append("| Agente | Estado | Procesos | CPU% Total | MEM% Total |")
    lines.append("|---|:---:|:---:|:---:|:---:|")

    if "agents" in ap:
        for name, info in ap["agents"].items():
            active_icon = "🟢 Activo" if info["active"] else "⚫ Inactivo"
            lines.append(
                f"| **{name}** | {active_icon} | {info['process_count']} | "
                f"{info['total_cpu']:.1f}% | {info['total_mem']:.1f}% |"
            )

    # === Symlinks ===
    sl = sections.get("skills_symlinks", {})
    lines.append(f"\n## 🔗 Integridad de Symlinks de Skills")
    lines.append(f"**Skills fuente**: {len(sl.get('source_skills', []))} en `.agents/skills/`\n")

    for dest in ["opencode", "hermes"]:
        dest_info = sl.get(dest, {})
        total = dest_info.get("total", 0)
        valid = dest_info.get("valid", 0)
        broken = dest_info.get("broken", [])
        missing = dest_info.get("missing", [])
        d_icon = "🟢" if not broken and not missing else "🟡"

        lines.append(f"### {dest.capitalize()}")
        lines.append(f"- Symlinks: {valid}/{total} válidos {d_icon}")
        if broken:
            lines.append(f"- ❌ **Rotos**: {', '.join(broken)}")
        if missing:
            lines.append(f"- ⚠️ **Faltantes**: {', '.join(missing)}")
        if dest_info.get("note"):
            lines.append(f"- ℹ️ {dest_info['note']}")

    # === MCPs ===
    mcp = sections.get("mcp_servers", {})
    lines.append(f"\n## 🔌 Servidores MCP Configurados")
    lines.append(f"**Total**: {mcp.get('total', 0)} servidores\n")

    if mcp.get("servers"):
        lines.append("| Servidor | Tipo | Comando Existe |")
        lines.append("|---|:---:|:---:|")
        for s in mcp["servers"]:
            cmd_ok = "✅" if s.get("command_exists") else "❌" if "command_exists" in s else "—"
            lines.append(f"| {s['name']} | {s.get('type', '?')} | {cmd_ok} |")

    # === Harness ===
    hs = sections.get("harness_state", {})
    lines.append(f"\n## 🏗️ Estado del Harness Workflow")
    lines.append(f"- `init_harness.sh` existe: {'✅' if hs.get('init_script_exists') else '❌'}")
    if hs.get("init_script_exists"):
        lines.append(f"- Ejecutable: {'✅' if hs.get('init_script_executable') else '❌'}")
    lines.append(f"- Skill `f-harness-workflow` existe: {'✅' if hs.get('harness_skill_exists') else '❌'}")
    lines.append(f"- Conversaciones recientes en `brain/`: {hs.get('recent_conversations', 0)}")

    # === Errores recientes ===
    re_section = sections.get("recent_errors", {})
    if re_section.get("errors"):
        lines.append(f"\n## ⚠️ Errores Recientes de Agentes (últimas 2h)")
        lines.append("```")
        for err in re_section["errors"]:
            lines.append(err[:200])
        lines.append("```")
    else:
        lines.append(f"\n## ✅ Sin Errores Recientes de Agentes (últimas 2h)")

    return "\n".join(lines)


if __name__ == "__main__":
    data = run_full_audit()
    if "--json" in sys.argv:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(format_markdown(data))
