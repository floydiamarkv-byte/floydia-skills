---
name: f-clientes
description: "Gestor de contexto de clientes y proyectos. Enruta al dominio canónico correcto, carga el brief del cliente, presenta tareas pendientes y accesos. USAR cuando el usuario invoque /f-clientes, /clientes, o pida trabajar en un cliente específico (PROJECT_ALPHA, PROJECT_BETA, PROJECT_GAMMA, PROJECT_DELTA). NO USAR para operaciones técnicas directas sin contexto de cliente."
version: 1.0.0
triggers:
  - /f-clientes
  - /clientes
  - /cliente
  - cambiar cliente
  - contexto cliente
  - brief cliente
---

# Skill: Gestor de Contexto de Clientes (`f-clientes` v1.0)
## Enrutamiento, Brief y Estado por Cliente

> **Propósito**: Proveer acceso rápido y estructurado al contexto de cada cliente del portafolio, evitando confusiones entre dominios y garantizando que el agente opere con el brief, accesos y assets correctos.

---

## 🎯 1. Menú Interactivo Menu-First

Al invocar `/f-clientes`, `/clientes` o solicitar trabajar con un cliente, el agente **DEBE responder presentando este menú interactivo**:

```markdown
╔═══════════════════════════════════════════════════════════════╗
║       💼 F-CLIENTES — GESTOR DE CONTEXTO DE CLIENTES           ║
╚═══════════════════════════════════════════════════════════════╝

Selecciona el cliente o acción respondiendo con el **número** correspondiente:

1️⃣ 🌳 **PROJECT_ALPHA 3.0**
   ↳ E-commerce orgánico, WooCommerce, WordPress Bluehost
   ↳ Ruta: `CLIENTES/PROJECT_ALPHA/`

2️⃣ ⚡ **PROJECT_BETA**
   ↳ Producto IoT de ahorro energético, e-commerce
   ↳ Ruta: `CLIENTES/PROJECT_BETA/`

3️⃣ 🧶 **PROJECT_GAMMA**
   ↳ Marca artesanal, catálogo de productos
   ↳ Ruta: `CLIENTES/PROJECT_GAMMA/`

4️⃣ 🌿 **PROJECT_DELTA**
   ↳ ONG ambiental, sitio web comunitario
   ↳ Ruta: `CLIENTES/PROJECT_DELTA/`

5️⃣ 🎨 **FloydIA (Marca Personal)**
   ↳ Portafolio, brandbook, herramientas y subtools
   ↳ Ruta: `FLOYDIA/`

6️⃣ 📋 **Listar Todos los Clientes y Estado**
   ↳ Muestra una tabla resumen de todos los clientes con su estado actual.

0️⃣ **Salir**
```

---

## 📂 2. Estructura Interna por Cliente (v4)

Al seleccionar un cliente, el agente carga automáticamente:

| Subcarpeta | Contenido | Acción |
|---|---|---|
| `DRIVE/BRANDBOOKS/V<n>/` | Brandbooks e identidades versionadas | Leer `README.md` para contexto visual |
| `DRIVE/PUBLIC_WEB/V<n>/` | Maquetaciones, código frontend, builds | Identificar la versión activa |
| `DRIVE/INFO_<CLIENTE>/` | Accesos, brief, assets, contacto | **Cargar brief como contexto** |
| `DRIVE/PROMPTS/` | Prompts maestros de generación | Disponibles para `/f-mejora` |
| `DRIVE/_LEGACY/` | Material obsoleto preservado | Solo consultar si se necesita historial |

---

## 🔍 3. Carga de Contexto al Seleccionar Cliente

Al elegir un cliente, el agente ejecuta automáticamente:

1. **Leer el brief**: `CLIENTES/<NOMBRE>/DRIVE/INFO_<NOMBRE>/` (si existe).
2. **Consultar journals recientes**: `rg --glob '*.md' '<NOMBRE>' memory-bank/journal/ | tail -5`.
3. **Consultar NotebookLM**: `python3 SCRIPTS/notebooklm_curator.py "<nombre_cliente>"` para enrutar al cuaderno correcto.
4. **Presentar resumen**: Estado actual, última actividad y tareas pendientes.

---

## 🛡️ 4. Reglas de Seguridad por Cliente

- **PROHIBIDO** mezclar accesos FTP/WP de un cliente con otro.
- **PROHIBIDO** desplegar a producción sin confirmación explícita del usuario.
- Siempre verificar la URL del sitio destino antes de cualquier deploy.
- Credenciales se resuelven por nombre de clave en `.env`, NUNCA se exponen.

---

## 🔄 5. Compatibilidad Multi-Agente

| Agente | Soporte | Notas |
|---|:---:|---|
| **Antigravity IDE** | ✅ Completo | Menú interactivo, carga de brief |
| **OpenCode CLI** | ✅ Completo | Menú en texto, lectura de archivos |
| **Hermes CLI** | ✅ Completo | Menú en texto, lectura de archivos |
| **Modo Degradado** | — | Navegar manualmente a `CLIENTES/<NOMBRE>/` |
