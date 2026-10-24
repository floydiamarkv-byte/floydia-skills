---
name: f-master-update
description: "Super Suite SRE: actualización de OS, agentes, memoria y NotebookLM. Invocar con /f-master-update."
version: 1.0.1
triggers:
  - /f-master-update
  - /master-update
  - /f-update
  - /actualizar-todo
  - /super-update
  - master update
  - optimizar y actualizar
  - full sovereign sweep
  - suite de mantenimiento
  - sync git repos
  - auditoria git
  - actualizar repos
  - flatpak update
---

# Super Skill: Master Update & SRE Sovereign Governor (`f-master-update` v1.0)

> **Propósito**: Super suite canónica unificada del Ecosistema FloydIA bajo el **Protocolo v28**. Centraliza en un único punto de entrada con arquitectura **Menu-First en 2 niveles** las tres suites maestras:
> 1. **`f-update-floydia` v5.3**: Actualización determinista bare-metal (OS APT, Flatpaks, firmware, NPM agents, Memory Bank, catálogo semántico de imágenes, Graphify AST, CODEX_FLOYDIA y smoke tests).
> 2. **`f-opti-floydia` v4.1**: SRE Governor, sonda de telemetría, saneamiento de temporales, rescate anti-hang seguro, análisis de cuellos de botella y resiliencia de backups.
> 3. **`f-opti-notebooklm` v1.1**: Curación soberana, auditoría y enrutamiento de los 34 cuadernos de la base de verdad Google NotebookLM (SSOT: SCRIPTS/notebooklm_curator.py --list).

---

## 🧭 1. Arquitectura Unificada & Flujo de Ejecución

```mermaid
graph TD
    Trigger["Invocación (/f-master-update, /master-update, /f-update, /f-opti)"] --> M1["Menú Nivel 1 (Master Hub)"]

    M1 -->|Opción 1| Sweep["🚀 Full Sovereign Sweep (Fases A ➔ B ➔ C ➔ D)"]
    M1 -->|Opción 2| Daily["⚡ Optimización Rápida & Mantenimiento Diario"]
    M1 -->|Opción 3| SubUpd["🛰️ Submenú Especializado: Actualización (7 Fases)"]
    M1 -->|Opción 4| SubOpt["🔍 Submenú Especializado: Optimización & SRE (11 Opciones)"]
    M1 -->|Opción 5| SubNLM["🧠 Submenú Especializado: NotebookLM (34 Cuadernos / 5 Variantes)"]
    M1 -->|Opción 0| Exit["🚪 Salir"]

    subgraph "🚀 Pipeline Full Sovereign Sweep"
        Sweep --> FA["Fase A: SRE & Quick Wins (Telemetría + Saneamiento)"]
        FA --> FB["Fase B: Actualización Core (OS + Agentes + Memoria + Imágenes + Grafo + Codex)"]
        FB --> FC["Fase C: Ground Truth (Auditoría Salud NotebookLM)"]
        FC --> FD["Fase D: Paridad Multi-Agente (Symlinks OpenCode / DSH)"]
    end
```

---

## 🎯 2. Menú Interactivo Nivel 1 — Master Hub

Al invocar `/f-master-update`, `/master-update`, `/f-update`, `/f-opti`, `/actualizar-todo` o `/super-update`, el agente **DEBE responder de inmediato presentando este menú Bento interactivo**:

