---
name: f-mejora-prompt
description: "🚨 STOP OBLIGATORIO: Optimizador de prompts v5.1 Menu-First. PROHIBIDO ejecutar la tarea del usuario, buscar en archivos o escribir código. Tu ÚNICA respuesta inicial debe ser emitir el MENÚ interactivo de 8 modos (salvo que el usuario incluya un dígito 1-8). Invocar con /f-mejora-prompt o /mejora."
version: 5.4.0
triggers:
  - /f-mejora
  - /f-mejora-prompt
  - /mejora
  - /mejor
  - /mejora-prompt
  - optimizar prompt
  - mejorar prompt
  - refinar prompt
  - pulir prompt
  - optimize prompt
  - improve prompt
  - investigacion profunda prompt
  - escaneo de apis
  - escaneo apis
  - reanaliza harness
  - ranking modelos
  - seleccion harness
  - seleccionar harness
  - cual harens usar
  - que harness usar
---

# Skill: Optimización Avanzada de Prompts v5.1 (`f-mejora-prompt`)
## Motor Interactivo Menu-First, Formato Bloque .md Canónico & Recuperación SSOT

> 🚨 **COMPUERTA DE INTERCEPCIÓN DURA (STOP ABSOLUTO — NUNCA EJECUTAR LA TAREA NI LLAMAR HERRAMIENTAS)**:
> Cuando el usuario invoque esta skill (con `/f-mejora-prompt`, `/f-mejora`, `/mejora`, etc.):
> 1. **ESTÁ ESTRICTAMENTE PROHIBIDO EJECUTAR LA TAREA DEL TEXTO**:
>    - Si el texto dice *"haz una web..."*, *"despliega el servicio..."*, *"analiza el bug..."*, *"actualiza el sistema..."*, **NO programes la web, NO modifiques código, NO ejecutes comandos de solución, NO crees `implementation_plan.md`**.
>    - Tu único rol es **OPTIMIZAR Y BLINDAR LA DIRECTIVA** para que pueda ejecutarse con máxima precisión.
> 2. **PROHIBIDO LLAMAR HERRAMIENTAS EN TURNO 0 (REGLA CERO-HERRAMIENTAS)**:
>    - Si el usuario no especificó un número de modo (`1` a `8`), **ESTÁ PROHIBIDO LLAMAR A NINGUNA HERRAMIENTA** (`view_file`, `grep_search`, `find_by_name`, `run_command`, etc.). NO busques código, NO investigues el tema del usuario.
>    - **DETENTE EN ESE MISMO TURNO** y presenta **ÚNICAMENTE** el menú interactivo en texto directo como tu respuesta.

---

## 🎯 1. Menú Interactivo Obligatorio (Menu-First)

Si no se ha recibido un número de modo previo (`1` a `7`), el agente responde **inmediatamente con este menú**:

```markdown
🎯 **Motor de Optimización de Prompts v5.1**
Selecciona cómo deseas optimizar tu instrucción respondiendo con el **número** correspondiente:

1️⃣ **Modo FULL (Workspace + Obsidian + Lecciones + Consulta NLM Rápida)**
   ↳ Inyecta tu entorno local (HP15 MX Linux / Debian 13), dominios canónicos, topología Proxmox,
      guardrails de `lessons-learned.md` y realiza una consulta dirigida al cuaderno
      PROMPT_ENGINEERING de NotebookLM (129 fuentes). Entrega salida completa con ficha técnica.

2️⃣ **Modo Ahorro de Tokens (Aislado / Portable / Ultra-Ligero)**
   ↳ Optimización agnóstica de mínimo consumo de tokens, 100% portable y lista para copiar
      y pegar en ChatGPT, Claude Desktop u otra IA externa sin contexto local.

3️⃣ **Modo Variantes (2 Alternativas Calibradas)**
   ↳ Genera dos versiones: **Opción A (Conservadora / Determinista)** y **Opción B (Creativa / Exploratoria)**.

4️⃣ **Modo Auto / Rápido**
   ↳ Detección automática inteligente según la complejidad y el contenido de tu instrucción.

5️⃣ **🔬 Modo Investigación Profunda (NotebookLM + Obsidian + Catálogo + Journals)**
   ↳ Pipeline exhaustivo de 7 pasos: escanea los 11 cuadernos de NotebookLM (1,500+ fuentes),
      el Vault de Obsidian, los 27+ archivos de prompts patrón y journals recientes. Coteja, sintetiza
      y optimiza con evidencia documentada. (Máxima calidad analítica).

6️⃣ **🐝 Modo Enjambre Multiconsulta (Consenso 5 Motores a coste $0.00)**
   ↳ Despacho concurrente a motores del harness (Nemotron 3 Ultra 550B, DeepSeek R1 Distill, Gemini Flash, etc.) para
      contrastar enfoques y sintetizar una directiva maestra consensuada.

7️⃣ **⚙️ Modo Harness (Optimiza + Invoca Harness Adecuado)**
   ↳ Analiza la tarea, selecciona el modo del harness óptimo (1‑Full Power, 2‑Working Horse, 3‑NIM Only,
      4‑AGY+Free, 5‑Free Light) y genera el prompt optimizado **ya prefijado con la invocación**
      `/f-harness <modo>` lista para copiar/pegar. Ideal para delegar a la IA externa o ejecutar en
      sesión harness sin pasos extra.

8️⃣ **🔍 Modo Escaneo de APIs y Selección de Harness**
   ↳ Re-analiza el inventario de APIs auditado (`AUDITORIA_APIS_COMPLETA_2026-10-20`), clasifica proveedores
      por estado (OPERATIVA/SIN_VALOR/BLOQUEADA/INACCESIBLE/402/403), cruza con rankings de inteligencia
      y rendimiento (Artificial Analysis, LMArena/Chatbot Arena, OpenRouter) y sentimiento técnico
      (last30days, Reddit/HN), y recomienda el modo de harness y el modelo óptimo para la tarea.
      Ideal para decidir qué harness usar o redefinir según qué APIs están disponibles y el nivel
      de inteligencia de los modelos.

---
💡 *¿Cómo responder?*
- Si ya incluiste tu directiva arriba, responde simplemente con el número: `1`–`7`.
- Si aún no la has escrito, responde con el número y tu idea (ejemplo: `7 Quiero un prompt para refactorizar un módulo Python legacy`).
```

