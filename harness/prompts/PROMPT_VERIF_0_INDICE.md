# Prompts de verificación del harness (4 ejes)

Cada prompt es **autocontenido**: se pega en una sesión nueva y produce un veredicto binario con evidencia.
Se pueden encadenar (1 → 2 → 3 → 4) o correr sueltos.

| # | Prompt | Pregunta que responde | Coste | Tiempo |
|---|---|---|---|---|
| 1 | `PROMPT_VERIF_1_ESTADO.md` | ¿está vivo y coherente? | $0,00 | ≤ 5 min |
| 2 | `PROMPT_VERIF_2_CAPACIDAD.md` | ¿este modelo sirve para este slot? | ≤ 1 % ventana 5 h | 10–20 min |
| 3 | `PROMPT_VERIF_3_PRESUPUESTO.md` | ¿cuánto queda, a qué ritmo, a qué coste por entregable? | $0,00 | 5 min |
| 4 | `PROMPT_VERIF_4_PROPAGACION.md` | ¿llegó igual y funciona en el segundo host y en los paneles? | $0,00 | 10 min |

## Cuándo cada uno

- **P1** antes de trabajar y después de cualquier reinicio.
- **P2** antes de meter/cambiar un modelo en una ruta.
- **P3** semanal o cuando el panel y el endpoint no cuadren.
- **P4** antes de declarar terminado un cambio de configuración.

## Regla común

Ninguno aplica cambios: entregan informe + propuesta. Escribir el SSOT exige token humano (R3).
