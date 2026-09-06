---
name: f-audit-web
description: "Orquestador del protocolo 'Auditoría externa por copia y pega': tú eres los ojos y las manos de una IA externa potente que solo puede conversar en texto plano por una interfaz web (sin subir archivos ni markdown). Genera el Prompt Semilla, ejecuta rondas de reconocimiento (solo lectura), aplica parches con red de seguridad git y cierra sesión con journal. USAR cuando el usuario invoque /f-audit-web, /audit-web, 'MEJORA <proyecto>' con intención de delegar diagnóstico a una IA externa por chat web, o pegue instrucciones/parches provenientes de una IA externa. NO USAR para diagnóstico propio directo del código (ese es el trabajo de la IA externa, R5) ni para tareas triviales de una sola línea."
version: 1.0.0
triggers:
  - /f-audit-web
  - /audit-web
  - auditoria externa por copia y pega
  - audit web
  - MEJORA /f-audit-web
  - ojos y manos de la IA externa
---

# Skill: Auditoría Externa por Copia y Pega (`f-audit-web` v1.0)

> **Propósito**: Cuando el usuario quiere resolver un problema de un proyecto con ayuda de una IA externa potente a la que solo accede por chat web de texto plano (sin archivos, sin markdown), **tú eres sus ojos y sus manos**: generas el Prompt Semilla, ejecutas las instrucciones de reconocimiento, devuelves UN solo bloque pegable, aplicas los parches con red de seguridad git y cierras con journal.

> **Frase guía (literal, debe aparecer en el Prompt Semilla y en toda descripción del protocolo):** "Tú eres sus ojos y sus manos."

---

## 🎯 1. Interfaz y Despacho de Modos

Invocación: `/f-audit-web <objetivo en lenguaje natural> [flags]`

| Flag | Modo | Descripción |
|---|---|---|
| `--ia <nombre>` | (modificador) | Nombre de la IA externa (defecto: "IA externa"). Solo cambia el saludo del Prompt Semilla. |
| `--proyecto <ruta>` | (modificador) | Raíz del proyecto. Si se omite, inferirla y confirmarla en la 1ª línea de salida. |
| `--ronda` | ejecución | El usuario pega instrucciones de la IA externa; tú las ejecutas (solo lectura). Es el modo por defecto si existe sesión abierta y el texto parece instrucciones. |
| `--aplicar` | aplicación | El texto pegado contiene parches/diffs/código a aplicar (con red de seguridad git). |
| `--cerrar` | cierre | Resumen de sesión, commits, tests finales, journal. |
| `--reanudar` | retomar | Recupera la última sesión del proyecto y muestra su estado. |
| `--estado` | estado | Muestra la sesión activa sin ejecutar nada. |
| `--ronda1-local` | modo local | Emite la Ronda 1 genérica prefabricada (§7) sin esperar a la IA externa. |

**Resolución de sesión (slug)**: `slug = slugify(nombre-proyecto)`. Si existe `<proyecto>/.f-audit-web/session_<slug>.md`, la sesión está activa: cualquier texto pegado que parezca instrucciones se trata como `--ronda`; si parece parches (diffs/bloques de código con ruta), avisar y pedir confirmar como `--aplicar` (R1).

---

## 🗂️ 2. Persistencia de Sesión

- Archivo: `<proyecto>/.f-audit-web/session_<slug>.md`. Crear en el Arranque; actualizar tras cada ronda.
- Antes de crearlo, asegurar `.f-audit-web/` en el `.gitignore` del proyecto (añadir si no está).
- Plantilla:

```text
# Sesión f-audit-web — <slug>
- Objetivo: <texto del usuario>
- IA externa: <nombre>
- Ruta proyecto: <ruta absoluta>
- Inicio: <ISO8601>
- Rama git de trabajo: <audit-web/<slug>-<fecha> o "ninguna aún">
- Ronda actual: <N>

## Rondas
### Ronda N
- Pedido: <3 líneas máx>
- Reportado: <3 líneas máx>
- Aplicado: <3 líneas máx>
```

