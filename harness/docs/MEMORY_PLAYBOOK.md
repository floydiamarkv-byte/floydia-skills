# MEMORY_PLAYBOOK — destino de la información

Regla base: **lo que otro agente necesita se escribe en disco; lo que el modelo necesita se carga por demanda.**

| Tipo | Destino | Nunca | Por qué |
|---|---|---|---|
| Hecho transversal (usuario, IP, estilo) | memoria del agente (L2) | journal | se inyecta en cada turno; debe ser pequeño |
| Procedimiento reproducible | skill (L3) | memoria | se carga sólo cuando aplica |
| Decisión con fecha, coste y evidencia | `memory-bank/journal/` (L4), append-only | chat | el chat no es auditable |
| Doctrina externa consolidada | NotebookLM (L5) | skill | cambia fuera del repo |
| Precio, límite, ID de modelo | SSOT en disco + cita de ruta | memoria, skill, prosa | una sola verdad numérica (R10) |
| Handoff de sesión | L4 + **índice** `journal/INDEX.md` | sólo el fichero suelto | 170/173 quedaron sin lector |

## Presupuesto de contexto

- Arranque medido: `activeContext` 381 tokens + `notes-next-session` 847 (límite 2 500 cada uno) → PASS.
- Índice de 83 skills ≈ 2 640 tokens; 21 MCP ≈ 40k de esquemas. **Carga perezosa obligatoria: ≤ 2 MCP y ≤ 2 skills por tarea (R14).**
- Métrica *Token-to-Utility* = llamadas exitosas / tokens de esquema cargado. Expulsar todo MCP con 0 llamadas en N tareas de su clase.

## Medición 2026-11-07 (últimas 10 sesiones)

- MCP con 0 llamadas: `notebooklm-mcp`, `obsidian-mcp`, `colab`, `google-cloud`, `google-ads-mcp`, `stitch`.
- Los 7 tenants `novamira-*` aparecen exactamente 63 veces (= nº de peticiones): sólo están en la definición de herramientas, sin uso.
- 7 de 83 skills sin mención: `almacenamiento-nas`, `hermes-runtime-audit`, `apple-notes`, `imessage`, `apple-reminders`, `findmy`, `teams-meeting-pipeline`.
- Recall@1: era 6/10 (FREE) y 5/10 (GO) con grep por patrón. Arreglado a **10/10 y 10/10** con dos cambios:
  (1) los hechos que solo vivían en el chat o en mi memoria se escribieron en `memory-bank/core/techContext.md`;
  (2) `SCRIPTS/memory_recall.py` recupera **párrafos** puntuados por solapamiento de términos (BM25-lite)
  en vez de la primera coincidencia de un patrón que escribía quien preguntaba. El modelo no cambió:
  el cuello era la recuperación, no el tamaño.

## Reglas

1. Antes de escribir en memoria: ¿esto cambia una decisión en cualquier sesión futura? Si no, va a journal.
2. Todo handoff nace con una línea en `journal/INDEX.md` (fecha · tema · ruta · estado). Sin índice, no existe.
3. Las cifras se citan con ruta de SSOT; si dos fuentes discrepan, se declara vencedora y **se purga la otra en el mismo cambio** (R10).
4. Los `f-*` son symlinks: se edita `.agents/skills/<name>/SKILL.md`, nunca la ruta de `~/.hermes/skills`.