```markdown
╔════════════════════════════════════════════════════════════════════════════════╗
║             ⚡ F-MASTER-UPDATE — MASTER SRE & UPDATE HUB v1.0.0               ║
║                     Ecosistema FloydIA — Protocolo v28                         ║
╚════════════════════════════════════════════════════════════════════════════════╝

Selecciona una acción respondiendo con el número correspondiente:

1️⃣ 🚀 **Suite Completa Soberana (Full Sovereign Sweep)**
   ↳ Pipeline de 4 Fases Integradas:
     • Fase A: Telemetría SRE + Quick Wins seguras (purga zombies, temporales).
     • Fase B: Actualización OS (APT/Flatpak/NPM), Memory Bank, Catálogo Visual de Imágenes,
       Graphify AST y regeneración de CODEX_FLOYDIA.md.
     • Fase C: Auditoría de integridad de NotebookLM y sincronización automática del cuaderno de configuración (ENTORNO_HARNESS_MIKROTIK_Y_OBSIDIAN_SSOT).
     • Fase D: Sincronización multi-agente (`sync_skills_multiagent.sh --fix`).

2️⃣ ⚡ **Optimización Rápida & Mantenimiento Diario (Quick Wins)**
   ↳ Saneamiento seguro de temporales (`antigravity_speed_boost.sh`), purga de procesos
     huérfanos, compactación de memoria (`memory_compactor.py`) y comprobación rápida
     de paquetes actualizables sin reinicio.

3️⃣ 🛰️ **Submenú Especializado de Actualización (f-update-floydia v5.3)**
   ↳ Despliega las 7 fases granulares de actualización de sistema, imágenes y manifiestos.

4️⃣ 🔍 **Submenú Especializado de Optimización & SRE (f-opti-floydia v4.1)**
   ↳ Despliega las 11 opciones de auditoría hardware/red, prompts duales y rescate anti-hang.

5️⃣ 🧠 **Submenú Especializado de NotebookLM (f-opti-notebooklm v1.1)**
   ↳ Despliega el selector de los 34 cuadernos activos y las 5 variantes de curación.

6️⃣ 🐙 **Auditoría & Sincronización Git/GitHub de Proyectos Activos**
   ↳ Inspecciona el estado de los repositorios activos (FloydIA Suite, Floydia Skills,
     Stitch2Elementor, prompt-optimizer, etc.), detecta divergencias/dirty y sincroniza
     ramas remotas sin colisiones vía `SCRIPTS/sync_git_repos.sh`.

0️⃣ 🚪 **Salir**
```

---

## 📂 3. Submenús Especializados (Nivel 2)

### 🛰️ Submenú 3: Actualización & Disaster Recovery (`f-update-floydia`)
```markdown
╔═══════════════════════════════════════════════════════════════╗
║         🛰️ SUBMENÚ: ACTUALIZACIÓN & DISASTER RECOVERY         ║
╚═══════════════════════════════════════════════════════════════╝

1️⃣ **Actualización Completa (Full Pipeline Fases 0 a 7)**
   ↳ Preflight, OS/APT/Flatpak/NPM, Memoria, Catálogo Imágenes, Grafo AST, CODEX, Smoke Tests y Sync.
2️⃣ **Catálogo Visual & Metadatos Semánticos de Imágenes** 📸
   ↳ Ejecuta `index_workspace_images.py` en paralelo (dimensiones, DPI, ratios, ALT text y JSON).
3️⃣ **Compactación del Memory Bank & Auditoría Syncthing**
   ↳ Lock exclusivo `memory_compactor.py`, verificación de budget (≤400 tokens) y escaneo `.sync-conflict`.
4️⃣ **Auditoría de Sistema, Paquetes & Agentes IA (MX Linux / APT / Flatpak / DSH / OpenCode)**
   ↳ Detección con `apt list --upgradable`, paquetes globales NPM y firmware sin cambios destructivos.
5️⃣ **Reconstrucción del Grafo AST (Graphify) & Manifiesto CODEX**
   ↳ `graphify update .` y regeneración determinista de `CODEX_FLOYDIA.md`.
6️⃣ **Smoke Tests & Certificación Rápida**
   ↳ `dpkg --configure -a`, `dsh --dump-config`, latencia Graphify <10ms y consistencia.
7️⃣ **Sincronización Multi-Agente (OpenCode Desktop, DeepSeek Harness)**
   ↳ `sync_skills_multiagent.sh --fix` asegurando paridad del 100% en la trinidad agéntica.
8️⃣ **Auditoría & Status Git de Repositorios Activos** 🐙
   ↳ `SCRIPTS/sync_git_repos.sh --status` (o `--fetch` / `--sync`) auditando ramas y cambios locales.
0️⃣ **Volver al Menú Principal**
```

