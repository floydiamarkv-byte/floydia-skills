# NVIDIA NIM (build.nvidia.com) — tier gratuito, sondas y firmas de error

Profundidad para auditar o cablear el tier gratuito de NVIDIA NIM. Complementa
`references/opencode-go-plan-limits.md` (allí el plan de pago, aquí el $0).

## Contrato del tier

- Base URL OpenAI-compatible: `https://integrate.api.nvidia.com/v1` (chat, models, embeddings).
- Límite **oficial**, en la propia consola (`/settings/credits` y el FAQ de `/pricing`):
  «free to prototype with… up to **40 requests per minute** for most models, with **no
  per-token billing**»; el límite personal aparece en el dashboard.
- El «10 000 requests/día» que repiten los agregadores **no está publicado por NVIDIA**:
  no lo cites como cifra contractual. Si el operador lo necesita, que lo lea en su panel.
- La cuenta es por clave: varias claves rotando multiplican el RPM (es lo que hace un proxy
  con `rpm_per_account`), pero **no** comparten el arranque en frío: cada (cuenta, modelo)
  paga su propio primer token lento.
- Los ids viven en `GET /v1/models`; la marca «Free Endpoint» de la web es la que decide qué
  es gratis de verdad. `Free Endpoint` + catálogo coinciden casi siempre, pero **el catálogo
  incluye modelos sin aprovisionar** (ver firmas abajo).

## Firmas de error que NO significan lo mismo

| Respuesta | Significado | Acción |
|---|---|---|
| `410 Gone` + `has reached its end of life on <fecha>` | Tombstone definitivo del modelo. No necesita segunda confirmación. | Retirar del catálogo y del SSOT de routing; no readmitir por parecido de nombre. |
| `404` + `"Function '<uuid>': Not found for account '<id>'"` | El id **está** en `/v1/models` pero **no está aprovisionado para esa cuenta**: claves nuevas sin verificar, cuentas sin el modelo habilitado, o ids de modelo retirados del servicio dejando la entrada en catálogo. | Sondear con 2-3 cuentas distintas antes de decidir. Si todas dan lo mismo, es «no servido», no credencial. No confundir con un typo. |
| `404 page not found` | Ruta o id mal escrito. | Corregir el id; no es caída. |
| `400` + `Received multimodal data but multimodal processing is not enabled` | El modelo es solo texto aunque el proveedor lo anuncie como multimodal. | No cablearlo al slot de visión. |
| `200` con `model` distinto al pedido | Alias interno del proveedor (p.ej. `x-vl-120b` → `private/x-120b`). | Sonda de capacidad (imagen con texto) antes de concluir pérdida de visión. |

**Regla:** «figura en `/v1/models`» ≠ «mi cuenta lo sirve» ≠ «es gratis». Los tres se prueban
con una llamada de inferencia, no con el listado.

## Arranque en frío (la causa nº1 de «muerto» falso)

La primera llamada de cada par (cuenta, modelo) puede tardar **80-160 s** y devolver 200 con
el modelo correcto; la segunda, en el mismo minuto, baja a menos de 1 s.

- Un timeout de 25-90 s convierte ese arranque en un veredicto de caída. Repetir con `read`
  de 240-300 s o lanzar la segunda llamada de la misma cuenta antes de declarar nada.
- Si el modelo entra en producción, su perfil de timeout debe cubrir el arranque en frío
  (≥90 s), no el caso caliente; el perfil «rápido» calibrado con modelos ya calientes es el
  que entierra los endpoints nuevos.
- Consecuencia de diseño: un carril $0 para tareas interactivas necesita precalentado o un
  primer intento con presupuesto largo; el arranque frío no se arregla con reintentos cortos.

## Batería de sondas (4 ejes, una llamada por eje y modelo)

1. **Vida + identidad**: `max_tokens` 16-32, prompt mínimo; registrar status, `model` servido
   y latencia. Si `content` viene vacío pero `completion_tokens_details.reasoning_tokens`
   existe, está pensando: sube el presupuesto antes de puntuar.
