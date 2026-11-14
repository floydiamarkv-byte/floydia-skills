---
name: f-dialogo-externo
description: "Conduce el navegador del operador en un dialogo externo de cuatro rondas con estado en disco. Activar para abrir pestana, pegar rondas de encuadre a cierre, o extraer y archivar respuestas. No usar para envio masivo por API ni cotejo sin navegador."
version: 2.2.0
license: MIT
metadata:
  cost: "0.00 USD (navegador del operador; sin API)"
  depends-on: "browse MCP + extension emparejada; cuenta Gemini del operador; scratch/"
  browser_default: "https://gemini.google.com/u/3/app"
  account_guard: "/u/3/"
  mode_default: "Argon / Thinking level Medium"
  max_sends_default: 5
  brother-skill: "f-enjambre-externo"
---

# f-dialogo-externo — consulta iterativa con IA externa (browser-first)

> El agente conduce el navegador del operador: abre la pestana, pega la ronda, espera,
> extrae la respuesta y la archiva. El humano solo interviene en login, 2FA, captcha,
> cambio de cuenta o confirmacion de cupo. Una ronda por turno. El estado vive en disco.

## Cuando usar / cuando no

| Usar | No usar |
|---|---|
| Refinar un plan o auditar con una IA externa en rondas | Consultar varios modelos y cotejar → `f-enjambre-externo` |
| El operador tiene cuenta web (Gemini Pro) sin API | Investigar en la web → `f-investiga` |
| Segunda opinion sobre arquitectura, texto o decision | Extraer una URL → `f-scraper` |

## Preflight (obligatorio, en orden)

1. `browse_status`: relay y extension conectados y emparejados. Si no, `handoff` para re-emparejar. No reintentar en bucle.
2. Abrir o adoptar la pestana (por defecto `https://gemini.google.com/u/3/app`). Validar cuenta: si la URL no contiene `/u/3/`, comprobar el `aria-label` del perfil de Google; si no coincide con la cuenta objetivo, abortar sin enviar.
3. Verificar el selector: debe mostrar `Argon` y `Thinking level: Medium`. Si no, cambiarlo y reconfirmar la etiqueta antes de enviar.
4. Confirmar brief y objetivo medible. Si falta, pedirlo antes de R1.
5. Crear la sesion en `scratch/dialogo_externo/<YYYY-MM-DD>_<slug>/`.
6. Higiene: sin secretos, tokens, PII ni datos de cliente. Solo `${VAR}` o `[REDACTED]`.

## Maquina de estados (4 rondas densas por defecto)

| Ronda | Objetivo | Cierra cuando |
|---|---|---|
| R1 ENCUADRE | plan adversarial y huecos con severidad | hay plan y huecos listados |
| R2 EVIDENCIA | verificar/refutar los huecos con extractos reales | cada hueco tiene veredicto o falta de evidencia declarada |
| R3 CORRECCION | corregir falsos positivos y depurar el plan | plan final de 6 cambios con tests |
| R4 CIERRE | informe final, checklist y riesgos aceptados | `SINTESIS.md` escrito |

Ampliable a 6 solo si el operador lo pide. Reglas de parada: convergencia, dos rondas sin hallazgos nuevos, contradiccion irresoluble (`[DISPUTADO]`), cupo agotado o aborto.

## Contrato de cada ronda

- UN envio por turno, autocontenido, en bloque de 4 backticks para copia manual si hiciera falta.
- Presupuesto de evidencia: <= 150 lineas de codigo por ronda; nunca el repo entero.
- NUNCA reenviar por timeout: sondear y, si el stream muere, `handoff`.
- Extraer la ULTIMA respuesta en Markdown (no `textContent` plano), esperar estabilizacion y excluir el bloque de pensamiento.
- Guardar y actualizar `ESTADO.md` (URL con ID, cupo usado, nodos antes/despues).

## Conduccion del navegador (browse)

