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
| **`f-harness`** | `/f-harness`, `/harness` | **Centro de Control Unificado del Harness (v4.3)**: Routing de 11 motores, gestión de presupuesto atómico WAL, gobernanza OpenCode Go ($10/mo) y selector de modos. |
| **`f-evidence-engine`** | `/f-evidence` | **Motor de Evidencia Determinista**: Certificación criptográfica SHA256, validación Playwright multi-contexto y verificación antes de afirmar. |
| **`f-orquestador-floydia`** | `/f-orquestador` | **Orquestador Multi-Agente & Arquitectura**: Asume rol de Arquitecto Director, delegación algorítmica y diseño de software. |
| **`f-mejora-prompt`** | `/f-mejora`, `/mejora` | **Optimizador Avanzado de Prompts v5.1**: Arquitectura Menu-First interactiva de 8 modos, calibración LRM y compilación quirúrgica. |
| **`web-quality-audit`** | `/web-quality-audit` | **Auditoría Integral de Calidad Web**: Evaluación determinista Core Web Vitals (LCP/CLS), accesibilidad WCAG AAA y SEO técnico. |
| **`f-handon-handoff`** | `/f-handoff`, `/f-handon` | **Continuidad Agéntica**: Persistencia de contexto en journals inmutables y traspaso de sesión sin pérdida de estado. |
| **`f-master-update`** | `/f-master-update` | **Super Suite SRE**: Mantenimiento determinista del sistema operativo, memoria, agentes y sincronización NotebookLM. |
| **`f-investiga`** | `/f-investiga` | **Investigación Profunda**: Modos Indagación (NotebookLM y vault) y Enjambre (consenso multi-modelo en paralelo). |

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
