# OpenCode Go — estructura real de límites y precios

Los precios y topes cambian: **verificar contra la sección «Usage limits» de la página
oficial del plan** antes de usarlos en un informe o de codificarlos en un medidor. Este
fichero fija la ESTRUCTURA (lo que no cambia) y da una foto de referencia de las cifras.

## 1. La regla que casi nadie declara: ventanas encadenadas

No son tres topes independientes. El límite mensual del modelo es la base y las otras
dos ventanas son porcentajes de él:

- 5 horas = **20 %** del mensual
- Semanal = **50 %** del mensual
- Mensual = **100 %**

Consecuencia práctica: un medidor que compare cada ventana contra su propio campo del
SSOT acierta solo si esos campos ya respetan 20/50/100. Si alguien los escribe a mano
inconsistentes, el medidor miente en la ventana corta — que es justo la que provoca el
corte de servicio. Deducir el tope de 5 h desde el mensual, no confiar en el campo.

## 2. Cómo se factura (y por qué el `cost` plano engaña)

Cada respuesta trae `usage.opencode` con:

- `list_cost` — precio de lista del consumo de esa llamada
- `allowance` — cuánto contó realmente contra la asignación

El múltiplo `allowance ÷ list_cost` **varía por modelo**, y ese cociente es la métrica de
valor del plan: a 4× el modelo gasta cuatro veces más asignación que su precio de lista;
a 1× gasta lo mismo que lista. Medido con sondas de 4–8 tokens en el plan Go:

| Múltiplo | Modelos observados |
|---|---|
| 1× (mejor valor) | GLM-5.2, GLM-5.3-Flash, Hy3, Hy4, LongCat-2.0, MiMo-V2.6-Flash, MiniMax M3, Qwen3.7 Plus, Kimi K2.7 Code |
| 2× | Gemini 4 Argon, Qwen3.8 Flash, Hy4 preview |
| 3× | MiniMax M3.1 Flash |
| 4× (más caro en cuota) | Kimi K3, Kimi K3.1 Pro, Claude Haiku 5.5, GLM-5.3, DeepSeek V4 Pro, Qwen3.8 Max, Step 5 Preview, MiMo-V2.6-Pro |
| <1× | DeepSeek V4.1 Flash (el ×2 de peak ya va dentro de `list_cost`) |

Re-medir, no memorizar: el cociente sale de la propia respuesta de cada sonda. El campo
`usage.cost` plano llega a **0** en todas las respuestas: nunca es la fuente de gasto.

Los metadatos de sesión que el cliente guarda en disco (historial de mensajes) suelen
conservar `cost` y `tokens`, pero **no** el bloque `usage.opencode`: el `allowance` no se
persiste. Consecuencia: un medidor que reconstruya el gasto desde el historial local solo
es exacto para el tráfico posterior a empezar a registrar `allowance` al vuelo; para el
histórico previo hay que estimar con la tarifa oficial, y **declarar la cobertura** en el
informe en vez de presentar la estimación como medición. Verificar qué campos guarda el
historial antes de prometer exactitud retroactiva.

## 3. Precio dual por hora

DeepSeek V4.1 Flash y V4 Pro (y otros) tienen dos tarifas:

- **Peak**: 01:00–04:00 y 06:00–10:00 UTC, de lunes a viernes
- **Off-peak**: todo lo demás, incluidos los fines de semana
- El precio peak es el **doble** del off-peak

Una tarifa medida de noche no describe el día. Si el medidor guarda una sola tarifa por
modelo, el gasto real de un lote ejecutado en peak aparece a la mitad.

## 4. Topes mensuales por modelo (plan Go, referencia)

| Modelo | Mensual | Notas |
|---|---:|---|
| DeepSeek V4.1 Flash | $100 | el mayor; precio dual peak/off-peak |
| DeepSeek V4 Pro | $15 | precio dual |
| GLM-5.3-Flash / GLM-5.2 | $60 | 1× en cuota |
| GLM-5.3 | $15 | 4× en cuota: el nombre no hereda el cupo del Flash |
| Kimi K3 / K3.1 Pro | $15 | 4×; input/output caros + escritura de caché |
| Kimi K2.7 Code | $60 | 1× |
| MiniMax M3 (≤512K) / M3.1 Flash | $60 / $20 | M3 sube de precio por encima de 512K |
| Qwen3.8 Max / Qwen3.8 Flash / Qwen3.7 Plus | $15 / $30 / $60 | |
| Gemini 4 Argon | $30 | 2×; 50 % de descuento hasta 2026-11-30, el 1-dic el list se duplica |
| Claude Haiku 5.5 / Step 5 Preview / MiMo-V2.6-Pro | $15 | 4× |
| MiMo-V2.6-Flash / Hy3 / Hy4 / LongCat-2.0 | $60 (Hy4 preview $30) | 1× |
| Beam Free / Iceman Contributor Free | ilimitado | gratis temporal; Beam bloqueado por región (Venezuela incluida); Iceman exige consentir entrenamiento |

Planes: Go ($10/mes), Go Plus ($40/mes, mismos modelos con más cupo), Go Teams.
Los topes son **por modelo**, no por cuenta: agotar uno no afecta a los demás.

