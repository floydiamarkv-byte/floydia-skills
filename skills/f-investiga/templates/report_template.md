# Plantilla de informe — f-swarm-research

> Generado por el fan-in (`merge_findings.py`) + verificación (`verify_citations.py`).
> Regla: **toda afirmación lleva etiqueta epistémica y cita verificada.** Sin etiqueta, no va en el informe.

---

# Informe: <TEMA>

**Fecha de ejecución**: <YYYY-MM-DD HH:MM UTC> · **Corte de datos**: <YYYY-MM-DD>
**Motores Consultados**: <n> · **Fuentes únicas**: <n> · **Modo**: <rápido|profundo|exhaustivo>
**Coste real de inferencia**: $0.00

## 1. Resumen ejecutivo

<Máximo 150 palabras. Sin jerga. Di qué se Planet y qué no se pudo determinar.>

## 2. Estado del enjambre

| Métrica | Valor |
| :-- | :-- |
| Hallazgos totales | <n> |
| Clústeres de afirmación | <n> |
| Fuentes deduplicadas | <n> |
| **Veredicto de consenso** | `<CONSENSO \| MAYORIA_2 \| UNANIMIDAD_SOBRE_PREMISA_NO_VERIFICADA \| SIN_CONSENSO>` |
| Votos del clúster ganador | <n>/<n> |
| Índice de divergencia | <0.0-1.0> |

> ⚠️ `<advertencia de consenso, copiada de merge_findings.py>`

## 3. Hallazgos verificados

### 🟢 [HECHO] — fuente primaria verificada

**<Afirmación atómica>**

- **Evidencia**: <descripción>
- **Fuentes**:
  - `<url>` — *<título real de la página>* — <fecha> — `<fragmento literal>`
    → ✅ verificada (HTTP <status>, wayback <snapshot>)
  - `<url>` — *<título>* — <fecha>
    → ✅ verificada
- **Confianza**: <alta|media|baja> (<n>/<n> motores)
- **Fecha del hecho**: <YYYY-MM-DD> | **Fecha de consulta**: <YYYY-MM-DD>

### 🟡 [INFERENCIA] — deducción razonada

**<Afirmación>**

- **Derivada de**: <lista de hallazgos [HECHO] que la sostienen>
- **Límite**: <qué la haría falsa>

### 🟠 [DISPUTADO] — fuentes autorizadas en conflicto

**<Tema en disputa>**

| Posición A | Posición B |
| :-- | :-- |
| <afirmación> | <afirmación> |
| `<url>` | `<url>` |
| `<titulo real>` | `<titulo real>` |

- **Por qué no se resuelve**: <motivo>
- **Qué la resolvería**: <fuente o prueba faltante>

### 🔴 [NO_VERIFICABLE] — ninguna cita sobrevive

**<Afirmación descartada>**

- **Citas que fallaron**:
  - `<url>` → `<motivo: ALUCINACION SEMANTICA / nunca existió / no responde>`
- **Acción**: excluida del informe

## 4. Fuentes descartadas y por qué

| URL | Motivo | potencialmente recuperable |
| :-- | :-- | :-- |
| `<url>` | nunca archivada + 404 | No |
| `<url>` | título real no respalda la afirmación | No |
| `<url>` | detrás de bloqueo de red conocido | Sí, reintentar desde otra IP |

## 5. Vacíos de cobertura

**Lo que NO se pudo determinar:**

- < vacío 1 > — por qué: <sin key /fuente caída / sin documentacion pública>
- < vacío 2 >

> Usar la formulación del principio de ausencia de evidencia:
> *«No se encontró documentación pública tras consultar N fuentes»* — **nunca** *«no existe»*.

## 6. Consultas externas (HIL)

| IA | Ronda | Fecha | Resultado tras verificación |
| :-- | :-- | :-- | :-- |
| ChatGPT | 0 | <fecha> | `<n>` afirmaciones aceptadas, `<n>` rechazadas |
| Claude | 1 | <fecha> | — |

> Toda respuesta externa entra etiquetada `[FUENTE: EXTERNA-NO-VERIFICADA]`
> hasta que `verify_citations.py` la respalda.

## 7. Herramientas degradadas en esta ejecución

| Herramienta | Estado | Impacto en el informe |
| :-- | :-- | :-- |
| `web_search` | FALLA (HTTP 402) | Sin búsqueda nativa; se usó curl + MCP |
| DuckDuckGo | PROBADO_CON_INTERMITENCIA | Cobertura de búsqueda web parcial |
| Reddit .json | FALLA (403) | Se usó `.rss` |

## 8. Manifiesto

```
MANIFEST.sha256 — <n> artefactos
<hash>  inventory.json
<hash>  finding-<id>.json  (× n)
<hash>  consensus.json
<hash>  verificacion.json
<hash>  informe.md
```

> Sin manifiesto SHA-256, esta tarea **no está cerrada**.
