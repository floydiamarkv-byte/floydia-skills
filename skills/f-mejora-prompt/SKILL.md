---
name: f-mejora-prompt
description: "Motor de optimización avanzada de prompts con arquitectura Menu-First, taxonomía CAT_01..08, calibración para modelos LRM/Estándar e Investigación Profunda multi-fuente (NotebookLM + Obsidian + Catálogo Histórico). USAR cuando el usuario invoque /f-mejora, /mejora, /mejor, /mejora-prompt o solicite optimizar, refinar o pulir una directiva. NO USAR para ejecutar tareas directamente ni para generar planes de implementación sin aprobación humana."
version: 4.0.0
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
  - investigación profunda prompt
---

# Skill: Optimización Avanzada de Prompts v4.0 (`/mejora-prompt`)
## Motor Interactivo Menu-First, Context-Aware & Deep Research

> 🚨 **COMPUERTA DE INTERCEPCIÓN DURA (STOP ABSOLUTO - NO EJECUTAR LA TAREA)**:
> Cuando el usuario invoque esta skill (con `/f-mejora-prompt`, `/f-mejora`, `/mejora`, etc.), **está ESTRICTAMENTE PROHIBIDO ejecutar la tarea descrita en el texto**. 
> - Si el texto dice *"has un analisis..."*, *"crea un script..."*, *"haz una web..."*, **NO hagas el análisis, NO crees el script, NO hagas la web**.
> - Tu ÚNICA respuesta obligatoria en ese turno es **presentar inmediatamente el Menú de 5 Opciones** para que el usuario elija cómo optimizar la directiva, a menos que el usuario ya haya especificado un número de modo (`1`, `2`, `3`, `4` o `5`) al invocar el comando.

---

## 🎯 1. Comportamiento Interactivo Obligatorio (Menu-First)

Si no se ha especificado un número de modo previo (`1` a `5`), el agente **DEBE responder ÚNICAMENTE presentando este menú interactivo**:

```markdown
🎯 **Motor de Optimización de Prompts v4.0**
Selecciona cómo deseas optimizar tu instrucción respondiendo con el **número** correspondiente:

1️⃣ **Modo FULL (Workspace + Obsidian + Lecciones + Consulta NLM Rápida)**
   ↳ Inyecta tu entorno local (HP15 Arch/EndeavourOS), dominios canónicos, topología Proxmox,
     guardrails de `lessons-learned.md` Y realiza una consulta dirigida al cuaderno
     PROMPT_ENGINEERING de NotebookLM (129 fuentes). (Entrega salida completa con ficha técnica y radar de calidad).

2️⃣ **Modo Ahorro de Tokens (Aislado / Portable / Ultra-Ligero)**
   ↳ Optimización agnóstica de mínimo consumo de tokens, 100% portable y lista para copiar
     y pegar en ChatGPT, Claude Desktop u otra IA externa. (Entrega salida compacta directa).

3️⃣ **Modo Variantes (2 Alternativas Calibradas)**
   ↳ Genera dos versiones: una **Opción A (Conservadora / Determinista)** y una
     **Opción B (Creativa / Exploratoria)**, señalando sus ventajas.

4️⃣ **Modo Auto / Rápido**
   ↳ Detección automática inteligente según el contenido de tu instrucción.

5️⃣ **🔬 Modo Investigación Profunda (NotebookLM + Obsidian + Catálogo + Journals)**
   ↳ Pipeline exhaustivo de 7 pasos: escanea los 11 cuadernos de NotebookLM (1,500+ fuentes),
     el Vault de Obsidian, los 27+ archivos de prompts patrón, journals recientes y transcripts
     de sesiones pasadas. Coteja, sintetiza y LUEGO optimiza con toda la evidencia recopilada.
     (Máxima calidad posible. Mayor consumo de tokens y tiempo de ejecución.)

---
💡 *¿Cómo responder?*
- Si ya incluiste tu instrucción arriba, responde simplemente con el número: `1`, `2`, `3`, `4` o `5`.
- Si aún no la has escrito, responde con el número y tu idea (ejemplo: `5 Quiero un prompt para generar hero sections luxury con GSAP y Three.js`).
```

