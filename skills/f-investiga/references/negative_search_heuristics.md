# 🔍 Heurísticas de Búsqueda Negativa & Contradiction Hunter

> **Propósito**: Conjunto de patrones de consulta deterministas para demoler el sesgo de confirmación y descubrir fallos, limitaciones, cuellos de botella y contradicciones en tecnologías, librerías o afirmaciones técnicas.

---

## 1. Patrones de Falsación por Categoría

### A. Estabilidad & Producción
- `"<tema>" ("memory leak" OR "high cpu" OR "OOM" OR "out of memory")`
- `"<tema>" ("crash" OR "segfault" OR "panic" OR "hang" OR "deadlock")`
- `"<tema>" ("production outage" OR "incident report" OR "postmortem")`

### B. Adopción & Abandono
- `"<tema>" ("why we left" OR "why we migrated away from" OR "abandoned")`
- `"<tema>" ("not recommended" OR "regret" OR "pitfalls" OR "anti-pattern")`
- `"<tema>" vs ("alternative" OR "replacement")`

### C. Seguridad & Vulnerabilidades
- `"<tema>" ("security advisory" OR "CVE" OR "vulnerability" OR "exploit")`
- `"<tema>" ("unauthenticated" OR "privilege escalation" OR "RCE")`

### D. Rendimiento & Benchmarks Críticos
- `"<tema>" ("benchmark" OR "bottleneck" OR "latency regression")`
- `"<tema>" ("slow" OR "overhead" OR "scaling issues")`

---

## 2. Matriz Dialéctica (Tesis vs Antítesis)

Al encontrar una afirmación positiva fuerte ($T$), el agente debe generar y buscar activamente la afirmación inversa ($\neg T$):

| Tesis ($T$) | Consulta Negativa ($\neg T$) | Criterio de Resolución |
|---|---|---|
| "X es la mejor opción para Y" | `"X" issues limitations when used for "Y"` | Comparar el volumen de problemas reportados en GitHub/Reddit vs las virtudes proclamadas en la documentación oficial. |
| "X tiene cero sobrecarga" | `"X" benchmark CPU latency overhead real world` | Descartar pruebas sintéticas y priorizar pruebas de estrés con carga real. |
| "X es 100% compatible con Z" | `"X" "Z" incompatibility breaking changes` | Verificar changelogs oficiales y tickets abiertos en repositorios. |

---

## 3. Clasificación de Resultados Negativos
- **Fallo Crítico No Resuelto**: Clasificar como 🔴 `[BLOQUEO_CONFIRMADO]` y destacar en el informe.
- **Fallo Resuelto en Versión Reciente**: Clasificar como 🟢 `[RESUELTO]` indicando versión mínima requerida.
- **Limitación por Diseño**: Clasificar como 🟡 `[LIMITACION_ESTRUCTURAL]` con sugerencia de mitigación.