- Memoria larga vive SOLO aquí y en el journal de cierre; no contaminar `memory-bank/core/` (Protocolo v27: escritura exclusiva en journal).

---

## 🛡️ 3. Reglas Duras (R1–R8) — INNEGOCIABLES

**R1 SOLO LECTURA POR DEFECTO.** En rondas de reconocimiento NO modificas archivos ni ejecutas comandos que escriban, salvo el archivo de sesión. Si la IA externa pide algo que escribe y el usuario no invocó `--aplicar`: ejecútalo SOLO si es reversible y trivial (crear temporal en `/tmp`). Si toca el proyecto: detente y avisa en una línea: `REQUIERE --aplicar`.

**R2 REDACCIÓN DE SECRETOS.** Todo valor de API key, token, contraseña, cookie o cadena que parezca secreto se sustituye por `<REDACTED>` antes de salir por pantalla (incluye salidas de comandos y mensajes de error). Los NOMBRES de variables sí se muestran. Nunca pegues contenido de `.env` con valores.

**R3 UN SOLO BLOQUE.** Toda respuesta destinada a la IA externa es UN bloque de texto plano delimitado EXACTAMENTE así:

```text
==================== COPIAR DESDE AQUI ====================
...
==================== HASTA AQUI ====================
```

Dentro: prohibidas tablas markdown, prohibidos bloques con triple comilla, prohibido JSON suelto. Separadores: `===== SECCION N: TITULO =====`. Código en crudo precedido de `--- archivo.py L120-L180 ---`.

**R4 LITERALIDAD.** Código y salidas de comandos se pegan tal cual: sin resumir, sin corregir, sin reformatear. Si algo no existe o falla: `NO EXISTE` o `ERROR: <mensaje>` literal. Prohibido inventar o rellenar huecos con suposiciones. Si una instrucción es ambigua, ejecuta la interpretación más literal y anota la ambigüedad en la sección final.

**R5 CERO DIAGNÓSTICO PROPIO EN LAS RONDAS.** El diagnóstico lo hace la IA externa. Solo al final del bloque, `===== OBSERVACIONES DEL AGENTE =====` con máx. 10 líneas de HECHOS vistos al leer (duplicados, TODOs, excepciones silenciadas, inconsistencias de nombres) — nunca hipótesis.

**R6 PRESUPUESTO.** Cada bloque: ~700 líneas máx. Si una función pedida supera 150 líneas, pégala completa igualmente y recorta otras secciones antes que esa, indicando qué se recortó.

**R7 RED DE SEGURIDAD EN `--aplicar`.**
1. Antes del primer parche: `git status` limpio (si no, parar y avisar) y crear rama `audit-web/<slug>-<fecha>`.
2. Por cada ronda de aplicación: aplicar parches, ejecutar la suite de tests del proyecto (detectar: `run_tests.py`, `pytest`, `npm test`...), commit `audit-web(<slug>) ronda N: <resumen>`.
3. Reportar a la IA externa en un bloque: diff aplicado (resumen por archivo con +/-), salida literal de tests (redactada) y errores.
4. Si tests que antes pasaban ahora fallan: NO commitear; reportar y esperar.

**R8 CIERRE (`--cerrar`).** Resumen de sesión, lista de commits, tests finales, y entrada de journal en `memory-bank/journal/<YYYY-MM-DD>_<proyecto>_audit_web.md` (convención append-only, plantilla del hanodoff del workspace) incluyendo sección **"Lecciones aprendidas"** con lo que la IA externa detectó que los tests no cubrían. Preguntar al usuario si hace merge a la rama principal; NO hacerlo tú.

---

## 🌱 4. Prompt Semilla — Plantilla (paso b del bucle)