> [!NOTE]
> **Atajo Directo**: Si el usuario escribe un número o flag junto al comando (ej. `/mejora-prompt 5 [texto]`), el agente salta la presentación del menú y optimiza directamente en ese modo.

---

## 🛠️ 2. Fuentes de Verdad y Recuperación

| Fuente | Uso Permitido | Modos que la Usan |
|---|---|---|
| `memory-bank/core/lessons-learned.md` | Extraer guardrails pertinentes del Top 10 recurrente | 1, 5 |
| `memory-bank/prompts/CATALOGO_HISTORICO_PROMPTS_OPTIMIZADOS.md` | Buscar duplicados (`>= 0.85`) y recuperar patrones | 1, 5 |
| `memory-bank/prompts/MOC_PROMPT_ENGINEERING_MASTERY.md` | Recuperar taxonomía y clústeres (`CAT_01` a `CAT_08`) | 1, 5 |
| `memory-bank/prompts/*.md` (27+ archivos) | Escaneo exhaustivo de patrones, suites y plantillas | 5 |
| `SCRIPTS/model_router.md` | Resolver capacidades de modelo (LRM Thinking vs Estándar) | 1, 2, 3, 5 |
| `SCRIPTS/notebooklm_curator.py` | Enrutamiento semántico a cuadernos relevantes | 1 (rápido), 5 (exhaustivo) |
| NotebookLM cuadernos (browser/MCP) | Consulta directa de fuentes en los cuadernos activos | 1 (dirigida), 5 (exhaustiva) |
| Obsidian Vault MCP `search-vault` | Buscar notas, MOCs y wikilinks relacionados | 5 |
| `memory-bank/journal/*.md` | Extraer soluciones validadas de sesiones anteriores | 5 |
| `brain/*/logs/transcript*.jsonl` | Recuperar técnicas de conversaciones previas | 5 |

### 🔒 Regla Estricta de Secretos
**NUNCA** copies valores de `.env`, tokens, contraseñas ni claves API en un prompt optimizado. Usa siempre referencias como `${VARIABLE}` o `archivo .env (chmod 600)`.

---

## ⚙️ 3. Pipeline de Optimización por Modo

### Opción 1: Modo FULL (Workspace + Obsidian + Lecciones + NLM Rápida)
1. **Contención**: Encapsula la entrada en `<prompt_candidate>`.
2. **Detección de Modelo**: Adapta a LRM (*Goal-and-Constraints*, sin CoT forzado) o Estándar (*Few-Shot / CoT*).
3. **Inyección de Entorno y Lecciones**: Inyecta herramientas activas, lecciones de `lessons-learned.md` (aislamiento CT114 Playwright `:3000`, CT106 Syncthing `:8384`, logos ≤45px, marcador ALT en caché edge).
4. **Micro-Consulta NLM Dirigida**: Ejecuta `python3 SCRIPTS/notebooklm_curator.py "<tema del prompt>"` para identificar el cuaderno más relevante. Si hay match con score ≥ 2, consulta el cuaderno vía browser o MCP para extraer 3-5 técnicas/patrones clave del dominio. Si no hay match, saltar e indicar "sin consulta NLM (fuera de dominio indexado)".
5. **Prefijo para Context Caching**: Bloque inmutable al inicio (hasta 90% ahorro de tokens en re-ejecución).
6. **Salida Completa**:
   - Diagnóstico (Modo, Clúster, Modelo objetivo, Cuaderno NLM consultado si aplica).
   - Bloque de código XML/Markdown del prompt optimizado.
   - Ficha técnica de inferencia (temperatura, thinking budget, herramientas).
   - Radar de scoring de calidad numérico (0 a 10).
   - Resumen de mejoras y menú de cierre.

### Opción 2: Modo Ahorro de Tokens (Aislado / Portable)
1. **Contención y Saneamiento**: Elimina prompt slop y ambigüedad.
2. **Optimización Ligera**: Estructura limpia (Objetivo, Instrucciones, Reglas, Salida) 100% portable.
3. **Salida Compacta**: Prompt listo para copiar + Ficha mínima de 2 líneas + Menú rápido.