### 🔍 Submenú 4: Optimización & SRE Governor (`f-opti-floydia`)
```markdown
╔═══════════════════════════════════════════════════════════════╗
║         🔍 SUBMENÚ: OPTIMIZACIÓN & SRE GOVERNOR               ║
╚═══════════════════════════════════════════════════════════════╝

1️⃣ **Diagnóstico Completo del Ecosistema** (`ecosystem_probe.py`: CPU, RAM, ZRAM, CT114, CT106, MikroTik).
2️⃣ **Generar Prompts Duales para IA Web** (Prompt A Telemetría Sanitizada + Prompt B Plan de Acción SRE).
3️⃣ **Optimización Rápida (Quick Wins Seguras)** (Saneamiento de temporales y procesos huérfanos).
4️⃣ **Consultar Ground Truth** (`graphify_query.sh` por lotes + NotebookLM + Obsidian).
5️⃣ **Auditoría de Red, MikroTik & APIs de IA** (Latencias TCP CT114 :3000, CT106 :8384, DNS AI).
6️⃣ **Rescate de Emergencia Anti-Hang (< 1s)** (`kill_hung_agents.sh` con lista blanca estricta).
7️⃣ **Diagnóstico de Cuellos de Botella & Errores** (`bottleneck_analyzer.py`: dmesg, I/O wait, throttling, PSI).
8️⃣ **Auditoría de Agentes & Harness Engineering** (`agent_health_check.py`: paridad symlinks, MCPs, logs). Incluye `SCRIPTS/healthcheck_mcps.py` (semáforo MCP 4 entornos DSH/Antigravity/OpenCode/Hermes + toolchain web; evidencia JSON en `.session/`, exit≠0 si hay ❌).
9️⃣ **Mapa Mental / Infograma del Ecosistema** (Mermaid completo y prompt infograma premium).
🔟 **Escaneo de Prompts Históricos & Enriquecimiento** (Inventario `memory-bank/prompts/` CAT_01..08).
1️⃣1️⃣ **Resiliencia & Continuidad SRE** (Verificar manifest SHA256, log OK, crons y `guard_command.py`).
0️⃣ **Volver al Menú Principal**
```

### 🧠 Submenú 5: Base de Verdad NotebookLM (`f-opti-notebooklm`)

> **DELEGACIÓN, NO COPIA.** El menú, el catálogo de cuadernos y las variantes de
> curación viven **exclusivamente** en el skill `f-opti-notebooklm`. Este hub
> **no los replica**, por diseño: antes lo hacía y las cifras divergieron
> (decía 11 cuadernos cuando el SSOT devuelve 34).
>
> **SSOT del recuento**: `python3 SCRIPTS/notebooklm_curator.py --list`
> **No escribas un número de cuadernos aquí.** Léelo del script o delega.

Al elegir esta opción, el agente **DEBE** invocar el skill `f-opti-notebooklm`
y dejar que su menú sea el que se presente. Si el usuario pide la variante 4
(auditoría de salud) sin pasar por el menú, ejecutar directamente:

```bash
python3 SCRIPTS/notebooklm_curator.py --health
```

---

## 🛠️ 4. Matriz de Comandos CLI y Scripts Operativos

| Suite / Fase | Script / Comando SSOT | Modo de Ejecución |
|---|---|:---:|
| **SRE Telemetría** | `python3 FLOYDIA/PUBLIC_REPOS/floydia-skills/skills/f-opti-floydia/scripts/ecosystem_probe.py` | Read-Only |
| **Quick Wins** | `./SCRIPTS/antigravity_speed_boost.sh --apply --clean-tmp --kill-duplicates` | Saneamiento |
| **Rescate Anti-Hang** | `./SCRIPTS/kill_hung_agents.sh` | Emergencia (<1s) |
| **Cuellos de Botella** | `python3 FLOYDIA/PUBLIC_REPOS/floydia-skills/skills/f-opti-floydia/scripts/bottleneck_analyzer.py` | Read-Only |
| **Auditoría Agentes** | `python3 FLOYDIA/PUBLIC_REPOS/floydia-skills/skills/f-opti-floydia/scripts/agent_health_check.py` | Auditoría |
| **Actualización OS/APT** | `python3 SCRIPTS/update_floydia.py --system --dry-run` (`--yes` para aplicar) | Sistema |
| **Flatpak Sanitization** | `flatpak update -y --noninteractive && flatpak uninstall --unused -y` | Aislamiento AppImage |
| **Git Repos Status/Sync**| `bash SCRIPTS/sync_git_repos.sh --status` (`--fetch` / `--sync`) | Control Versiones |
| **Catálogo Imágenes** | `python3 SCRIPTS/update_floydia.py --images` | Multimodal |
| **Memory Compactor** | `python3 SCRIPTS/memory_compactor.py` (bajo lock exclusivo) | Memoria |
| **Graphify AST** | `graphify update .` | AST Grafo |
| **CODEX_FLOYDIA** | `python3 SCRIPTS/update_floydia.py --codex` | Manifiesto |
| **NotebookLM Salud** | `python3 SCRIPTS/notebooklm_curator.py --health` | Ground Truth |
| **Sync Multi-Agente** | `bash SCRIPTS/sync_skills_multiagent.sh --fix` | Paridad |
| **Full Sweep Dry-Run** | `python3 SCRIPTS/update_floydia.py --full --dry-run --verbose` | Simulación |