> [!TIP]
> **Atajo Directo**: Si el usuario escribe el número junto al comando (ej. `/f-mejora-prompt 1 [texto]` o `7 optimiza esto...`), el agente salta la presentación del menú y optimiza directamente en ese modo.

---

## 📦 2. FORMATO DE ENTREGA CANÓNICO: BLOQUE .md ÚNICO

> 💎 **CONTRATO OBLIGATORIO DE RESPUESTA (PREDETERMINADO)**:
> El usuario exige que toda directiva o prompt optimizado se entregue **DENTRO DE UN ÚNICO BLOQUE DE CÓDIGO MARKDOWN (` ```markdown ... ``` `)**.
> - **Prohibido**: Entregar prompts divididos en múltiples bloques rotos o mezclar explicaciones dentro del bloque del prompt.
> - **El bloque `.md` debe ser 100% autocontenido**: listo para copiar y pegar con un solo clic.

### Estructura de la Respuesta al entregar el prompt:

1. **Breve Diagnóstico** (1-3 líneas: Modo seleccionado, Modelo objetivo, Clúster temático).
2. **Bloque Markdown Canónico**:
````markdown
```markdown
# [TÍTULO CLARO Y DETERMINISTA DEL PROMPT]

> **Rol y Objetivo**: ...
> **Modelo Recomendado**: LRM / Estándar | Temperatura sugerida: 0.1 - 0.3

## 🎯 Objetivo Principal
...

## 🔒 Reglas Inmutables y Restricciones
...

## 📋 Instrucciones Paso a Paso
...

## 📤 Contrato de Salida
...
```
````
3. **Ficha Técnica y Radar de Calidad (0 a 10)** fuera del bloque.
4. **Menú de Cierre** (acciones siguientes).

---

## 🛠️ 3. Fuentes de Verdad y Recuperación SSOT

