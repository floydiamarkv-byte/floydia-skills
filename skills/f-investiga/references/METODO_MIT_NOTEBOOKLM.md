# Metodología de Curaduría e Ingesta MIT en Google NotebookLM (50–200 Fuentes)
### Extensión de Referencia para `searcher-floydia` v2.0

---

## 🏛️ 1. Cuotas y Criterios de Calidad MIT

- **Volumen Objetivo**: Cada cuaderno debe albergar entre **50 a 100+ fuentes** (extendible a **200 fuentes** para materias de alta complejidad o dominios canónicos).
- **Filtro de Autoridad**:
  1. *Fuentes Primarias*: Documentación oficial de APIs, repositorios oficiales de GitHub, papers de arXiv, manuales de hardware y estándares RFC/W3C.
  2. *Análisis de Expertos*: Charlas técnicas de conferencias, artículos de ingeniería de equipos de producción (Anthropic, OpenAI, Meta, Google DeepMind) y debates técnicos en foros especializados.
  3. *Deduplicación Estricta*: Normalización de URLs y hash SHA256 (usando `scripts/sources_manager.py`).

---

## 📐 2. Los 3 Pilares del Método de Extracción MIT

Al curar un cuaderno o generar documentos de síntesis para NotebookLM (`source_add --file`), el agente debe estructurar:

### Pilar 1: 5 Modelos Mentales Fundamentales
1. **Concepto / Modelo**: Nombre técnico del principio.
2. **Explicación Intuitiva (Técnica Feynman)**: Analogía simple y clara para no expertos.
3. **Mecanismo Operativo Real**: Cómo funciona a bajo nivel (flujo de datos, algoritmos, arquitectura).
4. **Anti-Patrón Común**: Qué error comete el 90% de los desarrolladores al implementarlo.
5. **Ejemplo en Producción**: Caso práctico aplicado a nuestro stack (Arch Linux, Proxmox CT114, Colab GPU, WordPress, etc.).

### Pilar 2: 3 Debates de Expertos (Tesis vs Antítesis)
1. **Punto de Conflicto**: Dilema arquitectural o técnico no resuelto.
2. **Posición A (Tesis)**: Argumento técnico de sus defensores con pros y métricas.
3. **Posición B (Antítesis)**: Argumento técnico de sus detractores con contras y casos de fallo.
4. **Resolución / Consenso FloydIA**: Recomendación práctica fundamentada para nuestro entorno SSOT.

### Pilar 3: 10 Preguntas de Profundidad Evaluativa (Nivel 1 al 10)
- **Nivel 1–3 (Comprensión y Sintaxis)**: Preguntas de arquitectura básica y contratos de entrada/salida.
- **Nivel 4–7 (Diagnóstico y Edge Cases)**: Escenarios de fallo, degradación de memoria, race conditions y seguridad.
- **Nivel 8–10 (Arquitectura de Frontera)**: Compensaciones de latencia vs consistencia, escalabilidad y optimización extrema.

---

## 🛠️ 3. Comandos Deterministas CLI (`nlm`) y Scripts

- **Crear cuaderno**:
  ```bash
  python3 .agents/skills/searcher-floydia/scripts/nlm_bridge.py create "NOMBRE_DEL_CUADERNO"
  ```
- **Añadir URLs por lotes**:
  ```bash
  python3 .agents/skills/searcher-floydia/scripts/nlm_bridge.py add-batch <notebook_id> --file urls.txt
  ```
- **Normalizar y deduplicar fuentes**:
  ```bash
  python3 .agents/skills/searcher-floydia/scripts/sources_manager.py --workspace scratch/research_topic/
  ```
