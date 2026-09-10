#!/usr/bin/env python3
"""
.agents/skills/opti-floydia/scripts/dual_prompt_generator.py — Dual Prompt Generator v3.0

Genera dos prompts calibrados para análisis en IAs Web externas (Claude Web / ChatGPT):
- PROMPT A: Telemetría & Diagnóstico Profundo (Evidencia observable sin alucinaciones).
- PROMPT B: Plan de Acción SRE & Decisiones (Matriz de Impacto vs Riesgo y Rollback).

Aplica sanitización estricta de secretos (cero passwords, tokens o variables .env expuestas).
"""

import sys
import os
import json
import re

# Importar sonda local
sys.path.insert(0, os.path.dirname(__file__))
from ecosystem_probe import run_full_probe, format_markdown_report


def sanitize_secrets(text: str) -> str:
    """Elimina tokens, claves y secretos potenciales reemplazándolos por placeholders."""
    # Reemplazar patrones de tokens comunes
    text = re.sub(r'(sk-[a-zA-Z0-9_\-]{20,})', r'${OPENAI_API_KEY}', text)
    text = re.sub(r'(AIzaSy[a-zA-Z0-9_\-]{30,})', r'${GOOGLE_API_KEY}', text)
    text = re.sub(r'(ghp_[a-zA-Z0-9]{30,})', r'${GITHUB_TOKEN}', text)
    text = re.sub(r'(bearer\s+[a-zA-Z0-9_\-\.]{20,})', r'Bearer ${TOKEN}', text, flags=re.IGNORECASE)
    text = re.sub(r'(password|passwd|secret)\s*[:=]\s*["\']?[^"\'\s]+["\']?', r'\1: [REDACTED]', text, flags=re.IGNORECASE)
    return text


def generate_prompt_a(probe_data: dict) -> str:
    """Genera el Prompt A: Diagnóstico y Telemetría."""
    telemetry_md = format_markdown_report(probe_data)
    
    prompt = f"""# DIRECTIVA DE DIAGNÓSTICO SRE — ANÁLISIS DE TELEMETRÍA EN VIVO (ECOSISTEMA FLOYDIA)

<system_role>
Actúa como un **Principal Site Reliability Engineer (SRE), Linux Kernel Architect y Network Specialist**.
Tu objetivo exclusivo es **analizar la telemetría en vivo del ecosistema FloydIA, identificar cuellos de botella, anomalías, riesgos de latencia o recursos degradados, y formular un diagnóstico técnico basado estrictamente en la evidencia observable**.
</system_role>

<operational_rules>
1. **EVIDENCIA REAL**: No asumas configuraciones que no aparezcan en la telemetría. Diferencia hechos de hipótesis.
2. **DATOS INCOMPLETOS**: Si un dato no está en el reporte, márcalo como `UNKNOWN` o `NO MEDIDO`.
3. **CERO SECRETOS**: Todo el entorno opera bajo SSOT con permisos restringidos.
</operational_rules>

<ecosystem_telemetry>
{telemetry_md}
</ecosystem_telemetry>

<diagnostic_contract>
Genera tu informe de diagnóstico respondiendo con la siguiente estructura:

1. **Estado General del Ecosistema**: Veredicto de salud (🟢 Sano | 🟡 Degradado | 🔴 Crítico).
2. **Análisis de Nodos de Red & Proxmox**: Evaluación de latencias TCP (CT114 Playwright, CT106 Vault, MikroTik).
3. **Análisis de Recursos Locales**: Evaluación de CPU load, RAM disponible, ZRAM y métricas PSI.
4. **Top 3 Riesgos o Cuellos de Botella Detectados**: Detallando síntoma, causa raíz probable e impacto.
5. **Hipótesis Técnicas**: Aspectos que requieren verificación adicional.
</diagnostic_contract>
"""
    return sanitize_secrets(prompt)


def generate_prompt_b(probe_data: dict) -> str:
    """Genera el Prompt B: Plan de Acción y Decisiones SRE."""
    telemetry_md = format_markdown_report(probe_data)
    
    prompt = f"""# DIRECTIVA DE PLAN DE ACCIÓN SRE — OPTIMIZACIÓN & HARDENING (ECOSISTEMA FLOYDIA)

<system_role>
Actúa como un **Principal SRE Lead y Systems Decision Architect**.
A partir de la telemetría del ecosistema FloydIA y los principios de **Zero-Downtime, Least Privilege y Fail-Closed**, formula un **Plan de Acción Priorizado, Seguro y Reversible** para optimizar el rendimiento y prevenir bloqueos.
</system_role>

<ecosystem_context>
{telemetry_md}
</ecosystem_context>

<guardrails>
- **PROHIBIDO**: Ejecutar `sync` global en carpetas con sincronización (Dropbox/Syncthing) para evitar I/O stalls.
- **PROTEGIDO**: No tocar procesos de Antigravity IDE, LSPs (`jedi`, `tsserver`), Syncthing ni demonios de sistema.
- **TIMEOUTS**: Todo script debe ejecutarse a través de `safe_run_python.sh` con timeout duro y `stdin` desacoplado a `/dev/null`.
</guardrails>

<action_plan_contract>
Estructura tu plan de acción en 4 categorías:

### 1. QUICK WINS (Impacto Inmediato / Riesgo Cero)
- Acciones seguras, reversibles y verificables en < 1 minuto.

### 2. OPTIMIZACIONES MEDIAS (Configuración de Red & Timeouts)
- Ajustes de buffers, DNS caching, parámetros de sockets y prioridades de procesos.

### 3. ACCIONES NO RECOMENDADAS (Anti-Patrones Descartados)
- Acciones invasivas que NO deben ejecutarse (y por qué violarían la estabilidad).

### 4. MATRIZ DE DECISIÓN Y ROLLBACK
Para cada acción propuesta, completa la tabla:
| Acción | Impacto (1-5) | Riesgo (1-5) | Reversibilidad (1-5) | Comando Propuesto | Verificación | Plan de Rollback |
|---|:---:|:---:|:---:|---|---|---|

### 5. ORDEN EXACTO DE EJECUCIÓN PASO A PASO
- Secuencia numerada de comandos y validaciones.
</action_plan_contract>
"""
    return sanitize_secrets(prompt)


if __name__ == "__main__":
    probe = run_full_probe()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--prompt-a":
        print(generate_prompt_a(probe))
    elif len(sys.argv) > 1 and sys.argv[1] == "--prompt-b":
        print(generate_prompt_b(probe))
    else:
        print("=" * 70)
        print("📌 PROMPT A: TELEMETRÍA & DIAGNÓSTICO PROFUNDO (Para Claude/ChatGPT Web)")
        print("=" * 70)
        print(generate_prompt_a(probe))
        print("\n" + "=" * 70)
        print("📌 PROMPT B: PLAN DE ACCIÓN & DECISIONES SRE (Para Claude/ChatGPT Web)")
        print("=" * 70)
        print(generate_prompt_b(probe))
