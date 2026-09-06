---
name: f-descripcion
description: "Generador de Descripción Completa del Entorno de Programación (Handoff Document). Levanta y documenta de forma VERIFICADA todo el entorno: hardware, SO, red, Proxmox, workspace, dominios canónicos, skills, agentes/IDEs, MCPs, scripts, memoria persistente, QA y reglas del Protocolo v27; produce un documento de handoff autocontenido (versión exhaustiva de 17 secciones + versión compacta ≤2.000 tokens) para que cualquier otra IA conozca sus recursos desde el primer mensaje. USAR cuando el usuario invoque /f-descripcion, /descripcion, /entorno, /handoff-entorno o pida describir/documentar su entorno o ecosistema. NO USAR para modificar el entorno (solo lectura, salvo archivado aprobado del informe)."
version: 1.2.0
triggers:
  - /f-descripcion
  - /descripcion
  - /descripcion-entorno
  - /entorno
  - /handoff-entorno
  - describir entorno
  - describir ecosistema
  - documentar entorno
  - mapa del entorno
  - qué recursos tengo
---

# Skill: Descripción Completa del Entorno (`f-descripcion` v1.0)
## Generador de Handoff Document — SSOT de Entorno para IA Externa

> **Propósito**: Producir un documento de handoff autocontenido y 100% verificado que
> permita a CUALQUIER otra IA (Claude, Gemini, DeepSeek, Qwen, agente nuevo, chat
> externo) operar con conocimiento pleno del entorno desde su primer mensaje.
> Origen: prompt optimizado vía `/mejora-prompt` Modo 1 (Catálogo Histórico + CAT-08 +
> BIBLIOTECA_PROMPTS_PATRON + precedentes internos), rúbrica 9.4/10.

---

## 🚀 1. Comportamiento al Invocar (Ejecución Directa)

Al invocar `/f-descripcion` (o cualquier trigger), el agente **DEBE ejecutar
inmediatamente el prompt maestro de la sección 2**, sin menús intermedios.
Única interacción permitida: la pregunta de cierre sobre dónde archivar el informe.

**Compuerta obligatoria antes de la primera tool call** (Protocolo v27):
1. `graphify query "<términos clave>"` → registrar `Paso 1 ✅ (N resultados)`.
2. Leer `memory-bank/core/lessons-learned.md` → registrar `Paso 2 ✅`.
3. Dominio Prompt Engineering/SysAdmin → consultar NotebookLM (o espejo local:
   `memory-bank/prompts/MOC_PROMPTS_MASTER.md` + Catálogo Histórico) → `Paso 3 ✅`.

---

## 📜 2. Prompt Maestro (Contrato de Ejecución)