Generar dentro de los delimitadores COPIAR DESDE AQUI / HASTA AQUI, texto plano, español, ~40-60 líneas, en este orden:
1. Presentación del protocolo: quién es el usuario; la IA externa no tiene acceso a nada; existe un agente local que **"es sus ojos y sus manos"**; el canal es solo texto plano copiado y pegado.
2. Descripción del proyecto en máx. 8 líneas (leída de README, entrypoint, estructura; sin secretos).
3. El problema concreto (objetivo del usuario enriquecido con lo hallado en journals/commits recientes: últimos 8 commits, uno por línea).
4. Reglas del canal para la IA externa: pedir cosas concretas y ejecutables; indicar por petición si es lectura o escritura; no pedir secretos; asumir que recibirá un solo bloque de texto plano por ronda; pedir código con archivo y rango de líneas; separar siempre "reconocimiento" de "aplicación de parches".
5. Qué se espera: primero plan de diagnóstico en rondas; luego Ronda 1 de instrucciones de reconocimiento (solo lectura) formateada para ejecución literal. Cuando proponga parches: diff unificado o bloques completos con ruta y líneas, más el test que lo verifique.
6. Criterio de éxito para cerrar la sesión.
7. Cierre: "Responde con el plan y la Ronda 1."

---

## 🔄 5. El Bucle Operativo

a) Usuario: `MEJORA <proyecto> /f-audit-web <problema>` → generar Prompt Semilla (§4) + crear sesión (§2).
b) Usuario lo pega en la IA externa y te devuelve la respuesta (instrucciones).
c) Modo `--ronda` (o por defecto con sesión abierta): ejecutar con R1/R2/R4/R5 y devolver UN bloque (R3, R6).
d) Repetir c). Si llegan parches → modo `--aplicar` (R7).
e) Al resolver: `--cerrar` (R8).

### Plantilla del bloque de salida de una ronda

```text
==================== COPIAR DESDE AQUI ====================
===== RONDA N — RESULTADOS DE RECONOCIMIENTO =====
===== SECCION 1: <titulo de la instruccion 1> =====
<salias literal>
--- ruta/archivo.py L1-L80 ---
<codigo en crudo>
===== SECCION 2: <titulo de la instruccion 2> =====
NO EXISTE | ERROR: <mensaje literal>
===== RECORTES APLICADOS (SI HUBO) =====
<que se recorto y por que>
===== OBSERVACIONES DEL AGENTE =====
<max 10 lineas, solo hechos, sin hipotesis>
==================== HASTA AQUI ====================
```

---

## 🧰 6. Ronda 1 Genérica Prefabricada (`--ronda1-local`)

Texto plano parametrizado con `<PROYECTO>`, `<MODULO_CRITICO>`, `<FUNCIONES>`:

```text
===== RONDA 1 — RECONOCIMIENTO GENERICO (SOLO LECTURA) =====
1) PROCESO REAL: listar con ps aux los procesos vivos de <PROYECTO>; localizar lanzadores (scripts .sh, .desktop, aliases) y detectar copias duplicadas del proyecto (find por nombre de directorio raiz) comparando md5sum de <MODULO_CRITICO>.
2) ENTORNO: mostrar NOMBRES (no valores) de variables de entorno del .env de <PROYECTO> vs los presentes en una shell nueva (env | cut -d= -f1 | sort). Redactar cualquier valor.
3) CONSUMIDORES EXTERNOS: estado real de los archivos/servicios que <PROYECTO> escribe (existencia, fecha, tamano, proceso que los consume).
4) SINTOMA: reproducir el problema con 3 casos concretos y pegar las salidas literales (stdout/stderr, exit code).
5) CODIGO CRITICO: pegar completo el archivo <MODULO_CRITICO> con numeros de linea, y las funciones <FUNCIONES> con su contexto (+-10 lineas).
```

---

## 🔄 7. Compatibilidad Multi-Agente

| Agente | Soporte | Notas |
|---|:---:|---|
| **Antigravity IDE** | ✅ Completo | Lectura/escritura de sesión, git, ejecución de tests |
| **OpenCode CLI** | ✅ Completo | Idem, bloques en texto plano |
| **Hermes CLI** | ✅ Completo | Idem |
| **Modo Degradado** | — | Sin git: `--aplicar` bloqueado hasta restaurar red de seguridad |

> [!CAUTION]
> Esta skill NO diagnostica por sí misma (R5). Si el usuario quiere diagnóstico local sin IA externa, enrutar a `f-harness-workflow` o `f-opti-floydia`.
