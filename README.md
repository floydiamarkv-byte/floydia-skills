# ⚡ FloydIA Agent Skills Suite

[![CI](https://github.com/floydiamarkv-byte/floydia-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/floydiamarkv-byte/floydia-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Suite Metodológica, Gobernanza SRE y Habilidades Agénticas de Alto Rendimiento para Google Antigravity, OpenCode, Claude Code y Hermes CLI.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Compatibility](https://img.shields.io/badge/AI%20Ecosystem-Antigravity%20%7C%20OpenCode%20%7C%20Hermes%20%7C%20Claude-06B6D4.svg)](#compatibilidad)
[![Architecture](https://img.shields.io/badge/Protocolo-v27%20SSOT-10B981.svg)](#arquitectura)

La suite **FloydIA Agent Skills** reúne los protocolos y herramientas agénticas desarrollados por el ecosistema FloydIA. Diseñada bajo principios de **ingeniería de arneses (Harness Engineering)**, determinismo operativo y economía de tokens, esta suite permite que modelos de lenguaje actúen como ingenieros SRE, optimizadores de prompts y orquestadores multi-agente sin incurrir en bucles, alucinaciones o degradación de contexto.

---

## 📦 Catálogo de Skills

| Skill | Comando / Trigger | Descripción |
| :--- | :--- | :--- |
| **`f-harness-workflow`** | `/f-harness` | **Ingeniería de Arneses**: Flujo de trabajo estructurado con 4 roles desacoplados (*Líder, Explorador, Implementador, Revisor*) y principio de *Evidencia antes de Afirmar*. |
| **`f-mejora-prompt`** | `/f-mejora`, `/mejora` | **Optimizador Avanzado de Prompts**: Arquitectura *Menu-First*, taxonomía CAT_01..08, calibración LRM y compilación quirúrgica. |
| **`f-audit-web`** | `/f-audit-web`, `/audit-web` | **Auditoría Externa por Portapapeles**: Permite actuar como ojos y manos locales para diagnósticos de IAs web potentes mediante texto plano. |
| **`f-opti-notebooklm`** | `/f-opti-notebooklm` | **Curador y Enriquecedor de NotebookLM**: Síntesis temática, extracción estructurada e inyección de base de verdad (*Ground Truth*). |
| **`f-opti-floydia`** | `/f-opti`, `/opti` | **SRE Governor**: Detección de cuellos de botella de latencia, diagnóstico de nodos, resiliencia y telemetría de agentes. |
| **`f-update-floydia`** | `/f-update`, `/update` | **Mantenimiento Determinista**: Suite de actualización segura en Linux/Arch (pacman, AUR, flatpak) con chequeos de integridad. |
| **`f-handon-handoff`** | `/f-handoff`, `/f-handon` | **Continuidad Agéntica**: Persistencia de contexto en journals inmutables y traspaso de sesión sin pérdida de estado. |
| **`f-client-router`** | `/f-clientes`, `/clientes` | **Router de Contexto de Clientes**: Enrutamiento canónico de proyectos, briefs y accesos con aislamiento de dominios. |
| **`f-env-descriptor`** | `/f-descripcion`, `/entorno` | **Handoff Exhaustivo de Entorno**: Generador de reportes de introspección técnica de hardware, red, agentes y SO. |

---

## 🚀 Instalación y Uso

### 1. Google Antigravity / Gemini CLI
Clona o enlaza los skills dentro de tu directorio de configuración global o en tu workspace:
```bash
# Instalación a nivel de workspace
mkdir -p .agents/skills
cp -r skills/* .agents/skills/

# O instalación a nivel de usuario
mkdir -p ~/.gemini/config/skills/
cp -r skills/* ~/.gemini/config/skills/
```

### 2. OpenCode
```bash
mkdir -p ~/.config/opencode/skills/
cp -r skills/* ~/.config/opencode/skills/
```

### 3. Hermes CLI
```bash
mkdir -p ~/.hermes/skills/
cp -r skills/* ~/.hermes/skills/
```

---

## 🛡️ Seguridad y Privacidad

- **100% Sanitizado**: Todos los skills han sido auditados exhaustivamente para garantizar que no contengan credenciales, tokens, contraseñas, direcciones IP privadas ni datos confidenciales.
- **Variables Universales**: Rutas y endpoints se definen dinámicamente mediante variables de entorno estándar (`$WORKSPACE_ROOT`, `$HOME`, etc.).

---

## 📄 Licencia

Distribuido bajo la Licencia **MIT**. Consulta el archivo [`LICENSE`](LICENSE) para más información.

**Autor**: FloydIA ([floydiamarkv@gmail.com](mailto:floydiamarkv@gmail.com))
