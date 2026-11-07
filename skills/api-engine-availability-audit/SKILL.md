---
name: api-engine-availability-audit
description: "Use when checking if routing-chain engines really serve."
version: 1.0.2
author: HermesHP15
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [harness, routing, providers, canary, observability]
    related_skills: [blocked-page-recovery, systematic-debugging, f-harness]
---

# Auditoría de disponibilidad de motores (routing chain)

Clase de tarea: decidir si los motores de una cadena de routing (proveedores LLM,
gateways, fallbacks) **sirven de verdad**. Responde a "¿esto funciona?" con llamadas
reales, no con configuración, catálogo ni documentación.

Regla central: **configurado ≠ catalogado ≠ servido.** Cada una se prueba distinto y
colapsarlas produce informes falsos en las dos direcciones (motores vivos declarados
muertos; motores muertos avalados por un `exit 0`).

Responder en el idioma del usuario (español por defecto en este entorno).

## When to Use

- El usuario pide **evaluar, auditar o diagnosticar** el harness o una cadena de
  motores, o pregunta "¿esto funciona?" sobre proveedores/fallbacks.
- Un motor no responde, o un fallback parece caído, y hay que decidir si retirarlo.
- Hay que contrastar lo que **dice** la configuración con lo que **sirve** el endpoint.
- Se sospecha un alias de identidad o una cuota declarada sin control real.

No usar para leer páginas web bloqueadas (eso es `blocked-page-recovery`) ni para
descomponer proyectos (`f-orquestador-floydia`).

## Procedimiento

1. **Leer el SSOT para el ESTADO; la documentación oficial para los LÍMITES.** Localizar el fichero de cadena/modo y el de
   configuración del cliente (`harness_mode.json`, `config.yaml`, `opencode.jsonc`) y
   sacar de ahí versión, motor por defecto y orden real de motores. Cualquier cifra
   escrita en un skill viejo es contexto, no verdad. El SSOT manda sobre qué motor va
   dónde; **no** sobre cuánto cuesta ni cuánto se puede usar: eso se lee en la página
   de límites del proveedor antes de afirmar un número.
2. **Pase pasivo primero (estructura).** Doctor/validador de configuración: refs,
   cabeceras, rutas. Sirve para detectar config rota — **no** para concluir
   disponibilidad. Un validador en verde convive sin problema con un motor muerto en
   cadena; si el informe no separa ambos ejes, está mintiendo.
3. **Pre-flight de infraestructura local.** Proxy/gateway propio: `curl -s
   :PUERTO/health` y mirar cuentas disponibles y cooldowns. Si el proxy no está, el
   fallo es del proxy, no del proveedor. Si el proxy corre en un venv, el gestor que lo
   reinicia debe resolver ese intérprete: lanzarlo con el `python3` del sistema puede
   arrancar sin sus dependencias y dejar el puerto vacío aunque el `start` imprima OK —
   verifica `/health` (y su `uptime_s`) en una llamada aparte, y que el daemon detecte el
   venv en vez de asumir `python3`.
4. **Canario activo:** una llamada de inferencia real por motor (`max_tokens`
   pequeño, p.ej. 8–16). Registrar por motor: status HTTP crudo, **modelo servido en
   la respuesta**, latencia y motivo del fallo. El modelo servido es la única prueba
   de identidad.
5. **Clasificar el fallo antes de creerlo** (tabla de abajo). Un veredicto de
   "muerto" exige descartar las causas de falso negativo.
6. **Alias:** si el modelo servido difiere del pedido, es sospecha, no conclusión:
   sonda de capacidad con respuesta conocida (p.ej. imagen con texto legible → pedir
   que lo lea) antes de retirar el motor por pérdida funcional.
7. **Dos confirmaciones negativas separadas** (idealmente con minutos de diferencia)
   antes de retirar un motor. `410 Gone` es tombstone definitivo y no necesita
   segunda. Un `404` aislado no decide.
8. **Pase de gobierno:** cada cuota/tope declarado en el fichero de cadena
   (`monthly_allowance_usd`, `window_5h_cap_usd`, `weekly_cap_usd`, límites diarios)
   debe tener un **lector en runtime**: `grep -rn <campo> SCRIPTS/` y descartar
   matches de tests, `scratch/` o documentación. Sin lector, el tope es decorativo →
   se reporta como brecha, nunca como control existente. El mismo criterio vale para la
   cadena de fallback y los slots auxiliares: si la clave está mal nombrada, el runtime
   no la lee y el control no existe. Se comprueba buscando el nombre de la clave con
   `search_files` en el código del cliente, no leyendo su documentación ni el propio config.
9. **Consumo real de la suscripción, no del historial local.** Si el proveedor expone
   ventanas de cuota, pedirlas a su endpoint de introspección en vez de reconstruirlas
   desde logs o bases del cliente. En OpenCode Go: `GET .../v1/usage` →
   `{"usage":{"rolling"|"weekly"|"monthly":{"percent","resetsAt"}}}`. De ahí sale el
   ritmo: % consumido ÷ días transcurridos desde el reset, y con eso si el cupo se agota
   antes o después del cierre del ciclo (y si toca subir de plan). Es una medición, no
   una sonda: no se deduce del precio ni del número de peticiones.