## 5. Endpoints y cabeceras

- Chat compatible OpenAI: `https://opencode.ai/inference/go/openai/v1/chat/completions`
- Estilo Anthropic: `.../go/anthropic/v1/messages` (MiniMax M3, Qwen, Claude Haiku)
- Estilo Google: `.../go/google/v1beta/models/<id>` (Gemini 4 Argon)
- Responses API: `.../go/openai/v1/responses` (Grok, GPT Luna, Muse Spark)
- Catálogo: `GET https://opencode.ai/inference/go/v1/models`
- Consumo: `GET https://opencode.ai/inference/go/v1/usage` (idéntico en
  `https://opencode.ai/zen/go/v1/usage`; ambas rutas responden 200 con la misma clave)

El endpoint de consumo devuelve las tres ventanas ya calculadas, y es la única lectura
directa del estado del plan — no hace falta la consola ni reconstruir desde el historial
del cliente:

```json
{"usage":{"rolling":{"status":"ok","percent":3,"resetsAt":"…"},
          "weekly":{"percent":24,"resetsAt":"…"},
          "monthly":{"percent":45,"resetsAt":"…"}}}
```

`resetsAt` del mensual da el inicio del ciclo (reset − 1 mes) y por tanto el ritmo:
45 % en 14 días = 3,2 %/día → se agota justo en el reset. Ese cociente, no el importe
absoluto, es lo que justifica subir a Go Plus.

Cabeceras obligatorias para que el gateway rutee y cachee bien:

- `x-opencode-session: <id estable por conversación>` — sin ella: `400 MissingSessionID`
- `User-Agent` que identifique al cliente; un UA genérico de librería HTTP recibe `403
error code: 1010` de Cloudflare, que parece caída del proveedor y no lo es.

Un modelo puede estar en el catálogo y no servirse en ese endpoint (`400 Model is
unavailable`): catálogo ≠ disponibilidad, también aquí.

## 6. Región

Hay modelos gratuitos bloqueados por país (Beam Free entre ellos, con Venezuela en la
lista). El síntoma es `403 RegionError`, que **no** es fallo de credencial ni del
modelo: es política de región y no se arregla reintentando.

Firmas distintas, misma causa, y cada una apunta a un upstream diferente:

| Cuerpo del 403 | Quién bloquea |
|---|---|
| `unsupported_country_region_territory` | upstream OpenAI (GPT Luna) |
| `RegionError: This model is not available in your country` | Meta (Muse Spark) y Beam/Crouton |
| `Upstream request failed: Endpoint is unavailable` | Grok |

En un plan de suscripción el bloqueo es **por modelo, no por plan**: el catálogo anuncia
treinta modelos y desde una región sancionada sirven veinte. La matriz de routing se
construye con los que responden 200, nunca con la lista del plan.

## 7. Matriz de routing por múltiplo (cómo elegir default)

| Necesidad | Candidatos |
|---|---|
| Volumen, tareas de agente baratas | `deepseek-v4.1-flash` (y en off-peak, mitad de precio), GLM-5.3-Flash, Hy3, LongCat-2.0, MiMo-V2.6-Flash |
| Visión / imágenes / contexto gigante | Gemini 4 Argon (2×, 1.05M, hasta el 30-nov), Qwen3.7 Plus, Hy4 |
| Precisión alta, se paga el 4× | Kimi K3.1 Pro, Claude Haiku 5.5, GLM-5.3, Qwen3.8 Max |
| Auxiliares (títulos, compresión, review) | un 1× vivo: GLM-5.3-Flash o DeepSeek V4.1 Flash — nunca un ID delistado |

Regla de decisión: el default de un harness es un modelo de múltiplo 1× con contexto
suficiente; los 4× se reservan para lo que exige precisión, porque agotan la asignación
mensual del plan en una cuarta parte del trabajo.

## 8. Gobernar el default según el consumo (no congelarlo a mano)

La asignación es **mensual y no se acumula**: lo que no se consume se pierde, así que
gastarla cerca del 100 % antes del reset es lo óptimo y el riesgo real es agotarla antes
de tiempo. De ahí la consecuencia que se equivoca la mitad de las veces: **migrar todo a
los proveedores gratuitos no ahorra, desperdicia lo ya pagado.** Lo que corresponde es
que lo gratuito absorba volumen y el plan pague criterio, visión y contexto largo.

Escalones con los umbrales de la matriz (`soft_throttle` / `hard_stop`), recalculados por
un gobernador en cron, no elegidos a ojo:

| Escalón | Disparo | Default | Go queda para |
|---|---|---|---|
| normal | < 65 % | modelo 1× del plan | todo el trabajo de criterio |
| ahorro | < 80 % | igual | + volumen y auxiliares migrados a gratis |
| degradado | < 95 % | motor gratuito | visión, contexto >200k, R3 |
| gratis | ≥ 95 % | motor gratuito | solo turno humano explícito |

El gobernador es idempotente: lee el % del endpoint de consumo, deriva el escalón,
reescribe `default_model`/`architect_model`/`small_model` en el SSOT con backup previo y
no escribe si el valor ya coincide. Corre en el mismo cron que el medidor, de modo que la
degradación es automática y queda registrada en el fichero de estado del arnés.
