# Pruebas de fallo (v2.2)

| Escenario | Simulacion | Criterio PASS |
|---|---|---|
| Pensamiento largo | Prompt que fuerce >30 s de Thinking Medium | No aborta a los 24 s; espera hasta 240 s |
| Respuesta ultrarrápida | Prompt trivial que responda en <5 s | No se queda esperando el boton de parada |
| Crash en streaming | Cerrar la pestana mientras crece el texto | Reabre la URL de ESTADO.md y extrae sin reenviar |
| Listener de input roto | Inyectar texto sin InputEvent | Desbloquea el envio con Espacio + Backspace |
| Redireccion de cuenta | Abrir /u/3/ con sesion de otra cuenta | Aborta con 0 envios |

## Extraccion
- Convertir HTML a Markdown (o boton "Copiar respuesta"); nunca `textContent` plano.
- Excluir el nodo de pensamiento.
- Exigir >200 caracteres y descartar errores del sistema.

## Artefactos
- Escritura atomica `.tmp` + `rename`.
- `MANIFEST.sha256` actualizado por ronda y verificado con `sha256sum -c` al cerrar.