10. **Cerrar con contrato de salida** y **dejar constancia fuera del chat**: veredicto en
   una línea · lista por motor con
   estado y latencia medida · defectos reales con HTTP exacto y sus dos
   confirmaciones · brechas de gobierno · decisiones abiertas para el operador.
   Después, persistir lo aprendido en el sistema de memoria del proyecto —nota de
   journal con una sección por hallazgo, puntero en el índice/handoff vigente y
   evento append-only en el ledger— porque los demás agentes del entorno leen esos
   ficheros, no la conversación. Un cierre que solo existe en el chat se pierde para el
   siguiente agente, que repetirá la auditoría desde cero.
   Si el usuario pide **solo el plan** («no hagas nada, preséntame un plan»), no se
   escribe ningún artefacto: entrega el plan en bloques numerados con una recomendación
   explícita y el orden de ejecución, y deja el cierre documental para cuando apruebe.

## Taxonomía del fallo (no todos los errores significan lo mismo)

| Señal | Significado | Acción |
|---|---|---|
| `403` + cuerpo `error code: 1010` (Cloudflare) | Baneo por **firma de cliente** (UA de `Python-urllib`, TLS), no caída del proveedor | Reintentar con User-Agent de navegador antes de emitir cualquier veredicto |
| `400` que nombra una cabecera ausente (p.ej. sesión de gateway) | Bug del cliente, la clave es válida | Añadir la cabecera que el mensaje pide |
| `400` «This model trains on request data… turn on Allow paid endpoints» | **Puerta de privacidad** de la cuenta (consentimiento de entrenamiento), no caída ni falta de cupo | Activar el permiso en la consola o excluir el modelo; no retirarlo ni contarlo como muerto |
| `403` `unsupported_country_region_territory` · `RegionError` · «Endpoint is unavailable» dentro de un catálogo de suscripción | Bloqueo **geográfico del upstream** del modelo (quien lo sirve), aunque el plan lo anuncie como incluido | Clasificar «bloqueado por región», sacarlo de la matriz de routing y no presentarlo como disponible |
| `404` en `/models` | El gateway puede no exponer catálogo y servir igual `/chat/completions` | Probar inferencia; el catálogo no decide |
| `404` en `/chat/completions` con modelo concreto | El MODELO no existe en ese proveedor | Corregir ID o retirar; no es fallo de credencial |
| `401/402/403` de credencial | Credencial rechazada o sin saldo | Veredicto, sin reintentos ciegos |
| `402` con umbral de saldo (`requires at least $X in balance for <modalidad>`) | **Puerta de facturación por modalidad**, no falta de capacidad: el modelo existe y la cuenta responde, pero esa salida (imagen, vídeo) exige un saldo mínimo | Registrar el umbral y el saldo real; no retirar el motor ni concluir "no existe" |
| `429` | Estado de cuota, no caída — **salvo que el cuerpo diga `overloaded` / `over capacity`**: entonces es saturación del upstream para ESE modelo | Si nombra cuota/crédito: cooldown. Si dice `overloaded`: sondear un hermano del mismo plan antes de tocar nada — en el mismo minuto `v4-pro` respondió 200 mientras `v4.1-flash` daba 429, y ese contraste prueba que es el modelo, no la cuenta |
| `5xx` con cuerpo de sobrecarga (`503 Service temporarily overloaded`) | El upstream está saturado para ESE modelo; transitorio | Veredicto `DEGRADADO`, no `MUERTO`: reintentar en la siguiente pasada y no retirar el motor |
| Timeout | El motor no completa | Tratar como transitorio (`DEGRADADO`); registrar aparte, no confundir con rechazo |

## Pitfalls (mecanismo + regla)

- **El `else` del prober es el bug más caro.** Si un tipo de motor sin rama explícita
  cae en un proveedor por defecto, la sonda prueba el endpoint equivocado y produce
  muertes en bloque. Marcar `VACIO`/no verificado, nunca enrutar a ciegas.
- **User-Agent de navegador en toda sonda HTTP a proveedores con CDN.** Cloudflare
  banea `Python-urllib/*` con `1010`; sin UA el informe acusa al motor de un fallo del
  cliente.
- **Cabeceras propias del gateway.** Cada gateway con auth propio añade su handshake
  (cabecera de sesión, de proyecto, de versión). Deducirla del mensaje de error, no
  adivinarla.
- **No colapsar excepciones en una etiqueta.** Convertir todo en `"HTTPError"` borra
  `400/403/404/429`, que llevan acciones distintas. El status crudo va al artefacto y
  al informe.
- **No inferir capacidad de un string.** Un proxy puede reescribir el ID
  (`x-vl-120b` → `x-120b`); el nombre servido no prueba que se perdió la visión. Sonda
  de capacidad con respuesta verificable.
- **Si el veredicto elige motor por defecto, medir `tool_calls`, no solo latencia.**
  Un 200 rápido no significa que sirva de agente: en el mismo barrido, dos proveedores
  gratis contestaron en 400-500 ms y devolvieron **0/3** `tool_calls` con una función
  trivial (sirven para texto y análisis, nunca como motor de un arnés), mientras otro
  tardaba el triple y llamaba 3/3. El error inverso también muerde: un modelo que en
  producción usa herramientas sin problema dio 1/3 en una sonda de prompt mínimo, así que
  un `tools=False` aislado no retira un motor — repetir 3 veces y contrastar con uso real.
  La prueba se hace con `tools` + `tool_choice: auto` y se cuenta la presencia de
  `message.tool_calls`, nunca el texto de la respuesta.