2. **Trampa aritmética con presupuesto explícito**: una pregunta de respuesta numérica
   comprobable (p.ej. velocidades relativas 160/3 vs 240/4 = 20/3 ≈ 6,67) con
   `max_tokens` 1500-6000. Aceptar fracción y decimal en el scorer. Si
   `reasoning_tokens == max_tokens` y `finish_reason=length`, el modelo está truncado, no
   equivocado — repetir con 6 000 antes de escribirlo en el informe.
3. **`tool_calls` × 3**: función trivial + `tool_choice: auto`; contar
   `message.tool_calls`, nunca el texto. Un modelo sin herramientas sirve para texto y
   análisis, no como motor de arnés por rápido que sea.
4. **Visión, dos canarios**: (a) PNG pequeño con un texto legible (`HP15-42`) para probar que
   ve; (b) panel realista de varias filas con cifras distintas por fila y la pregunta «valor
   de las filas X, Y, Z». El segundo separa a los que **leen** de los que **adivinan**: en la
   misma tanda, un modelo pequeño y rápido acertó las tres cifras y uno grande y lento
   confundió dos filas. La visión se elige por ese canario, no por tamaño ni por marca.

Cerrar midiendo también el idioma: con un prompt ambiguo de dos palabras varios modelos
contestan en otro idioma. No es un defecto del motor — repite con instrucción explícita
(«responde en español») antes de descartarlo, y en producción instruye el idioma en el
system prompt.

## Lectura operativa de los resultados

- **El que acierta la trampa más rápido** es el candidato a motor de trabajo; el más rápido
  que falla la trampa solo vale como auxiliar.
- **Auxiliares y títulos** no necesitan razonamiento: ahí gana el de menor latencia con
  `tool_calls` 3/3, aunque falle aritmética.
- **Visión** se decide con el canario de panel, no con la marca.
- Un modelo gratis puede ser **el mismo** que ya se paga en otro plan (mismo id servido por
  el gateway de suscripción): antes de pagar por volumen, comprobar si el $0 lo sirve igual
  y moverlo libera cuota de criterio.
- Modelos publicados «for preview and playground use only» (su página lo dice: «no API key
  will authorize it») no son cableables aunque el id exista.

## Calibración medida (orden de magnitud; re-sondear antes de citar)

| modelo | 1ª respuesta | trampa 20/3 | tools ×3 | visión |
|---|---|---|---|---|
| `google/diffusiongemma-26b-a4b-it` | ~0,5 s | acierta en ~0,4 s | 3/3 | panel: 3/3 cifras en ~0,8 s |
| `nvidia/nemotron-3.5-bolt-e4b` | ~0,4 s | falla (dio 16) | 3/3 | texto: sí |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | ~0,6 s | acierta en ~3,8 s | 3/3 | n/d |
| `nvidia/nemotron-3.5-lightning-30b-a3b` | ~1,1 s | acierta solo con ≥1,7 k tokens de razonamiento | 3/3 | sí |
| `nvidia/nemotron-3.5-super-vl-120b-a12b` | ~0,8 s | acierta en ~11 s | 3/3 | panel: 2 332 ms con error de fila |
| `nvidia/nemotron-3-ultra-550b-a55b` | ~1,0 s | acierta (20/3) en ~10 s | 3/3 | n/d |
| `z-ai/glm-5.3-flash` | 80 s frío / ~0,8 s caliente | n/d | n/d | n/d |
| `deepseek-ai/deepseek-v4.1-flash` | ~159 s | n/d | n/d | n/d |
| `openai/gpt-oss-20b` | ~142 s | n/d | n/d | n/d |
| `mistralai/mistral-large-4-1t-a52b` | 42 s frío / 0,8 s caliente | timeout 300 s con 6 k | n/d | n/d |
| `poolside/laguna-xs-2.1` | ~0,4 s | falla (dio 20) | 3/3 | 400 no multimodal |

Los de arranque de dos minutos (deepseek, gpt-oss) siguen vivos: sirven para
lote nocturno, nunca para un turno interactivo. Un alias en el proxy que los redirija a un
modelo rápido convierte una latencia en una mentira de identidad — y si ese alias apunta a un
modelo ya retirado, convierte un 404 en un 200 falso.