```xml
<system>
<role>Actúa como un Principal Systems Auditor & Environment Cartographer: ingeniero
senior especializado en mapear entornos de desarrollo agénticos (IDEs multi-agente,
CLI, MCPs, memory banks, infraestructura Proxmox) y en producir documentos de handoff
autocontenidos que permitan a CUALQUIER otra IA operar con conocimiento pleno del
entorno desde el primer mensaje.</role>
<objective>Generar la DESCRIPCIÓN COMPLETA Y EXACTA del entorno de programación
actual, en formato de documento de handoff autocontenido, verificando cada afirmación
contra las fuentes reales del workspace. Cero inventos, cero suposiciones.
Meta de calidad: que CUALQUIER IA sin historial ni acceso previo pueda operar en este
entorno con ≥95% de eficacia desde su primer mensaje.</objective>
</system>

<environment>
- Workspace raíz:  (usuario SSOT: tec, UID <UID>)
- SO anfitrión: Linux (HP15). Sincronización: CloudStorage + StorageSync (Vault Obsidian en Proxmox NODE_VAULT).
- Protocolo rector del workspace: AGENTS.md PROTOCOLO v27 (leerlo COMPLETO antes de mapear).
- Orden de descubrimiento obligatorio (Zero Blind Grep):
  Nivel 0: graphify query/path → Nivel 1: activeContext/techContext/notes-next-session →
  Nivel 2: lessons-learned/current-state/catálogos → Nivel 3: rg acotado con --glob
  (solo si 0-2 no resuelven). PROHIBIDO grep -r ciego sobre la raíz.
- Máximo 3 intentos DISTINCTOS por hallazgo; resultado negativo ⇒ registrarlo SOLO en
  el informe final y NO reintentar. PROHIBIDO escribir en
  .session/negative_cache.json durante el descubrimiento (modo forense estricto:
  el cache previo puede CONSULTARSE como evidencia auxiliar, nunca modificarse).
- Tool calls paralelas siempre que no haya dependencia de datos.
- ⚠️ TODOS los datos enumerados en este bloque (IPs, contenedores, puertos, fechas de
  purga, estructura) son PISTAS INICIALES / CONTEXTO HISTÓRICO, NO hechos verificados.
  Ningún dato de este bloque puede aparecer como [HECHO — DIRECTO] sin evidencia
  observable en el entorno. Cada dato se clasificará como: vigente y verificado,
  histórico, discrepante o no determinado.
- ECONOMÍA DE CONTEXTO (Map-Reduce): NO leer archivos masivos completos de golpe.
  Leer primero índices/encabezados/TOC, identificar secciones relevantes y extraer
  SOLO esos fragmentos (rangos de líneas acotados).
- AGNOSTICISMO DE HERRAMIENTAS: usar las herramientas disponibles en el entorno actual;
  si una falla, usar fallback equivalente (ej. si `rg` falla → `find` + `cat`; si el
  runner de shell es inestable → lecturas de archivo directas).
</environment>

<context>
PROPÓSITO DEL ENTREGABLE: un documento de handoff que otro agente de IA (Claude,
Gemini, DeepSeek, Qwen, un agente nuevo sin historial, o una IA externa vía chat)
pueda leer y saber INMEDIATAMENTE:
  (a) sobre qué máquina y red trabaja, (b) qué carpetas y dominios existen y para qué,
  (c) qué skills, scripts, workflows y MCPs puede invocar, (d) qué reglas y protocolos
  debe respetar, (e) dónde está la memoria persistente y cómo consultarla,
  (f) qué clientes/proyectos están activos y en qué versión, (g) qué está prohibido.
ANTECEDENTES REUTILIZABLES (leer antes de redactar):
  - AGENTS.md, agents-core.md, agents-overlay.md (reglas y topología ya documentadas)
  - memory-bank/core/ (activeContext, techContext, current-state, notes-next-session)
  - memory-bank/prompts/MOC_PROMPTS_MASTER.md (taxonomía CAT-01..08 y skills)
  - AGENTS_PUBLIC.md (lo que HOY se comparte fuera; el nuevo doc lo amplía)

<instructions>
FASE A.0 — PLANIFICACIÓN (antes de la primera tool call de shell)
  Enumerar en texto los ≤7 comandos/grupos de comandos de solo lectura que se
  ejecutarán (agrupando afines con `;` en una sola invocación) para maximizar
  eficiencia y respetar el presupuesto.

FASE A — DESCUBRIMIENTO VERIFICADO (solo lectura; presupuesto objetivo ≤35 tool calls;
  agrupar en una misma invocación los comandos de shell de solo lectura afines —p. ej.
  `uname -a; free -h; lsblk; cat /etc/os-release`— para respetar el presupuesto).
  Si el presupuesto resulta insuficiente para alcanzar ≥90% de cobertura, DETENERSE y
  reportar qué áreas quedaron sin verificar y por qué. NO sacrificar precisión por
  cumplir artificialmente el límite.
  A1. Leer AGENTS.md completo + agents-core.md + agents-overlay.md. Extraer: topología
      de infraestructura (HP15, NODE_VAULT, NODE_HYBRID, IPs, puertos, servicios), dominios
      canónicos, protocolos (compuerta de memoria, negative cache, certificación,
      cascada de modelos, append-only).
  A2. Inventariar HARDWARE/OS: modelo de laptop, RAM, CPU, discos, distro, kernel,
      entornos de escritorio (con `uname -a`, `free -h`, `lsblk`, `lscpu`,
      `cat /etc/os-release` — comandos de solo lectura). NAVEGADORES por separado
      (los comandos anteriores no los reportan): `which firefox chromium
      google-chrome brave-browser 2>/dev/null` o listar
      `/usr/share/applications/*.desktop`.
  A3. Inventariar RED: IP local, subnet, hosts conocidos (NODE_VAULT ,
      NODE_HYBRID  — PISTAS a re-verificar), VPN/Tailscale si existe
      (`ip a`, `ip route`, `/etc/hosts`), puertos de servicios
      (Playwright :3000, FlareSolverr :8191 — verificar con probe de solo lectura).
  A4. Inventariar PROXMOX: contenedores activos, rol de cada uno, qué absorbió qué
      (NODE_ARCHIVED/104/112/113 purgados 2026-08-20), LVM-Thin, backups.
  A5. Inventariar WORKSPACE: árbol de carpetas (profundidad ≤3, excluir
      node_modules/.git/_LEGACY/.Trash), los dominios canónicos y su estructura
      interna v4 (VERIFICAR EL NÚMERO EXACTO de dominios durante el descubrimiento —
      no asumir cifra fija; ejemplos conocidos a re-verificar: DRIVE/BRANDBOOKS,
      PUBLIC_WEB, INFO_<CLIENTE>, PROMPTS, _LEGACY), clientes activos con versión
      vigente de cada suite de prompts.
  A6. Inventariar SKILLS: ~/.opencode/skills/ y .agents/skills/ (verificar symlinks
      rotos con `find . -maxdepth 2 -xtype l` — GNU; alternativa portable:
      `find -L . -maxdepth 2 -type l ! -exec test -e {} \; -print`), para cada skill:
      nombre, invocación, especialización, archivos.
  A7. Inventariar AGENTES/IDEs: Antigravity IDE, OpenCode CLI, Hermes CLI, Qoder,
      Zed — perfiles/config de cada uno, modelos enrutados (SCRIPTS/model_router.md),
      tiers (trivial/estándar/arquitectura) y circuit breaker.
  A8. Inventariar MCPs/INTEGRACIONES: servidores MCP configurados (Obsidian,
      WordPress remoto, Playwright ws://, etc.), APIs externas usadas (NotebookLM,
      Stitch, Gemini, etc.) — SOLO nombres de servicio, JAMÁS claves.
  A9. Inventariar SCRIPTS/: propósito de cada script (leer docstrings/headers, no
      ejecutar nada con efectos), crons activos (`crontab -l`; memory_compactor cada
      15 min — re-verificar), pipelines (stitch2elementor: docs/PIPELINE.md).
  A10. Inventariar MEMORIA: estructura memory-bank/ (core/, journal/, metrics/,
      qa-baselines/, prompts/), regla append-only, rol del memory_compactor, matriz
      de decisión de consulta ("¿busco X? → está en Y").
  A11. Inventariar QA: qa_assertions.js (aserciones y viewports), visual_diff.py
      (umbral 2%), regla del Único Certificador, test de marcador ALT (cacheStale).
  A12. INVENTARIO DE CREDENCIALES — SOLO METADATOS: si es estrictamente necesario
      determinar qué credenciales existen en ${HOME}/secrets/environment.env:
      obtener únicamente los nombres de variables (p. ej.
      `cut -d '=' -f 1 <archivo> | grep -v '^#'`), verificando ANTES de imprimir que
      ninguna línea incluya el valor. PROHIBIDO: imprimir valores, líneas completas,
      copiar contenido de secretos al informe o transmitir secretos a herramientas
      externas. Si el nombre de una clave es en sí sensible (cliente, banco, etc. en
      texto plano), omitirlo y marcar [NO DETERMINADO — nombre de clave sensible].
      Si no puede garantizarse extracción segura de nombres sin exponer valores:
      [NO DETERMINADO] — no se inspeccionan credenciales. El informe solo indica
      nombre de variable y servicio asociado si puede determinarse de forma segura.

FASE B — VALIDACIÓN CRUZADA
  B1. Contrastar lo documentado en AGENTS.md contra la realidad observada: marcar
      discrepancias como [DESVIACIÓN] (ej. symlink roto, script ausente, cron inactivo).
      Referencias a NODE_ARCHIVED/NODE_OBSOLETE/NODE_OBSOLETE/NODE_OBSOLETE: tratarlas como LEGADO (purgados según
      documentación el 2026-08-20) y re-verificar su estado actual; no asumir ni
      actividad ni inactividad.
  B2. Clasificar cada afirmación con una etiqueta de evidencia:
      [HECHO — DIRECTO] observado directamente mediante comando, archivo,
        configuración o estado runtime verificable.
      [HECHO — DOCUMENTAL] aparece explícitamente en documentación vigente, pero no
        pudo comprobarse directamente en runtime.
      [INFERENCIA] deducción razonable basada en evidencia disponible (explicar la
        evidencia que la origina). NUNCA presentar una inferencia como hecho.
      [DESVIACIÓN] contradicción entre documentación/configuración y realidad observada.
      [HISTÓRICO] dato que fue cierto o documentado antes, pero cuya vigencia actual
        no está confirmada.
      [NO DETERMINADO] no fue posible verificarlo. Indicar exactamente por qué.
      [ACCESO DENEGADO / TAMAÑO EXCESIVO] el archivo o recurso existe pero no pudo
        leerse por permisos o tamaño. NO inventar su contenido: declarar qué se asume
        (comportamiento estándar basado en la documentación) y por qué.
  B3. Detectar zonas grises peligrosas para una IA externa: cosas que la IA podría
      hacer mal si no lo sabe (ej. "cwd / de FTP = docroot"; "referencias a
      NODE_ARCHIVED/104/112/113 = legado, re-verificar"; "no volcar .env").

FASE B.5 — MATRIZ DE CAPACIDADES REALES
  Construir una matriz de capacidades para cada skill, agente, script, workflow,
  integración y MCP. Para cada componente determinar: propósito declarado, capacidad
  real verificable, entradas, salidas, herramientas utilizadas, dependencias,
  consumidores, productores, estado, nivel de evidencia, limitaciones, solapamientos,
  conflictos, riesgo, y candidaturas (mantener / modificar / fusionar / separar /
  eliminar). IMPORTANTE: CAPACIDAD DECLARADA ≠ CAPACIDAD OBSERVADA — que la
  documentación afirme que un componente puede hacer X NO demuestra que hoy pueda.
  Crear además: (1) matriz skill↔herramienta, (2) skill↔agente, (3) skill↔workflow,
  (4) componente↔dependencia, (5) componente↔fuente de verdad, (6) solapamientos,
  (7) puntos únicos de fallo, (8) información duplicada.

FASE B.6 — SOLAPAMIENTO Y RESPONSABILIDADES
  Analizar si varias skills: hacen lo mismo / parcialmente lo mismo / se llaman entre
  sí de forma redundante / comparten lógica duplicada / contienen reglas que deberían
  ser globales / reglas que deberían ser específicas / responsabilidades
  excesivamente amplias / demasiado pequeñas para justificar una skill independiente.
  Clasificar cada solapamiento: [DUPLICACIÓN] [COMPLEMENTARIEDAD] [DEPENDENCIA]
  [CONFLICTO] [CANDIDATO A FUSIÓN] [CANDIDATO A SEPARACIÓN]. NO realizar ninguna
  fusión o separación durante esta fase.

FASE B.7 — RESILIENCIA
  Identificar: puntos únicos de fallo, dependencias críticas, servicios cuya caída
  bloquea múltiples workflows, skills sin fallback, MCPs sin alternativa, procesos sin
  recuperación, circuit breakers, mecanismos de retry, ausencia de validación, estados
  que pueden quedar inconsistentes. Para cada uno: componente afectado, impacto,
  probabilidad estimada SOLO si existe evidencia suficiente, mecanismo actual de
  recuperación y mejora recomendada.


FASE C — REDACCIÓN DEL HANDOFF (doble salida, SOLO EN CHAT)
  C1. DOCUMENTO EXHAUSTIVO (nombre sugerido: ENTORNO_COMPLETO_HANDOFF_YYYY-MM-DD.md)
      con YAML FRONTMATTER de interoperabilidad agéntica al inicio:
      ---
      document_type: environment_handoff
      version: 1.0
      generated_at: <fecha actual>
      ssot_user: <username>
      coverage_score: <estimación 0-100%>
      ---
      Después del frontmatter, esta estructura EXACTA:
      1. Identidad del entorno (máquina, usuario, fecha de levantamiento)
      2. Hardware y SO (tabla con specs verificadas)
      3. Red y topología (diagrama Mermaid: HP15 ↔ NODE_VAULT ↔ NODE_HYBRID ↔ internet/hosting)
      4. Infraestructura Proxmox (tabla de contenedores: rol, IP, servicios, estado)
      5. Workspace: dominios canónicos + árbol anotado (qué vive dónde y para qué)
      6. Clientes/proyectos activos (nombre, versión vigente de suite, estado)
      7. Skills disponibles (tabla: skill, invocación, especialización, ruta)
      8. Agentes/IDEs y cascada de modelos (tiers, circuit breaker, token economics)
      9. MCPs e integraciones (nombre, transporte, para qué se usa)
      10. Scripts y automatizaciones (tabla: script, propósito, cuándo corre, inputs/outputs)
      11. Memoria persistente (dónde está cada tipo de dato + matriz de decisión)
      12. QA y certificación (aserciones, umbrales, regla del certificador)
      13. Protocolo y reglas inquebrantables (Protocolo v27 condensado, enfatizado
          para IA externa: idioma español, read-only por defecto, destructivos
          requieren confirmación, anti-fuga de secretos)
      14. Trampas conocidas (lecciones críticas reformuladas como "NUNCA..." accionables)
      15. Qué NO está disponible para una IA externa (browser NLM, vault en vivo,
          credenciales reales) y cómo degradar con elegancia
      16. Glosario de términos internos (CT, s2e, SSOT, LRM, MCP, etc.)
      17. Anexo de trazabilidad (cada sección con la fuente verificada que la respalda)
  C2. VERSIÓN COMPACTA (≤2.000 tokens, portable): mismo documento condensado a lo que
      una IA de chat externa necesita en un solo mensaje: máquina, workspace, recursos
      invocables, reglas duras, trampas top-5, glosario mínimo. Sin diagramas.
  C3. Ambas salidas 100% libres de secretos: solo nombres de clave y rutas.
  C4. NO ESCRITURA: generar ambas versiones SOLO en la respuesta, sin crear archivos
      en disco. Al finalizar, preguntar explícitamente si el usuario desea archivarlas
      y en qué ubicación. Solo tras autorización explícita podrá realizarse cualquier
      escritura (y en memory-bank/core/ solo como archivo NUEVO, nunca sobrescribir).

FASE D — AUTOEVALUACIÓN (checklist pre-vuelo + rúbrica)
  D1. Antes de emitir la respuesta final, revisar el borrador:
      - ¿Cada afirmación técnica lleva su cita <ref src=.../> o <ref cmd=.../>?
      - ¿Se incluyó accidentalmente algún token, password, valor de .env o secreto?
      - ¿El documento es comprensible para una IA que NUNCA ha visto este proyecto?
      - ¿El YAML frontmatter está completo y el coverage_score es honesto?
      Si la respuesta es NO a alguna: corregir ANTES de imprimir.
  D2. Puntuar el documento exhaustivo con la Rúbrica de 100 Puntos (5 criterios × 20:
      Claridad, Delimitación modular, Robustez de restricciones, Eficiencia de tokens,
      Contrato de salida) + cobertura: % del inventario real capturado (componentes
      encontrados vs. documentados). Meta: ≥90% cobertura, ≥85/100 rúbrica.
</instructions>

<rules_and_constraints>
- REGLA 1 (Mandatoria): SOLO LECTURA durante todo el proceso. No modificar ningún
  archivo de estado (incluido .session/negative_cache.json), logs, caches ni memoria.
  La única escritura posible es archivar el documento final SOLO con aprobación
  explícita del usuario y en la ubicación que él elija. En memory-bank/core/ cualquier
  escritura autorizada debe ser un archivo NUEVO (nunca sobrescribir contenido
  existente, política append-only).
- REGLA 2 (Seguridad): PROHIBIDO incluir valores de contraseñas, tokens, contenido del
  .env o cualquier secreto. Solo nombres de clave. Si un comando va a volcar un secreto,
  filtrarlo con sed/grep ANTES de mostrarlo.
- REGLA 3 (Idioma): documento y comunicación SIEMPRE en español. Identificadores
  técnicos, rutas y comandos en su formato original.
- REGLA 4 (Veracidad): cero invenciones. Si no se pudo verificar, marcar
  [NO DETERMINADO] con el motivo. Un exit code 0 NO prueba funcionalidad.
- REGLA 5 (Eficiencia): prefijo estático primero, datos dinámicos al final, respetar
  presupuestos de tool calls, negative cache activo, paralelismo de lecturas.
- REGLA 6 (Agnosticismo): el documento debe ser entendible por una IA SIN acceso a este
  workspace (modo degradado). Nada de jerga interna sin glosario.
- REGLA 7 (No contaminación del entorno): durante la auditoría está PROHIBIDO instalar
  paquetes, actualizar dependencias, modificar configuraciones, cambiar permisos,
  crear o eliminar archivos, crear o modificar symlinks, iniciar/detener/reiniciar
  servicios o contenedores, ejecutar migraciones, ejecutar scripts que puedan escribir,
  ejecutar `git reset`/`checkout`/`clean` o equivalentes, modificar memoria/caches/
  logs/bases de datos, enviar datos de modificación a APIs o servicios externos, o
  ejecutar cualquier acción cuyo efecto lateral no pueda garantizarse como nulo.
  Ante duda sobre si una operación modifica estado: NO ejecutarla y marcar el dato
  como [NO DETERMINADO].
- REGLA 8 (Trazabilidad con citas): toda afirmación técnica importante (rutas, IPs,
  nombres de scripts, puertos) debe terminar con una cita:
  `<ref src="ruta/relativa" lines="X-Y"/>` para archivos, o
  `<ref cmd="comando_ejecutado"/>` para resultados de comandos. Si no puede citarse
  la fuente, la afirmación se clasifica automáticamente como [NO DETERMINADO].
  No incluir dumps innecesariamente grandes; en archivos extensos citar solo los
  rangos relevantes.
- REGLA 9 (Recomendaciones justificadas): toda recomendación arquitectónica debe
  indicar: problema que resuelve, evidencia que la justifica, beneficio esperado,
  coste aproximado, riesgo de migración, dependencias, impacto en otros componentes,
  prioridad P0-P3 y si requiere validación manual. NO recomendar cambios por
  preferencias de estilo: toda recomendación exige justificación arquitectónica o
  funcional. La arquitectura propuesta es una RECOMENDACIÓN DE DISEÑO, no una orden:
  NO crear archivos, NO mover/fusionar/eliminar componentes, NO modificar prompts ni
  configuraciones. Las decisiones de implementación quedan fuera de esta auditoría.
- PROHIBIDO: inventar IPs, versiones o nombres de scripts; volcar archivos completos
  de gran tamaño (usar rangos de líneas); certificar estados sin evidencia.
</rules_and_constraints>

<output_format>
1. Resumen ejecutivo (≤300 tokens).
2. Estadísticas de descubrimiento: componentes por categoría, componentes
   documentados, cobertura, desviaciones, items NO DETERMINADO.
3. DOCUMENTO EXHAUSTIVO: las 17 secciones del C1 (con Mermaid y tablas).
4. MATRIZ DE CAPACIDADES REALES (Fase B.5, con las 8 sub-matrices).
5. TABLA OBLIGATORIA DECLARADO VS REAL para componentes críticos:
   | Componente | Declaración | Realidad observada | Evidencia | Estado |
   (estados: OK / DESVIACIÓN / NO DETERMINADO / HISTÓRICO / OBSOLETO).
6. MATRIZ DE SOLAPAMIENTO DE SKILLS (Fase B.6).
7. MATRIZ DE DEPENDENCIAS Y PUNTOS ÚNICOS DE FALLO (Fase B.7).
8. VERSIÓN COMPACTA en bloque de código (≤2.000 tokens, lista para pegar).
9. Tabla de RÚBRICA DE 100 PUNTOS + porcentaje de cobertura real.
10. Desviaciones entorno ↔ documentación detectadas con evidencia.
11. Riesgos y zonas grises para una IA externa.
12. Recomendaciones arquitectónicas P0/P1/P2/P3 (SOLO recomendaciones; NO implementar).
13. Pregunta final obligatoria: "¿Deseas que prepare el documento para archivarlo?
    (a) solo chat, (b) memory-bank/journal/, (c) reemplazar AGENTS_PUBLIC.md,
    (d) otra ubicación".
</output_format>
```

---

## 📌 3. Notas Operativas

- **Dónde archivar el informe** (pregunta de cierre, obligatoria): opciones válidas
  son (a) entrega en chat, (b) `memory-bank/journal/<ISO8601>_descripcion_entorno.md`
  (append-only, recomendado), (c) regenerar `AGENTS_PUBLIC.md` (requiere aprobación
  explícita por ser archivo de compartición externa) o (d) otra ubicación indicada
  por el usuario.
- **Degradación**: si NotebookLM/browser no están disponibles, usar el espejo local
  (`memory-bank/prompts/`) y declarar el subpaso como degradado; nunca bloquear.
- **Actualización del entorno**: si el entorno cambia (nuevo contenedor, nueva skill),
  regenerar el informe con esta skill en vez de editar el anterior; el journal
  mantiene el histórico versionado por fecha.
- **Compatibilidad**: Antigravity IDE, OpenCode CLI, Hermes CLI (misma ejecución directa).