- **Un validador que dice "sin credenciales" puede estar leyendo una línea comentada.**
  El chequeo de credenciales del cliente busca un nombre de variable concreto en su
  `.env`; si esa línea está comentada (`# PROVEEDOR_API_KEY=…`) o la clave vive en el
  `.env` de otro proyecto, el validador falla mientras el motor responde por otra vía.
  Contrasta siempre con una llamada real al proveedor antes de reportar credencial
  ausente, y revisa el patrón `^#\s*<NOMBRE>_API_KEY` en el fichero que el cliente lee
  (no el del proyecto). Un falso negativo de credenciales envenena el resto del informe.
- **Un canario defectuoso invalida el informe.** Si a mitad de auditoría se descubre
  que el prober miente: repararlo (R1), re-ejecutar y **declarar inválido** el
  veredicto anterior. No matizarlo ni publicarlo con nota al pie.
- **Endpoints de introspección cambian de versión.** Verificar la ruta antes de
  confiar (p.ej. OpenRouter responde en `/api/v1/auth/key`; `/api/v2/auth/key` → 404).
  Un 404 de ruta no es una caída del proveedor.
- **La ruta de inferencia de un gateway de suscripción se copia del cliente que ya
  funciona, no se compone.** `…/inference/go/v1/chat/completions` devuelve `400 Bad
  Request` mientras `…/inference/go/openai/v1/chat/completions` responde 200: el 400
  parece payload inválido y no lo es. Antes de depurar el body, saca la URL de un
  cliente probado (el bench o el catálogo del provider en `opencode.jsonc`), no del
  dominio del proveedor.
- **Un renombrador alimentado por un campo sin medir produce gramática mixta — se resuelve con un `?` explícito, nunca aplicando a medias.** Si el nombre se deriva del registro (`[ESTADO][CTX][MODO]`) y `ctx_real` es `null` para la mayoría, aplicar sólo el subconjunto medido deja dos gramáticas en el catálogo y el lint ya no distingue lo viejo de lo nuevo. Procedimiento que sí cierra: (1) rellenar `ctx_real` desde los catálogos que publican límite (`limit.context` del de suscripción, `context_length` de OpenRouter); (2) etiquetar `[?]` lo que no publica nada y hacer que el lint acepte `?` **sólo** cuando `ctx_real` es null; (3) comparar por **etiqueta normalizada**, no por cifras (1 000 000 y 1 048 576 son `1M`; 262 144 es `256k` ÷1024; 200 000 es `200k` ÷1000) — comparar números crudos inventa hallazgos; (4) al reescribir el nombre, purgar en el mismo cambio el `limit.context` declarado que contradice al catálogo; (5) contar duplicados **por proveedor**: el mismo id en `google_c2…c6` es legítimo.
- **Nada corre solo.** Comprobar si el diagnóstico está programado (cron, systemd
  timer). Un canario roto que sobrevive semanas es la prueba de que solo se ejecuta a
  mano: proponer la programación como parte del arreglo. En un host SysVinit
  `systemctl list-timers` no existe: el planificador se comprueba con `pgrep -a cron` y
  `crontab -l`, y una entrada cuyo fichero de log no existe **nunca ha disparado** — la
  programación se valida esperando el siguiente tick y viendo el log, no leyendo la
  crontab.
- **Un `cost` en 0 no significa gratis.** Los gateways de suscripción devuelven el
  coste facturable en 0 y el precio real en un bloque anidado de `usage` (p.ej.
  `usage.opencode.list_cost` / `.allowance`). Antes de concluir "no hay gasto",
  inspeccionar las claves del objeto `usage` completo; el campo plano miente.
- **El múltiplo `allowance ÷ list_cost` es POR MODELO: medirlo, no extrapolarlo.** En el
  mismo plan conviven modelos a 1×, 2×, 3× y 4×. Un modelo a 4× consume cuota cuatro
  veces más rápido que su precio de lista, así que el «más barato por token» puede ser el
  que agote la asignación primero. Calcular el cociente en la respuesta de cada sonda
  antes de recomendar un modelo por defecto; generalizarlo desde un solo modelo produce
  informes de gasto con error de 4×. Detalle y tabla: `references/opencode-go-plan-limits.md`.
- **El catálogo del cliente no es el catálogo del proveedor.** El cliente trae una lista
  curada en el código (`models_catalog_static.py` y equivalentes) que envejece en las dos
  direcciones: sigue ofreciendo IDs retirados y no conoce los nuevos. Autoridad =
  `GET <base_url>/v1/models` del endpoint que se va a usar; la lista curada solo sirve
  para saber qué se ofreció antes. Y un ID en el catálogo no garantiza que se sirva:
  `400 Model is unavailable` es delistado, no credencial.
- **El modelo auxiliar por defecto puede estar delistado, y cada tarea auxiliar lo paga.**
  Los perfiles de proveedor traen un modelo barato hardcodeado para títulos, compresión,
  resúmenes, review o descomposición de tareas. Si ese ID murió, cada llamada auxiliar
  gasta un `400 Model is unavailable` antes de caer al modelo principal: cuota consumida
  sin trabajo útil y telemetría de fallback ruidosa. Tras la auditoría, sondear también
  ese auxiliar y fijarlo a un modelo vivo de múltiplo 1×.