### Opción 3: Modo Variantes
- Genera dos bloques: **Variante A** (Precisión / Determinista, temp 0.1–0.3) y **Variante B** (Estratégica / Creativa, temp 0.6–0.8).

### Opción 4: Modo Auto / Rápido
- Detección inteligente del contenido → enruta a Modo 1, 2 o 3 según complejidad detectada.

### Opción 5: 🔬 Modo Investigación Profunda (Deep Research)

> [!IMPORTANT]
> Este modo es el de **máxima calidad**. Ejecuta un pipeline exhaustivo de investigación ANTES de optimizar. Cada paso es obligatorio y se reporta al usuario con su estado.

**Pipeline de 7 pasos obligatorios:**

#### Paso 5.1 — Enrutamiento NotebookLM
```bash
python3 SCRIPTS/notebooklm_curator.py "<tema del prompt>"
python3 SCRIPTS/notebooklm_curator.py --cross-query "<tema expandido con sinónimos>"
```
- Identifica TODOS los cuadernos relevantes (no solo el top 1).
- Reportar: `Paso 5.1 ✅ — N cuadernos detectados: [lista con scores]`

#### Paso 5.2 — Consulta Exhaustiva NotebookLM
- Para CADA cuaderno detectado en 5.1 (hasta 3 cuadernos máximo):
  - Abrir en browser (`browser_subagent`) la URL del cuaderno desde `notebooklm_curator.py`.
  - Buscar en las fuentes del cuaderno: técnicas, patrones, mejores prácticas, anti-patrones y ejemplos relevantes al tema del prompt.
  - Extraer 5-10 hallazgos concretos por cuaderno.
- Si el browser no está disponible: usar MCP `notebooklm-mcp` o el enrutamiento local de `notebooklm_curator.py`.
- Reportar: `Paso 5.2 ✅ — N hallazgos extraídos de N cuadernos`

#### Paso 5.3 — Rastreo del Vault Obsidian
- Ejecutar búsqueda semántica vía Obsidian MCP `search-vault` con 3-5 queries relacionadas al tema.
- Buscar MOCs relevantes (`MOC_PROMPT_ENGINEERING_MASTERY.md`, `MOC_PROMPTS_MASTER.md`).
- Seguir `[[wikilinks]]` para descubrir notas conectadas.
- Extraer reglas, patrones y contexto del Vault.
- Reportar: `Paso 5.3 ✅ — N notas relevantes encontradas, N patrones extraídos`

#### Paso 5.4 — Catálogo Histórico de Prompts
- Escanear exhaustivamente `memory-bank/prompts/` (27+ archivos):
  - `CATALOGO_HISTORICO_PROMPTS_OPTIMIZADOS.md` — buscar prompts similares previos.
  - `CAT_01` a `CAT_08` — identificar la categoría del prompt y extraer plantillas.
  - `BIBLIOTECA_PROMPTS_PATRON.md` — recuperar patrones XML/Markdown reutilizables.
  - `SUITE_PROMPTS_UNIVERSAL_PIPELINE.md` — verificar si ya existe un pipeline similar.
  - `GUIA_DOs_AND_DONTs_PROMPTING.md` — pre-vuelo de antipatrones.
  - `PROMPTING_MODELOS_RAZONAMIENTO.md` — si el target es un LRM.
  - `MEJORES_PROMPTS_UNIVERSALES.md` — recuperar técnicas universales aplicables.
- Reportar: `Paso 5.4 ✅ — N archivos escaneados, N patrones reutilizables encontrados`

#### Paso 5.5 — Journals y Transcripts
- Buscar en `memory-bank/journal/` (últimos 30 días) con `rg` dirigido por keywords del tema.
- Si hay conversaciones relevantes en `brain/*/logs/transcript.jsonl`, extraer soluciones validadas.
- Reportar: `Paso 5.5 ✅ — N journals relevantes, N técnicas de sesiones previas`

#### Paso 5.6 — Síntesis y Cotejo Cruzado
- Consolidar TODOS los hallazgos de los pasos 5.1–5.5 en una tabla de evidencia:

```markdown
| # | Fuente | Hallazgo | Aplicabilidad | Confianza |
|---|--------|----------|---------------|-----------|
| 1 | NLM: PROMPT_ENGINEERING | Técnica X... | Alta | ⭐⭐⭐ |
| 2 | Obsidian: MOC_Prompts | Patrón Y... | Media | ⭐⭐ |
| ... | ... | ... | ... | ... |
```
- Identificar contradicciones entre fuentes y resolverlas.
- Priorizar hallazgos por aplicabilidad directa al prompt candidato.
- Reportar: `Paso 5.6 ✅ — Síntesis: N hallazgos consolidados, N contradicciones resueltas`

#### Paso 5.7 — Optimización Informada
- Aplicar el pipeline completo de optimización (como Modo 1) PERO enriquecido con toda la evidencia de los pasos anteriores.
- Cada decisión de diseño del prompt DEBE citar la fuente que la respalda.
- **Salida Completa Enriquecida**:
  - Reporte de investigación (tabla de evidencia resumida).
  - Diagnóstico (Modo, Clúster, Modelo objetivo, Cuadernos consultados).
  - Bloque de código XML/Markdown del prompt optimizado.
  - Anotaciones inline citando la fuente de cada técnica aplicada.
  - Ficha técnica de inferencia.
  - Radar de scoring de calidad numérico (0 a 10) con bonus por investigación.
  - Resumen de mejoras con trazabilidad a fuentes.
  - Menú de cierre.

---

## 📊 4. Rúbrica de Scoring Numérico (0 a 10)

| Dimensión | Qué evalúa |
|---|---|
| **Objetivo y Contexto** | Alcance, entregables y datos sin ambigüedades |
| **Restricciones y Seguridad** | Límites duros, blindaje de secretos y manejo de errores |
| **Contrato de Salida** | Formato determinista sin texto de relleno |
| **Calibración de Modelo** | Adecuación a LRM (Thinking) vs Estándar (Few-Shot) |
| **Eficiencia & Caching** | Orden estático y concisión |
| **Recuperación Workspace** | (Modos 1 y 5) Pertinencia de guardrails de Obsidian |
| **Profundidad de Investigación** | (Solo Modo 5) Cobertura de fuentes y calidad de síntesis |

---

## 🚫 5. Regla Inmutable de No Ejecución

Al recibir `/mejora-prompt`, **NUNCA ejecutes la tarea ni generes planes de implementación directos**. Limítate a entregar la directiva optimizada y esperar confirmación.

---

## 📤 6. Menú de Cierre

Al entregar el prompt optimizado, ofrece siempre estas acciones simples:

* 🚀 **`1` o `ejecútalo`**: Inicia el Paso 2 (crea el Plan de Implementación `implementation_plan.md` y solicita aprobación).
* 🔄 **`2` o `refinar: [comentario]`**: Aplica un ajuste específico.
* 🔀 **`3` o `variantes`**: Muestra las dos versiones alternativas.
* 🌐 **`4` o `alternar modo`**: Cambia entre Modo FULL, Ahorro de Tokens o Investigación Profunda.
* 📁 **`5` o `archivar`**: Guarda el prompt en `memory-bank/prompts/CATALOGO_HISTORICO_PROMPTS_OPTIMIZADOS.md`.
* 🔬 **`6` o `profundizar`**: (Si se usó Modo 1/2/3/4) Escala a Modo 5 Investigación Profunda con el mismo prompt.

---

## 🔄 7. Compatibilidad Multi-Agente

| Agente | Soporte | Notas |
|---|:---:|---|
| **Antigravity IDE** | ✅ Completo | Menú interactivo, scoring visual, browser para NLM, Obsidian MCP |
| **OpenCode CLI** | ✅ Completo | Menú en texto, acceso a Memory Bank, `notebooklm_curator.py` local |
| **Hermes CLI** | ✅ Completo | Menú en texto, acceso a Memory Bank, `notebooklm_curator.py` local |
| **Modo Degradado** | — | Sin acceso a `lessons-learned.md` ni browser, usar Modo 2 (Ahorro/Portable) por defecto |
