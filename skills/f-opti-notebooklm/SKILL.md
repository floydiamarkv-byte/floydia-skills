---
name: f-opti-notebooklm
description: "Curador, optimizador y enriquecedor soberano de la base de verdad Google NotebookLM. Permite seleccionar cuadernos específicos o todos los 11 cuadernos activos, buscar y sintetizar fuentes nuevas, enriquecer los cuadernos con hallazgos de sesiones y generar informes temáticos para el Memory Bank. USAR cuando el usuario invoque /f-opti-notebooklm, /opti-notebooklm, /curar-notebooks o solicite enriquecer/auditar cuadernos. NO USAR para consultas de código local sin relación con los cuadernos indexados."
version: 1.1.0
triggers:
  - /f-opti-notebooklm
  - /opti-notebooklm
  - /curar-notebooks
  - optimizar notebooklm
  - enriquecer cuadernos
  - notebooklm opti
  - curar notebooklm
---

# Skill: Optimizador y Curador Soberano de NotebookLM (`f-opti-notebooklm` v1.1)

> **Propósito**: Mantener la base de verdad de Google NotebookLM en máxima integridad y profundidad técnica. Proporciona un flujo guiado menu-first para enriquecer cuadernos con nuevas fuentes externas, hallazgos de sesiones y transcripciones pasadas, generar resúmenes ejecutivos para el Memory Bank y auditar la cobertura de los 11 cuadernos activos.

---

## 🎯 1. Menú Interactivo Menu-First

Al invocar `/f-opti-notebooklm`, `/opti-notebooklm` o solicitar curar/optimizar NotebookLM, el agente **DEBE responder presentando este menú interactivo en 2 pasos**:

```markdown
╔═══════════════════════════════════════════════════════════════════╗
║       🧠 F-OPTI-NOTEBOOKLM — CURADOR DE BASE DE VERDAD GOOGLE     ║
╚═══════════════════════════════════════════════════════════════════╝

### 📚 Paso 1: Selecciona el o los Cuadernos a Optimizar:
- `[0]` **Todos los Cuadernos** (11 cuadernos activos / 1,500+ fuentes)
- `[1]` 🐝 **BEE_IoT** (ESP32, LoRa, MQTT, Sensores)
- `[2]` 📖 **BRANDING** (Design Systems, Manuales, UI Luxury)
- `[3]` 🌳 **KUAMIKIACHI** (ONG, Arquitectura Web, Comunidad)
- `[4]` 🎨 **STITCH2ELEMENTOR** (Stitch a WordPress Elementor, MU-Plugins)
- `[5]` 🕸️ **ARQ_WEB_SCRAPING** (Playwright, Puppeteer, FlareSolverr, Anti-Bot)
- `[6]` 🛡️ **LINUX_PROXMOX** (Kernel Linux, PVE 8.x, CT114, CT106, ZFS, sysctl)
- `[7]` 🛡️ **MIKROTIK** (RouterOS v7, MAC Drift, FastTrack, Firewall)
- `[8]` ⚡ **FLOYDIA_SUITE_MASTER** (PyQt6, SRE Governor, Multi-Cuenta APIs)
- `[9]` 💼 **CLIENTES_Y_NEGOCIOS** (Evergreen 3.0, WattSaver, C_Crochet, Briefs)
- `[10]` 🛸 **AGENTS_HARNESS_ENGINEERING** (DeepSeek R1, Hermes, MCPs, Protocolo v27)
- `[11]` 🪄 **CREATIVE_WEB_AI_ANIMATIONS** (GSAP 3.12+, Three.js, Shaders, Luxury UI)

---

### ⚙️ Paso 2: Selecciona la Variante de Optimización:
1️⃣ 🔍 **Búsqueda y Adición de Fuentes Nuevas**
   ↳ Rastrea documentación oficial reciente y especificaciones técnicas para generar bloques listos para añadir.

2️⃣ 💬 **Enriquecimiento desde Conversaciones Anteriores (Transcripts & Journals)**
   ↳ Analiza `brain/` y `memory-bank/journal/` extrayendo soluciones validadas para actualizar el cuaderno.

3️⃣ 📑 **Generación de Informes y Resúmenes SSOT para Memory Bank**
   ↳ Sintetiza el conocimiento del cuaderno en notas estructuradas con `[[wikilinks]]`.

4️⃣ 🛡️ **Auditoría de Integridad, Salud & Cobertura**
   ↳ Ejecuta `python3 SCRIPTS/notebooklm_curator.py --health` auditando IDs, URLs y densidad de keywords.

5️⃣ 🚀 **Pipeline Completo (Full Suite Auto-Opti)**
   ↳ Ejecuta las variantes 1, 2, 3 y 4 de forma secuencial.

---
💡 *¿Cómo responder?*
- Responde con el número de cuaderno y la variante deseada (ej. `6 2`, `0 4`, `11 1`).
```

---

## 🔬 2. Mapa SSOT y Enrutamiento con `notebooklm_curator.py`

```bash
# Listar todos los cuadernos indexados
python3 SCRIPTS/notebooklm_curator.py --list

# Reporte de salud SRE y conteo de fuentes
python3 SCRIPTS/notebooklm_curator.py --health

# Enrutamiento semántico automático para una consulta o tarea
python3 SCRIPTS/notebooklm_curator.py "optimizar scrolltrigger gsap con lenis"

# Análisis multidominio cruzado (Cross-Query)
python3 SCRIPTS/notebooklm_curator.py --cross-query "despliegue elementor con tailwind y playwright"
```

---

## 🛠️ 3. Protocolos de Enriquecimiento

1. **Variante 1 (Nuevas Fuentes)**: Consultar lagunas y formatear fuentes markdown con URL, resumen y snippets listos para importar.
2. **Variante 2 (Journals y Transcripts)**: Extraer soluciones de `memory-bank/journal/` y generar nota `Hallazgo_[DOMINIO]_[FECHA].md`.
3. **Variante 3 (Síntesis)**: Crear notas en `memory-bank/proyectos/` o `technical/` con YAML frontmatter y `[[wikilinks]]`.
4. **Variante 4 (Auditoría)**: Validar coherencia de enlaces e IDs con `notebooklm_curator.py --health --json`.

---

## 🔌 4. Consulta vía MCP `notebooklm-mcp` (Alternativa al Browser)

Si el browser no está disponible, usar el MCP `notebooklm-mcp` configurado en `techContext.md`:
```bash
# Consulta directa al cuaderno via MCP (sin browser)
# El MCP notebooklm-mcp está registrado en ~/.gemini/config/mcp_config.json
# Permite queries semánticas sin necesidad de autenticación visual
```

> [!TIP]
> En agentes sin browser (OpenCode, Hermes), priorizar `notebooklm_curator.py` para enrutamiento local y el MCP para consultas directas.

---

## 🔄 5. Compatibilidad Multi-Agente

| Agente | Soporte | Notas |
|---|:---:|---|
| **Antigravity IDE** | ✅ Completo | Menú interactivo, browser para NotebookLM, MCP |
| **OpenCode CLI** | ✅ Parcial | Menú en texto, `notebooklm_curator.py` local, sin browser |
| **Hermes CLI** | ✅ Parcial | Menú en texto, `notebooklm_curator.py` local, sin browser |
| **Modo Degradado** | — | Usar `notebooklm_curator.py --health` para diagnóstico offline |