- **Qué endpoint está realmente en uso se lee en el log, no en el config.** Un fichero de
  configuración puede declarar su propio bloque de proveedor con una `base_url`, mientras
  el cliente resuelve el perfil interno con otra, y ambas responden igual. Atribuir el
  informe al endpoint del config sin comprobarlo invalida las conclusiones sobre latencia
  y ruteo: `grep -o 'https://<host>/[a-z0-9/._-]*' <agent.log> | sort | uniq -c` da la URL
  que de verdad se está usando.
- **Un `usage: null` en la respuesta no significa gratis: las tarifas planas viven
  fuera de `pricing.prompt`.** Hay modelos que cobran por petición o por herramienta y
  no lo declaran en el precio por token: en OpenRouter, `perplexity/sonar-deep-research`
  cobró **$0.286 por una sonda de 24 tokens**, y `sonar-pro-search` añade
  `pricing.web_search = $0.018` por llamada. Antes de sondear en bloque, listar las
  claves del objeto `pricing` (`prompt`, `completion`, `request`, `web_search`, `image`,
  `audio`, `input_cache_read`) y **excluir del barrido** todo modelo con tarifa por
  petición o herramienta; si hay que probarlo, hacerlo individualmente y con el saldo
  contado. Un barrido de 450 modelos "de prueba" puede costar dólares por este agujero.
- **Falsar la creencia "modelos de pago que en realidad son gratis" con saldo a cero.**
  El método no es leer el catálogo ni buscar promos: es vaciar (o esperar a vaciar) el
  saldo, confirmar el `402 Insufficient credits`, y **re-sondear todos los que antes
  cobraron**. Si alguno responde 200 con saldo 0, es gratis de facto; si todos dan 402,
  la creencia queda falsada con evidencia dura. En OpenRouter los gratis son entradas de
  catálogo con `pricing.prompt` y `pricing.completion` en 0 **publicados**; `:free` en el id
  es una convención de marketing, no el discriminador: hay ids sin sufijo con precio 0 y
  `:free` en el nombre que ya no son gratuitos. Clasificar SIEMPRE por los campos de
  `pricing` (+ `supported_parameters` para tools), nunca por el sufijo — un filtro por
  `':free' in id` produjo un falso negativo que se publicó como «ese modelo no existe».
- **`GET /api/v1/generation?id=<gen-...>` es la lectura independiente del coste, pero
  el mismo URL responde 200 por `curl` y 404 por `urllib`.** Cuando el importe no
  aparece en `usage.cost`, verificarlo con `curl` antes de declarar el modelo gratis: el
  404 aislado es del cliente, no del endpoint (misma trampa que `/api/v2/auth/key`).
- **El bloqueo geográfico es la causa de "muerto" más fácil de confundir con caída.**
  Desde Venezuela, 21 modelos del catálogo OpenRouter (todo `x-ai/grok`, `openai/gpt-5-pro`,
  `o3*`, `gpt-4o*`, `meta/muse-*`, `stealth/*`) devuelven 403 con cuerpo
  `This model is not available in your region`. No es cuota ni credencial: es región.
  Clasificarlo aparte y proponer salida por proxy de otro país, no retirar el motor.
- **Un endpoint gratis puede tardar 80-160 s en la PRIMERA llamada de cada cuenta y modelo, y devolver 200 igual.** Medido en NVIDIA NIM (2026-11-06): `deepseek-v4.1-flash` 159 s, `gpt-oss-20b` 141 s, `glm-5.3-flash` 80,6 s con `max_tokens=16`; la misma llama en el mismo minuto por el proxy ya caliente contestó en 0,84 s. Una sonda con timeout de 30-90 s los declaró muertos en tres auditorías seguidas. Regla: ante un timeout de motor gratis, **no** emitir veredicto — repetir con `read` de 240-300 s o lanzar la segunda llamada de la misma cuenta; solo el fallo que persiste tras dos esperas largas es caída. Y si el motor entra en producción, su perfil de timeout debe cubrir el arranque en frío (≥90 s), no el caso caliente.
- **Los modelos de razonamiento gratis agotan `max_tokens` en el pensamiento y devuelven
  `content: ""`.** Un bench con `max_tokens=700` marcó como fallidos a Nemotron, Flint y
  Dots cuando en realidad respondieron bien con 4000. Antes de puntuar, comprobar
  `completion_tokens_details.reasoning_tokens == max_tokens`: si coincide, la respuesta
  está truncada, no equivocada.
  El corolario de diseño muerde más fuerte: **un razonador no sirve para un slot de salida
  corta** (título, compresión, triage, voz). Medido con el `max_tokens` real del slot: 60 y
  150 → `finish=length` y `content: ""`; subirlo a 400 → el proxy devuelve 429 «circuit
  breaker: repetitive» por bucle de pensamiento. Por eso un slot auxiliar se prueba con **su**
  presupuesto de salida, no con el del bench, y el reparto es razonador sólo donde decide
  (decomposición, juicio, review) + modelo pequeño no-razonador donde sólo formatea. Tabla,
  payload y umbrales: `references/model-slot-assignment.md`.
- **Un evaluador que solo busca decimales condena a los modelos que contestan en
  fracción.** A la trampa de velocidades relativas (respuesta 160/3 = 53,33) varios
  modelos gratis respondieron `160/3`: correcto, pero `\d+\.\d+` no lo encuentra y los
  marca falsos. Aceptar fracciones en el scorer o el informe acusará al modelo correcto.
