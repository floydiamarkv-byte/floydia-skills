# memory_map — 7 capas de almacenamiento del harness

| Capa | Qué contiene | Ruta | Tamaño medido | TTL / frescura |
|---|---|---|---|---|
| **L0** preflight / índice AST | `activeContext`, `notes-next-session`, índice del grafo | `memory-bank/core/` | 381 + 847 tokens (límite 2 500 c/u) | cada sesión |
| **L1** SSOT de entorno | 431 variables, claves por cuenta | `.env` → `~/.secrets/antigravity.env` (`env_loader.py`) | 431 claves | al rotar credencial |
| **L2** memoria del agente | hechos transversales, preferencias | `~/.hermes/memories/` | 2 188 / 2 200 chars (99 %) | revisar cuando crece |
| **L3** skills | 83 skills; índice ≈ 2 640 tokens | `~/.hermes/skills` (los `f-*` son symlinks a `.agents/skills/`) | 83 SKILL.md | ≤ 30 d |
| **L4** vault | `journal/`, `events/`, `technical/` | `memory-bank/` → `~/.local/share/floydia/memory-bank` | 173 handoffs en 30 d | append-only |
| **L5** NotebookLM | doctrina web/SEO consolidada | notebooks `[WEB] *` | 5 notebooks citados | por curación |
| **L6** MCP | 21 servidores; SSOT `mcp_config.full.json`, proyección `mcp_config.json` | `~/.gemini/config/` | 21 servidores, ≈3,2 GB RSS con 3 clientes | ≤ 7 d |

## Resolución en 3 niveles (ortogonal a las capas)

1. **L1 caché inmediato** — `activeContext`, `notes-next-session`, `techContext`, `.env`. Coste 0, sin búsqueda.
2. **L2 vault dirigido** — `lessons-learned` (≤120 líneas), MOCs, Obsidian MCP. Coste 1 lectura.
3. **L3 `rg` acotado** — sólo si 1 y 2 no responden. Coste variable, requiere patrón.

**Empezar por L3 es error de método**: medido, 10/10 recuperaciones encontraron fichero pero sólo 60 % dieron el dato, porque el `grep` devuelve la primera coincidencia del patrón, no el pasaje que responde.

## Qué falta (crear)

1. **Registro de estado con TTL** — `SCRIPTS/model_state_registry.json`, generado. Propuesta lista en `out/model_state_registry.json`.
2. **Log append-only de routing** — decisión, modelo, coste, resultado de verificación, por tarea. Sin él la memoria narra pero no prueba.

## Fallos conocidos y evidencia

| Fallo | Evidencia 2026-11-07 |
|---|---|
| F1 amnesia de sesión | 170/173 handoffs sin referencia externa |
| F2 deriva SSOT↔realidad | 1 320 / 170 / 60 conviviendo; allowlist 4/10 muerta |
| F3 allowlist podrida | `c7_allowlist.yaml` con IDs que no existen en `/api/v1/models` |
| F4 tool drift MCP | `crawl4ai` caído; 6 servidores con 0 llamadas en 10 sesiones |
| F5 symlinks no editables | `skill_manage` falla en `f-*`; editar `.agents/skills/` |
| F6 colisión de nombres | 3 IDs repetidos entre proveedores Google (legítimo, pero el lint debe acotarlo) |
| F7 presupuesto de contexto | 2 640 tokens de índice + ~40k de MCP para 8 tareas distintas |
