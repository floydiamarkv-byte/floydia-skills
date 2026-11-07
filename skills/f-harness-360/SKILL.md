---
name: f-harness-360
description: "Auditoría TOTAL del harness en una sola llamada: escanea APIs, evalúa, consulta el enjambre y a una IA externa, propone y (con token) redefine el harness. USAR con /harness-360, /auditoria-total, /redefinir-harness-total, 'audita todo el harness', 'revisa todo y dime qué cambiar'."
version: 1.0.0
author: HermesHP15
triggers:
  - /harness-360
  - /auditoria-total
  - /auditoria-completa
  - /redefinir-harness-total
  - audita todo el harness
  - revisa todo el harness
  - escanea todo y redefine
  - auditoria total del harness
metadata:
  hermes:
    tags: [harness, routing, audit, swarm, orchestration, evidence]
    related_skills: [f-harness, api-engine-availability-audit, f-evidence-engine]
---

# f-harness-360 — una llamada, ciclo completo

Este skill existe para que **no haya que recordar el runbook**: se invoca, corre el pipeline completo,
deja artefactos y devuelve un veredicto. El detalle de cada etapa vive en `f-harness` (runbook de 11
pasos) y la doctrina de decisión en `api-engine-availability-audit`; aquí solo está el disparador y el
contrato.

## La llamada

```bash
cd <PROYECTO>

python3 SCRIPTS/harness_full_audit.py --run                # ciclo completo (~10 min, incluye banco ciego)
python3 SCRIPTS/harness_full_audit.py --run --fast          # sin banco ni recall (~25 s)
python3 SCRIPTS/harness_full_audit.py --run --apply         # escribe SSOT (EXIGE token humano)
python3 SCRIPTS/harness_full_audit.py --run --no-external    # sin consulta a IA externa
```

Sin `--run` el script imprime la ayuda y no toca nada. Sin `--apply` **no escribe** ningún SSOT: deja
propuesta y diff. `--apply` solo se usa con orden explícita del operador (R3), y aun así hace backup
`.bak-<ts>` antes de cada fichero.

## Qué hace en cada etapa

| # | Etapa | Qué verifica | Artefacto |
|---|---|---|---|
| 0 | preflight | proxy `/health`, cuentas disponibles | aborta con exit 3 si el proxy está caído |
| 1 | registro | catálogo vivo → 79 entradas con TTL | `out/model_state_registry.json` |
| 2 | contexto | `limit.context` (GO) · `context_length` (OR) · `inputTokenLimit` (Google) | `ctx_status` VERIFIED/UNPUBLISHED |
| 3 | lint | gramática, ctx real, IDs, duplicados por proveedor | exit 2 si hay deriva |
| 4 | nombres | `[ESTADO][CTX][MODO]`; con `--apply` reescribe el catálogo | backup + JSONC válido |
| 5 | allowlist | regenerada desde `/api/v1/models` (precio 0 + tools) | `providers/c7_allowlist.yaml` |
| 6 | suite | overlay que la Suite consume + cotejo | `SIN_DERIVA` o exit 2 |
| 7 | banco ciego | 8 tareas × 2 modos × 3 reps, VCR, seed 42, McNemar | `out/publicable_*_v2.json` |
| 8 | recall | 10 preguntas contra el vault | `out/recall_test.json` |
| 9 | conmutador | GO⇄FREE atómico con P50/P95/P99 | `out/switch_bench.json` |
| 10 | **enjambre** | SSOT MCP vs lo que declara cada cliente vs lo que responde Hermes | `hermes_down` / `hermes_disabled` (¡distintos!) |
| 11 | **revisión externa** | un modelo externo audita el resumen y devuelve JSON cerrado | `revision_externa` con `validado` |
| 12 | dashboard | recalcula todas las cifras desde los artefactos | `dashboard.html` |

Salidas: `out/full_audit_<ts>.json` (máquina) · `FULL_AUDIT.md` (persona) · `out/full_audit_<ts>.log` (crudo).
Códigos: **0** VERDE · **2** ROJO (etapa fallida, lint > 0, Suite con deriva o MCP habilitado caído) · **3** abortado.

## Reglas que el orquestador hace cumplir

1. **Un MCP deshabilitado no es un MCP caído.** `hermes mcp list` marca `✗ disabled` para lo que se apagó
   a propósito y `✗` a secas para lo que falla; confundirlos inventa una alerta en cada corrida.
2. **El revisor externo también se audita (R12).** Se le pasa solo el resumen, se le prohíbe hablar de
   campos ausentes y luego se comprueba que sus cifras y sus tokens técnicos existen en el payload
   (`validado: false` si inventa). Un veredicto de un modelo que alucina métricas no es evidencia.
3. **Sin `--apply` no se escribe SSOT.** La corrida por defecto es propuesta + evidencia.
4. **El veredicto lo decide el artefacto, no la prosa**: etapa fallida, lint o deriva de Suite → ROJO.
5. **`--fast` es para vigilar, no para publicar**: se salta banco y recall (los dos caros) y nunca debe
   citarse como certificación.

## Cuándo NO usarlo

- Para un solo motor o una caída concreta: `api-engine-availability-audit` (8 pasos, barato).
- Para cambiar de modo o cadena sin auditar: `f-harness` modo SELECTOR (`harness_mode.sh`).
- Para descomponer un proyecto: `f-orquestador-floydia`.