- **El veto de sondas va ANTES de la petición, no en el filtro del informe.** Si ya sabes
  que una familia cobra por petición, el arreglo no es "excluirla al analizar" sino
  bloquearla en el chokepoint: una lista de patrones con motivo medido, más un veto
  dinámico por catálogo (`request`/`web_search`/`image`/`audio` > 0), chequeados antes de
  construir el payload. El post-flight de coste **no** protege de estos cargos, así que
  la capa de coste no sustituye al veto. Verificado con un id sintácticamente válido
  (`perplexity/sonar:free`): pasa la validación de forma y lo corta la de veto — ese es el
  caso de prueba que demuestra que la capa está puesta y en el orden correcto.
- **Un barrido programado de un catálogo entero no puede incluir los de pago, y el
  veredicto no puede ser "respondió".** El cron filtra por catálogo (`pricing` 0 y sin
  tarifas planas) y compara contra su propio estado: **ROJO** solo si un modelo que antes
  respondía ahora falla en duro o desaparece; **AMARILLO** si el transitorio se repite N
  pasadas; **VERDE** (silencio) si no hay regresión. Un modelo gratis nuevo que falla no
  alerta: nunca funcionó, no es una regresión. Sin esa comparación contra el estado previo
  el vigilante avisa cada día de las mismas bajas conocidas y el operador lo ignora.
- **Nunca derives el precio de un modelo por parecido de nombre.** `x-4-pro` no
  hereda el precio de `x-4-flash`: la línea de nombre solo coincide en el prefijo y
  el error de un orden de magnitud pasa desapercibido. Autoridad de precio, en este
  orden: medición del propio endpoint > muestras propias del proveedor > proxy
  declarado como tal. Si usas proxy, márcalo y **degrada el veredicto**: con precio
  prestado el máximo imputable es "aviso", nunca "excedido".
- **No reconfigures la cadena para sondear facturación.** Cambiar el SSOT de routing
  para lanzar una sonda convierte una medición en una caída: si el proceso muere entre
  aplicar y restaurar, la cadena queda degradada. Una sonda es una llamada HTTP
  directa con las cabeceras correctas. Si aun así hay que tocar el SSOT, restaurar en
  el mismo `try/finally`, nunca en un paso posterior.
- **Los topes y precios se leen en la documentación del proveedor; no se deducen de
  sondas.** Una sonda te da el coste efectivo de esa llamada, no la estructura: no
  revela si las ventanas están encadenadas (p.ej. 5 h = 20 % del mensual y semana =
  50 %, en vez de tres topes independientes), ni si hay tarifa horaria peak/off-peak
  al doble, ni el tope propio de cada modelo. Publicar topes deducidos es peor que no
  publicarlos: el medidor comparará contra un número inventado y el operador decidirá
  con él. Consulta la tabla oficial, guárdala, y usa la sonda solo para verificar la
  aritmética.
- **Tope declarado sin lector = medidor + cron, no un párrafo en el informe.** Cuando
  la auditoría detecta topes decorativos, el entregable de la sesión es el medidor que
  los lee y el trabajo programado que los vigila; dejar la brecha documentada y sin
  instrumentar la reproduce en la siguiente auditoría.
- **Programar el diagnóstico exige separar estados, no solo colores.** Tres niveles y
  no uno: **ROJO** = infraestructura caída o veredicto duro (motor inexistente,
  credencial rechazada) · **AMARILLO** = presupuesto alto **o fallo transitorio** (5xx,
  timeout, 429) · **VERDE** = silencio. Un 5xx que despierta al operador con "motor
  muerto" quema la confianza en las alertas: el operador retira un motor que solo estaba
  saturado. Alerta con dedupe por veredicto y TTL (corto para caída, largo para
  presupuesto). Escala un transitorio a ROJO solo si se repite en N pasadas consecutivas.
- **Un modelo saturado puede tumbar a los sanos por la política de reintentos.** Si el
  prober reintenta N veces repartiendo entre cuentas, cada `5xx` de un solo modelo quema
  el presupuesto de todas: aparecen `Circuit breaker: 5 fallos seguidos` y cooldowns en
  cuentas que servían bien, y el informe culpa a los motores equivocados. Antes de
  concluir, lee las estadísticas por cuenta del proxy (`ok`, `timeouts`, `errors`, `429`,
  `cooldown_reason`) y separa "el modelo falla" de "las cuentas se agotaron". Al
  repararlo, el arreglo es doble: **rama propia para `5xx` que NO penalice la cuenta**
  (no llames al `note_failure` del pool: el fallo no es suyo) y **tope de intentos
  específico** (2–3 con backoff corto, no el máximo global de reintentos). Penalizar la
  cuenta por un `5xx` del upstream es lo que convierte una saturación de un modelo en
  una caída de todo el pool. Y no
  aceptes `status: ok` + `available_accounts: N` como salud: un proxy puede declararse
  `ok` con `stats.ok` de 2 frente a 19 `errors` por cuenta y el monitor repetirá ese
  verde cada pocos segundos; el veredicto se emite cruzando los contadores, no el
  campo agregado.
- **La clasificación transitorio/duro tiene que viajar en el artefacto, no en la cabeza
  de quien lo lee.** El prober devuelve por motor un campo explícito de clasificación
  (`upstream_5xx` / `cuota_429` / `timeout_red` / `veredicto_duro`) y el informe separa
  dos listas: `muertos` y `degradados`. Si el resumen solo publica "N muertos", el
  consumidor aguas abajo (guardia, cron, alerta) no puede distinguir un motor retirado de
  uno saturado, y acabará despertando al operador por lo segundo.
