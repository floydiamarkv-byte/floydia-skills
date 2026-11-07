# Asignar modelos a slots: razonador vs formateador

Regla: **un slot se define por su presupuesto de salida, no por la calidad que quieres.**

| Clase de slot | Ejemplos | Motor | Presupuesto típico |
|---|---|---|---|
| Decide | descomposición de tareas, juicio de objetivo, review | razonador (el mejor que el plan permita) | 1 500–8 000 tok |
| Formatea | título, compresión, triage descriptivo, voz | pequeño **no razonador** | 40–300 tok |
| Ve | QA de captura, OCR de cifras | modelo VL medido | 300–1 000 tok |

## Por qué el razonador rompe los slots de formato

Medido con el `max_tokens` real del slot, no con el del bench:

| `max_tokens` | Resultado |
|---|---|
| 60 | 1 222 ms · `out=60` · `finish=length` · **`content: ""`** |
| 150 | 1 569 ms · `out=150` · `finish=length` · **`content: ""`** |
| 400 | **429 «circuit breaker: repetitive»** (bucle de pensamiento) |
| 600 (canario) | 200 · texto correcto |

Un canario de 600 tokens **no certifica** el modelo para un slot de 60: el mismo motor pasa
uno y falla el otro. El síntoma en producción no es un error: es un título vacío o una
compresión en blanco, silencioso.

## Cómo se prueba un slot (30 s, $0 en el pool local)

```python
# usar el max_tokens que el slot usa de verdad, la tarea que el slot hace de verdad
task = "Titula en 4 palabras: <tema real del slot>"
body = {"model": MID, "messages": [{"role": "user", "content": task}],
        "max_tokens": 80, "temperature": 0}
# criterio de aptitud: content no vacío, finish_reason == "stop",
# y completion_tokens <= 3 × max_tokens (si no, está razonando de más)
```

Repetir 3 veces: un vacío aislado puede ser arranque en frío.

## Ventanas de saturación

`429 upstream overloaded` es del modelo, no de la cuenta: en el mismo minuto un hermano del
mismo plan respondió 200. Sondear el hermano antes de tocar la configuración y, si el slot es
crítico, dejarlo apuntando al hermano que responde mientras pasa el pico.

## Orden de fallback que funciona

1. Pool local $0 no razonador — es el que hace el 90 % del trabajo de formato.
2. Razonador de pago — sólo para los tres slots que deciden.
3. Pool local otra vez, como último recurso (nunca un razonador en un slot de 60 tokens).

Al reescribir el bloque `auxiliary` de un YAML a mano, conserva las claves extra de cada slot
(`reasoning_effort: none` en voz, por ejemplo): reconstruir el bloque desde un dict borra
esas claves sin avisar y el slot pierde su configuración de latencia.