| Fuente | Uso Permitido | Modos que la Usan |
|---|---|---|
| `memory-bank/core/lessons-learned.md` | Extraer guardrails pertinentes del Top 10 recurrente | 1, 5 |
| `memory-bank/prompts/CATALOGO_HISTORICO_PROMPTS_OPTIMIZADOS.md` | Buscar duplicados (`>= 0.85`) y recuperar patrones | 1, 5 |
| `memory-bank/prompts/MOC_PROMPT_ENGINEERING_MASTERY.md` | Recuperar taxonomía y clústeres (`CAT_01` a `CAT_08`) | 1, 5 |
| `memory-bank/prompts/*.md` (27+ archivos) | Escaneo exhaustivo de patrones, suites y plantillas | 5 |
| `SCRIPTS/model_router.md` | Resolver capacidades de modelo (LRM Thinking vs Estándar) | 1, 2, 3, 5 |
| `SCRIPTS/notebooklm_curator.py` | Enrutamiento semántico a cuadernos relevantes | 1 (rápido), 5 (exhaustivo) |
| NotebookLM MCP / browser | Consulta directa de fuentes en cuadernos temáticos | 1 (dirigida), 5 (exhaustiva) |
| Obsidian Vault MCP | Buscar notas y wikilinks relacionados | 5 |
| `memory-bank/journal/*.md` | Extraer soluciones y fallas validadas recientemente | 5 |
| `/home/tec/Descargas/APIS/INFORME_AUDITORIA_APIS_COMPLETA_2026-10-20.md` + `.csv` | Inventario auditado de 226 variables de API, 67 proveedores, estados (OPERATIVA/SIN_VALOR/BLOQUEADA/INACCESIBLE/etc.), latencias y TTFT reales | 8 (nuevo) |
| `/home/tec/Descargas/APIS/IAS WEB/` | Catálogo técnico de APIs, rankings y sentimiento: Artificial Analysis API, LMArena HF, OpenRouter, Reddit/HN, queries de silent-nerf y rate-limit | 8 (nuevo) |
| `/home/tec/Descargas/APIS/Enjambre/` | Informe enjambre LLMs, modelos usados, stack MVP de enriquecimiento desde `.env`, matriz comparativa de fuentes de ranking | 8 (nuevo) |
| `SCRIPTS/model_router.md` | Matriz de 5 marchas del harness, rotación NIM C1/C2/C7/C9, capacidades C0..C6, modelos `:free` verificados | 1, 2, 3, 5, 8 |
| `SCRIPTS/harness_mode.sh` / `SCRIPTS/harness_mode.json` | Conmutación y consulta del modo activo del harness (1-6) | 7, 8 |
| `SCRIPTS/nim_rotator.sh` | Rotación round-robin de cuentas NVIDIA NIM con cooldown 429 y fail-fast 401/403 | 3, 8 |

### 🔒 Regla Estricta Anti-Fuga de Secretos
**NUNCA** copies valores de contraseñas, tokens de API o claves de `.env` en un prompt optimizado. Usa siempre variables de entorno genéricas como `${MI_VARIABLE}` o referencias de archivo `[REDACTED]`.

---

## ⚙️ 4. Pipeline de Optimización por Modo

### Opción 1: Modo FULL (Workspace + Obsidian + Lecciones + NLM Rápida)
1. **Contención**: Delimita el input del usuario en `<prompt_candidate>`.
2. **Calibración de Modelo**: Si es LRM (DeepSeek-R1 / Nemotron 3 Ultra 550B / O1 / O3), usa *Goal-and-Constraints* sin CoT forzado. Si es Estándar (Claude / GPT-4o / Gemini Flash), usa *Few-Shot* y pasos ordenados.
3. **Inyección de Guardrails Locales**: Inyecta entorno real (HP15 Debian 13 / MX Linux, CT114 Playwright :3000, CT106 Syncthing :8384).
4. **Consulta Rápida NLM**: Ejecuta `python3 SCRIPTS/notebooklm_curator.py "<tema>"` y si hay match, añade 2-3 técnicas clave.
5. **Entrega**: Formato canónico en bloque `.md` único + Ficha técnica.

### Opción 2: Modo Ahorro de Tokens (Aislado / Portable)
1. **Saneamiento**: Elimina "slop", relleno y ambigüedad.
2. **Estructura Compacta**: Rol, Objetivo, Reglas estrictas y Contrato de salida limpio.
3. **Entrega**: Bloque `.md` único ultra-ligero listo para web/chatbots.

### Opción 3: Modo Variantes
- Genera dos bloques `.md`: **Variante A (Determinista / Baja Temp 0.1)** y **Variante B (Estratégica / Creativa Temp 0.7)**.

### Opción 4: Modo Auto / Rápido
- Analiza la longitud y complejidad del texto. Si requiere entorno local → Modo 1; si es una consulta general → Modo 2.

### Opción 5: 🔬 Modo Investigación Profunda (Deep Research)
- Ejecuta los 7 pasos de investigación:
  1. Enrutamiento NotebookLM (`notebooklm_curator.py`).
  2. Consulta a los cuadernos activos detectados.
  3. Rastreo del Vault de Obsidian.
  4. Búsqueda en el Catálogo Histórico (`memory-bank/prompts/`).
  5. Consulta a Journals recientes (`memory-bank/journal/`).
  6. Síntesis y resolución de contradicciones en tabla de evidencia.
  7. Redacción del prompt final enriquecido en el bloque `.md` único.

### Opción 6: 🐝 Modo Enjambre Multiconsulta
- Despacha el borrador a motores disponibles del harness para extraer críticas constructivas y fusionar la mejor versión.
- **Composición de motores y reglas de consenso: SSOT en `memory-bank/prompts/ENJAMBRE_5_MOTORES_SSOT.md`** (nunca embeber la lista aquí).