- **Un banco de tareas fáciles no discrimina motores: mete una trampa verificable.** Con
  preguntas triviales dos modelos de tamaño muy distinto aciertan ambos y solo los separa
  la latencia, lo que empuja a elegir el más rápido como motor por defecto. Añade un caso
  de respuesta numérica comprobable con una trampa conocida (p. ej. velocidades
  relativas): el modelo pequeño contestó 180 donde son 120 en 249 ms; el grande acertó en
  9 s; el de pago acertó en 1,7 s. La latencia solo decide **entre motores que aciertan**;
  una respuesta rápida y falsa cuesta más que una lenta y buena. Antes de declarar
  superioridad por tamaño, cruza el resultado con el margen estadístico declarado (±15 pp
  en este entorno): 9 pp de diferencia no es evidencia, un fallo cualitativo sí.
- **Al reiniciar el motor que estás auditando, el patrón de `pkill` mata también a tu
  shell.** `pkill -f <nombre>.py` compara contra la línea de comandos de TODOS los
  procesos, incluida la de la orden que estás ejecutando: si tu comando contiene el
  nombre del proceso objetivo (`python3 -m py_compile <nombre>.py`, un `grep`, un `curl`
  al fichero), el reinicio te envía SIGTERM y la auditoría muere a mitad con `exit -15`
  sin mensaje. Invoca el gestor del servicio por su propio nombre de script y deja el
  reinicio en una llamada separada de la verificación.
- **Tras un reinicio del host, re-baselina antes de interpretar.** El primer canario
  después de un arranque corre con upstream frío y proxies que acaban de subir: un
  timeout ahí no es evidencia de caída. Comprueba arranque y uptime del proxy, repite la
  sonda del motor sospechoso 2–3 veces y solo entonces emite veredicto. Los artefactos
  publicados en un CDN externo siguen sirviendo durante el corte: úsalos como eje
  independiente en el informe, no como prueba de que el local está bien.

- **El nombre visible del modelo es una afirmación de capacidad que nadie verificó.** Un display
  name tipo `[1M-F-V] X 120B` puede declarar 1 M de contexto con `context: 262144` real y llevar el
  sufijo de visión sin que la visión esté probada. El routing por capacidad se calcula del tag, así
  que el nombre mal puesto enruta tareas de 1 M a un motor de 256k. Auditar tres cosas a la vez:
  `display name` ↔ `context` real ↔ capacidades medidas (tools/visión). Y si en el mismo sistema
  conviven dos gramáticas de nombre (una en el SSOT de routing, otra en el config del cliente, p. ej.
  `[1M-Go] Nombre (rol)` vs `[C7-128k-F] Nombre [Proveedor]`), elige una, documéntala y lintéala:
  dos gramáticas significa que ningún consumidor puede comparar nombres sin un mapa mental.
- **Antes de citar un presupuesto, cuenta cuántas cifras distintas circulan del mismo plan.** En una
  sola instalación convivían $170 («bolsa compartida» en la documentación), $60 ponderados/mes en el
  fichero de facturación y $1 320 en el SSOT de routing. Solo la cifra compatible con las ventanas
  (20/50/100 % → $12/$30/$60) era real; las otras eran artefactos aditivos (suma de allowances por
  modelo). Regla: enumera las fuentes, comprueba cuál cierra aritméticamente con las ventanas
  observadas y declara las demás como contradicción a purgar en el mismo cambio. Elegir la cifra más
  cómoda es financiar decisiones con un número inventado, y el informe siguiente la heredará. El arreglo es de código, no de prosa: el medidor lee la
  ventana compartida (`shared_windows_usd.mensual`) y **no suma** las carteras por modelo,
  que son el mismo tope normalizado repetido N veces (22 × $60 = $1 320, la cifra fantasma
  que publicaba el medidor anterior).

## Elegir el arnés, no solo auditarlo

Cuando la pregunta es «¿cuál es el mejor arnés con lo que tengo?», la auditoría es el
insumo, no el entregable. Tres reglas deciden el diseño:

1. **La cuota de suscripción no se acumula: gastarla ~100 % antes del reset es lo
   óptimo.** Migrar todo a gratis «por ahorrar» tira lo ya pagado. El riesgo real es
   agotarla antes de tiempo (% consumido ÷ días transcurridos × días restantes), no
   consumirla.
2. **Gratis absorbe volumen, el pago paga criterio.** Trivial/fondo/auxiliares → pool
   local $0; criterio, contexto largo, visión y R3 → suscripción. Un motor con
   `tool_calls` 0/N sirve para texto y análisis, nunca como motor de un arnés, por
   rápido que sea.
3. **La degradación se automatiza, no se recuerda.** Un gobernador que lee el % real de
   la cuenta y reescribe el SSOT de routing por escalones (p. ej. <65 % normal · <80 %
   volumen a $0 · <95 % default al pool gratis, pago reservado a visión/contexto/R3 ·
   ≥95 % congelado) convierte la política en comportamiento; con la cuota en runtime,
   los escalones son el único control que sobrevive a la sesión. Plantilla:
   `scripts/quota_governor.py`.

