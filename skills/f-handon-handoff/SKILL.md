---
name: f-handon-handoff
description: "Continuidad agéntica, cierre de sesión y traspaso de memoria. Invocar con /f-handon o /f-handoff."
version: 2.0.0
triggers:
  - /f-handoff
  - /f-handon
  - /f-handon-handoff
  - handoff!!
  - /handoff
  - handoff
  - handon!!
  - /handon
  - handon
  - continuar sesion
  - cerrar sesion
---

# Skill: Protocolo de Continuidad Agéntica (`f-handon-handoff` v2.0)
## Traspaso Determinista de Sesión & Cero Pérdida de Contexto

> **Propósito**: Garantizar un puente determinista entre sesiones de trabajo independientes en Antigravity IDE, Obsidian Memory Bank y terminales del workspace, evitando la degradación de contexto y asegurando memoria append-only.

---

## 🎯 1. Menú Interactivo Menu-First

Al invocar `/f-handon-handoff`, `/f-handon` o `/f-handoff` sin parámetros, el agente **DEBE responder presentando este menú interactivo**:

```markdown
╔═══════════════════════════════════════════════════════════════╗
║     🔄 F-HANDON-HANDOFF — CONTINUIDAD AGÉNTICA FLOYDIA        ║
╚═══════════════════════════════════════════════════════════════╝

Selecciona una acción respondiendo con el **número** correspondiente:

1️⃣ **Cerrar Sesión & Generar Handoff (`handoff!!`)**
   ↳ Audita archivos modificados, estado de servidores locales y escribe el informe inmutable en `memory-bank/journal/` con el prompt de reanudación.

2️⃣ **Reanudar Sesión & Cargar Contexto (`handon!!`)**
   ↳ Localiza el handoff más reciente, sincroniza el estado de servidores y presenta el briefing estructurado de arranque.

3️⃣ **Consultar Notas de la Siguiente Sesión**
   ↳ Muestra el contenido resumido de `memory-bank/core/notes-next-session.md`.

4️⃣ **Auditar Estado de Servidores & Procesos Locales**
   ↳ Comprueba puertos activos (Vite, WordPress, Playwright CT114 :3000, Syncthing :8384).

0️⃣ **Salir**
```

---

## 🛑 2. Protocolo de Salida: `handoff!!` o `/handoff`

Al recibir **`handoff!!`**, **`/handoff`** o la opción `1`, el agente **DEBE** ejecutar:

### 1. Auditoría del Estado
- Identificar el cliente o dominio activo (`CLIENTES/*`, `FLOYDIA/*`, etc.).
- Listar archivos modificados/creados y estado de servidores locales.
- **Detección automática de servidores activos** (ejecutar en background):
  ```bash
  lsof -i -P -n 2>/dev/null | grep LISTEN | grep -E ':(3000|3001|4321|5173|8000|8080|8384|8191)' | awk '{print $1, $9}'
  ```
- Registrar tareas pendientes y bloqueos.

### 2. Generación del Archivo de Handoff Inmutable
Escribir exclusivamente en:
📁 `memory-bank/journal/<YYYY-MM-DD>_<cliente_o_proyecto>_handoff.md`

```markdown
# Handoff: Estado de Cierre de Sesión — [Proyecto / Cliente]

- **Fecha:** [YYYY-MM-DD]
- **Cliente / Proyecto:** [Nombre]
- **Estado General:** [Resumen de 1 línea]
- **Servidor / Procesos Activos:** [IP:Puerto / PID / None]

---

## 1. Trabajo Completado y Verificado
[Lista numerada de hitos completados, archivos modificados y pruebas realizadas]

## 2. Decisiones Técnicas y de Diseño
[Decisiones clave acordadas con el usuario]

## 3. Puntos Prioritarios para la Siguiente Sesión
[Tareas exactas pendientes en orden de prioridad]

## 4. Rutas Clave del Ecosistema
[Rutas a archivos fuente, assets y catálogos]
```

### 3. Actualización de Puntero Inmediato
Actualizar [`memory-bank/core/notes-next-session.md`](file:///home/tec/Dropbox/ANTIGRAVITY_PROJECTS/memory-bank/core/notes-next-session.md) con el enlace y resumen de este último handoff.

### 4. Entrega del Prompt de Reanudación
```text
@[/home/tec/Dropbox/ANTIGRAVITY_PROJECTS/memory-bank/journal/<archivo_handoff>.md] handon!!
```

---

## 🟢 3. Protocolo de Entrada: `handon!!` o `/handon`

Al recibir **`handon!!`**, **`/handon`** o la opción `2`, el agente **DEBE** ejecutar:

### 1. Localización del Handoff
- Si el usuario mencionó `@archivo_handoff.md`, leer directamente ese archivo.
- Si no mencionó ninguno, buscar automáticamente en `memory-bank/journal/` el `*_handoff.md` más reciente o leer `notes-next-session.md`.

### 2. Briefing Estructurado de Arranque
Responder de inmediato en español:

```markdown
👋 **Sesión Sincronizada — Hand-On Activo**

📍 **Proyecto:** [Nombre del Cliente / Proyecto]  
📅 **Último Handoff:** [Fecha del handoff leído]  
🟢 **Servidor / Entorno:** [Estado de servicios locales]

---

### 📌 Estado Actual del Proyecto:
- [Hito 1 completado en la sesión anterior]
- [Hito 2 completado en la sesión anterior]

### 🎯 Tareas Prioritarias en Agenda:
1. **[Tarea 1 Inmediata]**: [Detalle breve]
2. **[Tarea 2]**: [Detalle breve]
3. **[Tarea 3]**: [Detalle breve]

---

¿Por cuál de estas tareas deseas arrancar o tienes alguna instrucción prioritaria?
```

> [!CAUTION]
> **Regla de Espera**: El agente **NO** debe modificar código ni ejecutar cambios destructivos tras el `handon!!` sin la confirmación explícita del usuario.

---

## 🔄 4. Compatibilidad Multi-Agente

| Agente | Soporte | Notas |
|---|:---:|---|
| **Antigravity IDE** | ✅ Completo | Menú interactivo, lectura de journals |
| **OpenCode CLI** | ✅ Completo | Menú en texto, escritura de journals |
| **Hermes CLI** | ✅ Completo | Menú en texto, escritura de journals |
| **Modo Degradado** | — | Si `lsof` no disponible, omitir detección de servidores sin bloquear |