> **Nota de rutas (2026-09-30)**: `f-opti-floydia` **no** forma parte de las 7 skills canónicas
> desplegadas en `.agents/skills/` (ver `sync_skills_multiagent.sh`). Sus tres scripts SRE viven
> únicamente en el repo canónico `FLOYDIA/PUBLIC_REPOS/floydia-skills/skills/f-opti-floydia/scripts/`.
> Las rutas antiguas `.agents/skills/f-opti-floydia/scripts/*` fueron corregidas a esa ubicación.
> Si en el futuro se despliega la skill, verificar cuál de las dos rutas es válida antes de ejecutar.

---

## 🛡️ 5. Guardrails Inmutables & Protocolo v28

1. **Idioma Obligatorio (2026-08-20)**: Toda la interacción, menús, logs, advertencias y reportes DEBEN redactarse en **español**.
2. **P0 — Anti-Fuga de Secretos**: PROHIBIDO escribir credenciales o tokens de `/home/tec/.secrets/antigravity.env` en logs, reportes o prompts externos. Sustituir siempre por `[REDACTED]`.
3. **P3 — Prohibición de `sync` Global**: PROHIBIDO invocar `sync` en carpetas sincronizadas con Dropbox o Syncthing para evitar I/O stalls en Xorg/Electron.
4. **P4 — Lista Blanca Estricta Anti-Hang**: El script de rescate (`kill_hung_agents.sh`) NUNCA debe tocar Antigravity IDE, LSPs (`jedi`, `tsserver`), Syncthing ni demonios críticos de sistema.
5. **Non-Destructive por Defecto**: Comandos que modifiquen paquetes del sistema (`apt upgrade`, purgas) requieren autorización explícita o flag `--yes`.
6. **#vetado — Aislamiento HP45**: PROHIBIDA la sincronización o réplica desatendida hacia HP45 (`192.168.1.204`).
7. **P8 — Certificación con Artefacto**: Ningún backup ni verificación se da por válido sin citar el manifiesto `.sha256`, la línea `OK` en log y el heartbeat.
8. **P9 — Aislamiento de Entorno AppImage**: Toda ejecución de `flatpak` o llamadas a herramientas bare-metal debe purgar variables `LD_LIBRARY_PATH` contaminadas por AppImages (ej. `cockpit-tools`) para evitar fallos de resolución de símbolos (`libmalcontent-0.so.0`).
9. **P10 — Actualización Flatpak Dual**: Actualizar siempre a nivel de usuario (`flatpak update -y`) y a nivel de sistema (`sudo flatpak update -y`), saneando runtimes obsoletos con `flatpak uninstall --unused -y`.
10. **P11 — Sincronización Git No Destructiva**: En sincronización de repositorios (`sync_git_repos.sh`), únicamente aplicar `--ff-only` si el repositorio está en estado limpio (`clean`) y sin commits locales no pusheados. Nunca forzar sobrescrituras.

---

## 🔄 6. Compatibilidad Multi-Agente (Trinidad Canónica)

| Entorno / Agente | Estado | Mecanismo de Integración |
|---|:---:|---|
| **Antigravity IDE** | 🟢 Nativo | Lectura directa en `.agents/skills/f-master-update/SKILL.md` con menú interactivo |
| **OpenCode Desktop / CLI** | 🟢 Sincronizado | Symlink automático en `~/.opencode/skills/f-master-update` vía `sync_skills_multiagent.sh` |
| **DeepSeek Harness (`dsh`)** | 🟢 Sincronizado | Enlace SSOT en `~/.dsh/AGENTS.md` y verificación de perfiles Cordis Web |
| **Hermes / Qoder** | 🟡 CLI Directo | Ejecución de scripts en modo no interactivo vía CLI (`python3 SCRIPTS/...`) |