**Las fuentes de conocimiento del proyecto no son evidencia de disponibilidad.** Un
cuaderno (NotebookLM, vault, ranking de una sesión anterior) puede recomendar como motor
por defecto un id que ya murió — un `:free` cuya ventana cerró responde
`404 … the free launch period … ended on <fecha>`. Al cruzar fuentes, separa dos ejes:
*qué política* dice cada una (eso sí se hereda: reglas de QA visual, guard de coste,
prohibiciones de pago) y *qué endpoint* propone (eso se re-sonda antes de cablearlo). Si
el operador corrige una recomendación previa, la corrección manda y se verifica contra el
vault en vez de defenderse.

**Visión: el QA visual y el slot de visión son dos rutas distintas.** El QA sobre
capturas reales va por el puente CLI suscrito (`agy`/Antigravity, coste marginal $0,
latencia de decenas de segundos, nunca para bucle interactivo), y el slot
`auxiliary.vision` del cliente va a un modelo VL del pool local $0 (~0,6-1,1 s medido con
canario) con un multimodal de pago como respaldo. Un modelo multimodal premium (múltiplo
2×, con subida de precio anunciada) no es opción por defecto para visión: cuesta cuota y
latencia sin mejorar la lectura del canario.

## Instancia conocida: Harness FloydIA ($0.00 / allowance)

Raíz canónica del proyecto: `<PROYECTO>` (los comandos con
rutas relativas solo resuelven desde ahí).

```bash
cd <PROYECTO>
cat harness_mode.json                                     # SSOT: versión, modo, default_model, execution_chain
curl -s http://127.0.0.1:8088/health                      # proxy NIM (4 cuentas rotativas)
python3 SCRIPTS/harness_doctor.py                         # pasivo: estructura, NO disponibilidad
python3 SCRIPTS/harness_api_scan.py --canary              # canario de identidad (llamada real por motor)
```

Notas de la instancia: OpenCode Go exige `x-opencode-session` (sin ella, `400
MissingSessionID`); el proxy NIM reescribe IDs y sirve variantes equivalentes (un alias
con `vl` puede seguir leyendo imágenes — verificado con sonda de imagen); valores fuera
de la cadena activa (regiones bloqueadas, modelos retirados) no son defectos hasta que
se demuestre lo contrario. Si el canario del harness vuelve a declarar muertes en
bloque, revisar primero las ramas por `kind`, el UA y las cabeceras antes de retirar un
solo motor.

Para contenido web bloqueado (no motores) usar `blocked-page-recovery`; para el
control del harness FloydIA (modos, cadenas, workflow) usar `f-harness`.

Cuando el paso 8 del procedimiento encuentra una asignación prepago sin control,
la receta completa (fuente de verdad del consumo, dos cifras, niveles de confianza de
la tarifa y sonda de calibración) está en `references/allowance-accounting.md`.
Los límites, topes por modelo y precios publicados del plan que usa este harness, con
la regla de ventanas encadenadas y las tarifas peak/off-peak, están en
`references/opencode-go-plan-limits.md` — leer ese fichero **antes** de afirmar
cualquier cifra de cuota o coste. El reparto medido de razonador vs formateador por tipo de
slot (y cómo probar un slot con su propio `max_tokens`) está en
`references/model-slot-assignment.md`. El tier gratuito de NVIDIA NIM (límite oficial,
firmas de 404/410 que no significan lo mismo, arranque en frío y batería de sondas con
trampa aritmética y visión) está en `references/nvidia-nim-free-tier.md`.

### Estado conocido de la instancia (2026-10-29)

- El canario `harness_api_scan.py --canary` ya ramifica por `kind`
  (`nim`/`opencode`/`cerebras`/`or_free`/`cf`/`mistral`), envía User-Agent de
  navegador, añade `x-opencode-session` a OpenCode Go y publica el status HTTP crudo.
  Antes mandaba todo `kind` desconocido a Cloudflare y declaraba muertes en bloque.
- **`google/gemini-4-argon`: servido por opencode_go, retirado solo de Google directo.**
  El `400 Model is unavailable` que motivó la retirada era del plan de suscripción y el
  429 era de cuota en Google C1/C7. Re-sondado después: el plan lo sirve por
  `chat/completions` (200, 1.05M de contexto, visión, `tool_calls` 3/3) y el cliente lo
  ejecuta sin cambios. Los tombstones caducan igual que los catálogos: re-sondear con el
  endpoint y las cabeceras del cliente antes de confiar en una retirada antigua.
- **Gobierno del gasto**: `monitor_opencode_go.py` (lee `opencode.db`, tabla
  `message`) y `harness_daily_guard.py` (proxy + doctor + canario + gasto, alerta
  sólo si ≠ VERDE). El presupuesto declarado ya tiene lector y cron.
- OpenRouter responde en `/api/v1/auth/key`; `/api/v2/...` da 404.
- **Veto de sondas (2026-11-05)**: `providers/probe_veto.yaml` + `SCRIPTS/probe_veto.py`
  (`--check <id>`, `--list`, `--catalog <json> --free`). Vetados: `perplexity/*`,
  `*/sonar*`, `morph/*`, `google/lyria-*`. Aplicado en `c7_free_client.py` (capa 1.5 del
  `dispatch`), en el canario de `harness_api_scan.py` (VACIO `vetado=True`) y en la
  propuesta de cadena.
- **Barrido programado de gratis**: `SCRIPTS/or_free_watch.py` (`--alert`, `--json`,
  `--dry-run`, `--max-models`). Estado en `.session/or_free_watch_state.json`. Solo
  modelos con `pricing` 0 sin tarifas planas; una petición por modelo; coste $0.00.
  El 2026-11-05 quedaron **9 de 14 vivos**; fuera de uso: `stealth/crouton-alpha` (403 por
  región desde VE), gemma-4 26B/31B y xingchen (429 upstream), content-safety (404).
