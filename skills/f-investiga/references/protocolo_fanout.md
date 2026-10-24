# Protocolo de fan-out

> Basado en la metodología de Karpathy (*LLM Council*): dispatch a N motores → revisión anónima → chairman sintetiza.

## 1. Paralelismo — no negociable

**Secuencial auto-anchora las respuestas.** El motor 2 ve lo que dijo el motor 1 y se alinea. En DSH: `run_in_background: true` en todos los subagentes, o `parallel()` en el tool `workflow`.

> Verificado: 4 modelos `:free` en paralelo = 4roeferencias independientes, 4 familias distintas (NVIDIA, Dots, Cohere, Liquid) para decorrelacionar errores.

## 2. Lentes de pensamiento (no solo canales)

Ocho motores con el mismo rol devuelven **ocho respuestas idénticas**. La tensión útil viene de la lente, no del modelo.

| Lente | Pregunta que se hace |
| :-- | :-- |
| **Primera-principios** | ¿Qué es verdad aquí eliminando toda suposición? |
| **Contrarian** | ¿Cuál es el argumento más fuerte contra esto? |
| **Pragmatista** | ¿Qué se hace el lunes por la mañana con esto? |
| **Escéptico** | ¿Qué evidencia FALTA para sostenerlo? |
| **Histórico** | ¿Qué pasó la última vez que se intentó esto? |
| **Outsider** | ¿Lo que se dice aquí es un consenso real o un eco repetido? |

Para una **revisión adversarial** (auditar afirmaciones), usa: `Contrarian` + `Escéptico` + `Pragmista` + `Histórico`.

## 3. Tope duro de palabras

| Rol | Tope |
| :-- | :-- |
| Asesor / investigador | 150-300 palabras |
| Revisor | ≤200 palabras |
| Chairman / veredicto | ≤600 palabras |

Sin tope, 8×3k tokens revientan el contexto padre y el synthesis se vuelve imposible.

## 4. Anonimización de revisores

Un revisor que sabe quién escribió cada respuesta **juzga el estilo, no el contenido**.

```
Mapea las respuestas a "Response A", "Response B"… con orden ALEATORIO.
Muestra solo A-E al revisor. El mapeo real se revela solo al sintetizar.
```

## 5. Artefactos en disco, no en el chat

Cada subagente escribe `runs/<slug>/finding-<id>.json`. El padre lee **solo** el resumen, nunca el transcript completo. Es la barrera anti-explosión de contexto.

## 6. Normalización de salida de modelos

Probado el 2026-09-28: los proveedores fallan de formas distintas. `fanout_models.py` ya lo cubre:

| Fallo | Síntoma | Mitigación |
| :-- | :-- | :-- |
| Fuga de razonamiento | `content` trae el thinking | strip `<think>…</think>` y prefijos "Here's a thinking…" |
| Content nulo | `content: null`, hay `reasoning` | caer al campo `reasoning` |
| Rate limit | 429 upstream | backoff exponencial 2^n |
| Provider error | `Provider returned error` | retry acotado |
| Edad verificada | `only available on age-verified accounts` | clasificar `AGE_GATED`, no reintentar |

## 7. Circuit breaker por proveedor/modelo

Un modelo que falla 2 veces seguidas en una ronda **se marca y no se reintenta** en esa ronda. Evita que un proveedor muerto consuma la mitad del presupuesto temporal.

## 8. Regla epistémica del consenso

```
"Todos de acuerdo" ≠ "es verdad"
```

`merge_findings.py` clasifica:
- `CONSENSO` — ≥3 motores, al menos un cluster
- `MAYORIA_2` — 2 motores coinciden, el resto no
- `UNANIMIDAD_SOBRE_PREMISA_NO_VERIFICADA` — **1 solo cluster con todos los motores**. Todos compartieron premisa; eso no la valida.
- `SIN_CONSENSO` — cada motor va por su lado

El campo `divergencia` = proporción de motores en posición distinta a la ganadora.

## 9. Anti-patrones (resumen)

| ❌ Anti-patrón | ✅ Regla |
| :-- | :-- |
| Lanzar todas las fuentes indiscriminadamente | Seleccionar por tipo de pregunta; un enjambre sin roles multiplica coste y afirmaciones sin verificar |
| Fan-out secuencial | Siempre paralelo |
| Revisores sin anonimizar | Response A-E con orden aleatorio |
| Acumular transcripts en el padre | Artefactos en disco |
| "8 motores, mismo prompt" | 8 lentes distintas |
| 3 copias del prompt literal | Un template en `templates/` |
| Citar sin verificar | `verify_citations.py` antes de escribir |
| Confundir "no hay resultados" con "falló" | Estados separados en el doctor |
