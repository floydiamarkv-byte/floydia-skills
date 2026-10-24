---
name: f-harness
description: "Centro de control unificado del Harness FloydIA (antes f-harness + f-harness-select + f-harness-workflow, fusionados 2026-10-13). Cuatro modos: (1) Operativa/SRE — routing de 11 motores $0.00, doctor de DSH, telemetría; (2) Selector de MODO — conmutar las 6 cadenas de prioridades (AGY, Nemotron, Kilo, Cloudflare, Pool Free); (3) Metodología WORKFLOW — roles Líder/Explorador/Implementador/Revisor para tareas complejas; (4) ESCANEO DE APIs + RANKING — auditoría empírica del .env, ranking de inteligencia y propuesta de redefinición de la cadena. USAR con /f-harness, /harness, /modo, /harness-mode, /harness-select, /harness-workflow, /elegir-modelo, /prioridades, /model-router, /api-scan, /escanear-apis, /ranking-modelos, /redefinir-harness o ante caídas de motores/DSH. NO USAR para descomponer proyectos (eso es f-orquestador-floydia) ni para consultas triviales."
version: 4.1.0
triggers:
  - /f-harness
  - /harness
  - /f-harness-select
  - /harness-select
  - /f-harness-workflow
  - /harness-workflow
  - /modo
  - /harness-mode
  - /elegir-modelo
  - /prioridades
  - /model-router
  - /routing
  - /api-scan
  - /escanear-apis
  - /ranking-modelos
  - /auditar-apis
  - /redefinir-harness
  - /harness-api-scan
  - harness floydia
  - cadena de motores
  - cambiar modo del harness
  - cambiar orden de motores
  - deepseek no arranca
  - dsh no arranca
  - dsh se cae
  - harness doctor
  - reparar dsh
  - arnes agéntico
  - harness-workflow
---

# Skill: f-harness v4.0 — Centro Unificado del Harness FloydIA

> **Fusión 2026-10-13**: unifica `f-harness` (operativa SRE), `f-harness-select` (selector de modo) y `f-harness-workflow` (metodología de roles). Cuerpos íntegros preservados en `references/` (carga bajo demanda).
>
> **Frontera con f-orquestador-floydia (INMUTABLE)**: este skill NO descompone proyectos ni define arquitectura. `f-orquestador-floydia` es el Arquitecto Director (diseña y delega); `f-harness` modo WORKFLOW gobierna la **ejecución** multi-agente de una tarea compleja ya definida (roles, evidencia, tests). Si la petición es "orquesta este proyecto", derivar a `f-orquestador-floydia`.

## 🎯 Enrutamiento interno (leer SOLO el modo correspondiente)

| Modo | Triggers dominantes | Referencia a leer |
|---|---|---|
| **1. OPERATIVA/SRE** | `/f-harness`, `/harness`, `/model-router`, caídas DSH, doctor, telemetría | `references/operativa.md` |
| **2. SELECTOR DE MODO** | `/modo`, `/harness-mode`, `/f-harness-select`, `/elegir-modelo`, `/prioridades` | `references/select.md` |
| **3. WORKFLOW (metodología)** | `/f-harness-workflow`, tarea compleja multi-agente, ingeniería de arneses | `references/workflow.md` |
| **4. ESCANEO DE APIs + RANKING** | `/api-scan`, `/escanear-apis`, `/ranking-modelos`, `/auditar-apis`, `/redefinir-harness` | `references/api-scan.md` |

Regla: carga **una** referencia según el trigger, nunca las tres. Si la petición es ambigua entre modos, presenta este mini-menú:

```markdown
🛸 F-HARNESS v4 — ¿Qué necesitas?
1️⃣ Operativa/SRE (motores, doctor DSH, telemetría, escaneo de APIs + ranking)
2️⃣ Cambiar el MODO del harness (cadenas 1-6)
3️⃣ Metodología WORKFLOW (roles para tarea compleja)
```

## Aliases preservados (transición)

Los antiguos comandos `/f-harness-select` y `/f-harness-workflow` siguen vivos como triggers de este skill y rutean a los modos 2 y 3 directamente. Las carpetas `f-harness-select/` y `f-harness-workflow/` originales viven en `.agents/archived-skills/fusionados-20261013/` (restaurables).

## ⚡ Resumen operativo (sin cargar referencias)

- **Modo activo del harness**: `cat SCRIPTS/harness_mode.json` · cambiar: `bash SCRIPTS/harness_mode.sh <N> < /dev/null` (modos 1–6, ver `references/select.md`).
- **Doctor de motores/DSH**: `python3 SCRIPTS/harness_doctor.py` (pasivo, $0.00).
- **Escaneo de APIs + ranking + propuesta de cadena**: `python3 SCRIPTS/harness_api_scan.py --scan --rank --propose` (R1, $0.00, **nunca auto-aplica**; detalle en `references/api-scan.md`).
- **Regla #vetado**: NUNCA borrar líneas sueltas con `sed` en `~/.dsh/settings.yaml` — sustituir el ID del modelo por el sucesor vivo.
- **Parser canónico del `.env`**: `SCRIPTS/env_loader.py` (`env_line`, `load_env`). Prohibido reintroducir `split("=", 1)`: el SSOT admite comentarios inline `# endpoint:`.
- **Evidencia antes de Afirmar**: ninguna conmutación o rescate se cierra sin mostrar el JSON/exit 0 resultante.
- **Obligación en Auditorías de APIs**: Toda evaluación, benchmarking o redefinición del arnés DEBE incluir por defecto pruebas activas de NVIDIA NIM (4 cuentas C1, C2, C7, C9 y proxy local :8088) y OpenRouter C7 (cuenta fondeada protegida, 1.000 req/día en modelos :free) junto a C1..C6. Prohibido omitirlas o darlas por supuestas.
- **Tombstone de motor**: `Kimi K3` está **EOL** (`410 Gone` en NIM, 2026-10-15) y no figura en ninguna cadena. La API directa de Moonshot es **de pago** y queda fuera del harness. Sustitutos: `nemotron-3-ultra-550b-a55b` y `nemotron-3.5-super-vl-120b-a12b`. No reintroducirlo.
- **Dónde consultar el estado completo**: `memory-bank/technical/HARNESS_FLOYDIA_V41_INDICE.md` (índice de una página) · `memory-bank/journal/2026-10-21_harness_floydia_v41_handoff.md` (handoff) · NotebookLM *"FLOYDIA - HARNESS v4.1 (SSOT 2026-10-21)"* (id `a94ef989-9cc9-4a01-a7c9-bac58fa6e038`).
- **Motor por defecto del sistema**: `minimax/minimax-m3.1-flash:free` vía `openrouter_c7` (94 % de capacidad, 1 045 ms, $0.00, **con visión probada**). Configurado en los 4 campos (`model`, `small_model`, `default_model`, `agent.*.model`).
- **Identidad de motor**: el proxy NIM **reescribe** lo que se pide (`deepseek-ai/deepseek-v4.1-flash` → `private/nvidia/nemotron-3.5-super-120b-a12b`). Para saber qué sirve realmente cada motor: `python3 SCRIPTS/harness_api_scan.py --canary`.