- **Guardia consolidada (6 ejes)**: `harness_daily_guard.py` = proxy + doctor + canario +
  gasto OpenCode Go + `or_free` + `cupos` por cuenta. Cron `15 7,19 * * *` (antes
  `30 8,20`). Valídala con `env -i HOME=… PATH=/usr/bin:/bin sh -c 'cd … && python3 …'`:
  si solo funciona con el PATH interactivo, el cron fallará en silencio.
- Cifras del plan (topes por modelo, regla 20/50/100, tarifas peak/off-peak, campos de
  facturación): `references/opencode-go-plan-limits.md`. No citarlas de memoria ni
  deducirlas de una sonda.

## Pipeline de decisión (auditar → elegir → aplicar)

La auditoría termina en una decisión de routing, no en un informe. Orden que evita los tres errores
caros (elegir por nombre, aplicar sin medir, publicar cifras sin traza):

1. **Existe** → catálogo vivo del endpoint (`/v1/models`), nunca el config del cliente.
2. **Sirve** → una inferencia real con `max_tokens` **del slot que va a ocupar**, no del bench. Con
   presupuesto corto el razonador trunca y el 0 % acusa al modelo de un límite de la rúbrica (hero:
   0/8 con 2 000 tokens, **8/8 con 12 000**, mismo prompt).
3. **Es agéntico** → `tools` + `tool_choice:auto`, 3 repeticiones, contar `message.tool_calls`.
4. **Es correcto** → trampa aritmética verificable (20/3, no 6,666 aproximado).
5. **Cabe en el presupuesto** → `usage.allowance` por respuesta y la ventana real (`resetsAt`).
6. **Se propaga** → checksum + canario + prueba negativa en el segundo host.
7. **Es estable** → ≥3 repeticiones y comparación pareada (McNemar). 2 de 3 reps = **inestable**, no
   incapaz: se arregla con reintento + escalada, no cambiando de motor. Si el proveedor dispara un
   circuit breaker a mitad de barrido, se **re-mide ese brazo entero** antes de publicar el número.
8. **Se vigila** → el número vive en un medidor con lector en runtime, no en prosa.

Scripts que materializan el pipeline (instancia FloydIA, `SCRIPTS/`):
`model_state_registry.py --build|--lint` · `refresh_ctx_from_catalog.py` · `apply_model_names.py` ·
`gen_c7_allowlist.py` · `suite_overlay_gen.py` · `suite_cotejo.py` · `harness_dashboard.py` ·
`memory_recall.py` (recuperación por párrafos) · `harness_switch.py` (GO⇄FREE atómico, P99 medido) ·
`peak_guard.py` (baja a v4-pro en peak 01-04/06-10 UTC) · `scratch/harness_v51/bench_publicable.py`
(banco ciego con VCR, seed 42, McNemar).

### Reglas de decisión medidas (2026-11-07)

- **Un razonador nunca ocupa un slot de salida corta.** Con el `max_tokens` real del slot (60-150)
  devuelve `content: ""` y `finish=length`; a 400 el proxy corta con 429 «circuit breaker: repetitive».
  Reparto: razonador donde **decide** (decomposición, juicio, review), modelo pequeño no-razonador
  donde **formatea** (título, compresión, triage, voz).
- **La saturación es por modelo, no por cuenta.** En el mismo minuto `deepseek-v4-pro` respondió 200
  (1,9 s) mientras `deepseek-v4.1-flash` daba 429 `overloaded` en la ventana peak 01-04 UTC. Antes de
  tocar credenciales o cuota, sondear un hermano del mismo plan.
- **El nombre del modelo es una afirmación, no un dato.** Si el display name lleva contexto o visión,
  o los genera el registro o se eliminan del nombre: un `[1M]` sobre 131 072 enruta tareas de 1 M a un
  motor de 128k.
- **Medir el contexto cuesta una sonda; inventarlo cuesta una regresión.** Si el proveedor no publica
  el límite, la etiqueta honesta es `?`, y el lint debe aceptarla sólo en ese caso.
- **El catálogo del proveedor tampoco es el catálogo del gateway: los alias responden 200.** Purgar una
  lista de modelos por pertenencia a `/v1/models` borra ids válidos que el proxy resuelve por alias
  (`nemotron-3-ultra-550b` → `nvidia/nemotron-3-ultra-550b-a55b`): el catálogo dice que no existe y la
  sonda de 1 token devuelve 200. La poda se hace **por sonda** (404/410 reales, uno por id), nunca por
  lista; si un id no figura en el catálogo pero responde, se queda con nota, no se borra. Restaurar del
  backup cuesta más que sondear 20 ids.
- **Un test de recall cuyos patrones los escribe quien pregunta mide adivinar la cadena, no la memoria.**
  Antes de culpar al modelo, comprueba dos cosas: (1) ¿el hecho existe en la capa que se consulta?
  (los datos que solo viven en el chat no están en L1 y ninguna recuperación los inventa) y (2) ¿la
  recuperación puntúa pasajes o devuelve la primera coincidencia de un patrón? Pasar de grep-por-patrón
  a párrafos puntuados por solapamiento de términos (idf + normalización por longitud + dedupe por
  contenido cuando el vault está enlazado en dos rutas) subió el mismo par de modelos de 6/10 a 10/10.