### Opción 7: ⚙️ Modo Harness (Invocación Adecuada)
- El skill analiza la tarea del usuario y:
  1. **Detecta la dificultad**: razonamiento, medio, flash, etc.
  2. **Selecciona el modo del harness** más apropiado:
     - Modo 1 (Full Power): AGY → Nemotron Ultra 550B → DeepSeek V4.1 Flash → Pool
     - Modo 2 (Working Horse): V4 Flash → Nemotron Super → AGY → Laguna S
     - Modo 3 (NIM Only): Nemotron 3.5 Super VL, rotación NIM C1→C9
     - Modo 4 (AGY+Free): AGY → DeepSeek V4.1 Flash → Pool Free
     - Modo 5 (Free Light): Pool Free rotativo (Mistral, GLM, DashScope, Ollama)
   3. **Genera el prompt optimizado** con bloque `.md` canónico que **comienza con la invocación** `/f-harness <modo>`, seguida del objetivo y reglas del usuario.
   4. **Entrega** el prompt con ficha técnica y el comando listo para copiar/pegar en cualquier sesión harness.

### Opción 8: 🔍 Modo Escaneo de APIs y Selección de Harness
1. **Leer inventario de APIs**: parsea `AUDITORIA_APIS_COMPLETA_2026-10-20.md` (y su CSV) del workspace; extrae proveedor, endpoint, estado, latencia p50, TTFT, catálogo de entradas, modelo probado y cuota/tier.
2. **Clasificar disponibilidad**: agrupa por estado — `OPERATIVA` (candidata), `SIN_VALOR` (sin credencial), `BLOQUEADA`/`403` (denegada), `INACCESIBLE` (sin red/DNS), `SIN_SALDO`/`402` (sin crédito), `CREDENCIAL_INVALIDA` (401).
3. **Cruzar con rankings de inteligencia**: para cada proveedor/modelo operativo, consulta:
   - `Artificial Analysis API` (`GET /api/v2/language/models/free`) → Intelligence Index, tokens/s, TTFT, precios input/output.
   - `LMArena / Chatbot Arena` (dataset HF `lmarena-ai/leaderboard-dataset`) → Arena Score/Elo y CI.
   - `OpenRouter` (`GET /api/v1/models`) → pricing, contexto, disponibilidad y sorts (intelligence/latency/throughput/price).
4. **Capa de sentimiento técnico**: `last30days` + Reddit `.json`/PullPush + Hacker News Algolia con queries `<modelo> silent nerf | rate limit | 429 | best model | daily driver` (última semana/mes).
5. **Construir registro enriquecido por modelo**: `{slug, proveedor, estado, elo/ia_index, tps, ttft_s, precio_in, precio_out, contexto, sentimiento, senales_nerf, menciones_rate_limit, fuente, fecha_consulta}`.
6. **Recomendar modo de harness**: según la dificultad de la tarea y los modelos disponibles:
   - Razonamiento profundo/arquitectura → Modo 1 (Full Power) o 6 (AGY Deep) con Nemotron/Gemini Pro. [Kimi K3 retirado: EOL 2026-10-15]
   - Desarrollo diario → Modo 2 (Working Horse).
   - Solo NIM → Modo 3 (NIM Only).
   - Preservar cuota de pago → Modo 4 (AGY+Free).
   - Tareas triviales/$0.00 → Modo 5 (Free Light) con modelos `:free` auditados.
7. **Entrega**: bloque `.md` único con el inventario filtrado (solo OPERATIVA), tabla de rankings por modelo, recomendación de modo de harness (`/f-harness <N>`) y modelo óptimo, más ficha técnica y comando listo para ejecutar.

---

## 📤 5. Menú de Cierre

Al entregar el prompt optimizado en su bloque `.md`, ofrece las siguientes acciones rápidas:

* 🚀 **`1` o `ejecútalo`**: Inicia la fase de ejecución (crea el plan y solicita confirmación humana).
* 🔄 **`2` o `refinar: [ajuste]`**: Aplica una corrección o detalle específico.
* 🔀 **`3` o `variantes`**: Genera la versión alternativa complementaria.
* 📁 **`4` o `archivar`**: Guarda el prompt en `memory-bank/prompts/CATALOGO_HISTORICO_PROMPTS_OPTIMIZADOS.md`.
* 🔬 **`5` o `profundizar`**: Escala la directiva al Modo 5 de Investigación Profunda.
* ⚙️ **`6` o `con harness`**: Reenvía el prompt optimizado envolviéndolo en la invocación del harness adecuado
  (`/f-harness <modo> <prompt>`) para que la IA lo ejecute en cadena sobre los motores correctos.