1. `page.goto(url)` con `domcontentloaded`; esperar 3 s.
2. Limpiar el input: `click`, `Control+A`, `Backspace`; verificar que queda vacio.
3. `insertText(prompt)`; verificar primeros y ultimos 40 caracteres. Si el boton de enviar sigue `disabled`, pulsar `Espacio` + `Backspace` para disparar el listener del editor.
4. Antes de enviar: `count_prev = document.querySelectorAll('model-response').length`. Pulsar enviar.
5. Inicio del turno cuando `boton_parada_visto` O `count_actual == count_prev + 1`. Fin cuando `count_actual == count_prev + 1` Y el boton de parada NO esta visible, con el texto estable durante 2 ciclos.
6. Sondear cada 8 s, maximo 30 ciclos (240 s). No aplicar la regla de "sin crecimiento" mientras el indicador de pensamiento este activo o el boton de parada sea visible con el texto final vacio.
7. Tras enviar R1, esperar en bucle de 500 ms (maximo 15 s) hasta que la URL cumpla `/\/app\/[a-zA-Z0-9]+/`; guardarla en `ESTADO.md` antes de sondear.
8. Extraer el ultimo `model-response` convirtiendo su HTML a Markdown (o usando el boton nativo "Copiar respuesta"), excluyendo el nodo de pensamiento.

## Recuperacion y persistencia

- Si se pierde la pestana: reabrir la URL de `ESTADO.md`; re-verificar `Argon Medium` y la cuenta (/u/3/).
- Si `count_actual == count_prev + 1` al reabrir, confirmar que el boton de parada NO esta visible y que el texto no cambia en 2 ciclos antes de extraer. Solo reenviar si no hay nodo nuevo.
- Si hay varias pestanas de `/u/3/app`, adoptar solo la que coincida con el ID de `ESTADO.md`; en R1 usar una pestana nueva.
- Al reanudar tras un `handoff`: repetir validacion de cuenta, selector y conteo de nodos antes de continuar.

## Cupo y fallos

- Tope por defecto: 5 envios (4 rondas + 1 margen). Contabilizar en `CONSULTAS.md` cada intento, exitoso o fallido.
- Distinguir bloqueo temporal de agotamiento diario. Si el operador indica un reset, esperar ese tiempo; si no se conoce, `handoff` y preguntar.
- Senales de cupo: sin respuesta nueva, banner de limite, captcha. Entonces `handoff` (pausa y espera) o cierre con `SINTESIS.md` y estado `DEGRADADA`. Prohibido el reintento en bucle.
- Antes de guardar una respuesta: exigir >200 caracteres y que no sea un mensaje de error del sistema ("Algo salio mal", "No puedo ayudar con eso"); si falla, registrar en `CONSULTAS.md` y `handoff`.
- Relay caido: `browse doctor`; si no se arregla en un intento, modo manual (copiar/pegar) y decirlo.
- Nunca automatizar login, 2FA, passkeys ni captchas.

## Estado de sesion

`scratch/dialogo_externo/<fecha>_<slug>/`
- `ESTADO.md` — ronda, huecos, URL de conversacion, cupo, decisiones, siguiente accion
- `RONDA_N_PROMPT.md` y `RONDA_N_RESPUESTA.md`
- `CONSULTAS.md` — bitacora: hora, ronda, enviados, recibidos, nodos antes/despues, resultado
- `SINTESIS.md` — informe final con procedencia
- `MANIFEST.sha256` — sellado al cerrar, tambien en aborto

Escritura atomica: `.tmp` + `rename` para cada artefacto; actualizar `MANIFEST.sha256` al final de cada ronda completada.

Plantillas: `references/plantillas.md`. Convergencia: `references/criterios-convergencia.md`. Protocolo: `references/protocolo-rondas.md`.

## Procedencia

Toda afirmacion externa nace `[EXTERNO/NO VERIFICADA]`; pasa a `[HECHO]` solo con verificacion local; contradiccion = `[DISPUTADO]`; cita inexistente = `[RECHAZADA]`.

## Contrato de salida

Cada turno: ronda activa, bloque enviado, respuesta archivada, estado actualizado y siguiente accion. Al cerrar: `SINTESIS.md`, `MANIFEST.sha256` verificado con `sha256sum -c` y checklist marcada.
