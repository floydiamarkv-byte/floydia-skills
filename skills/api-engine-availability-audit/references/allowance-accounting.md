# Contabilidad de una asignación prepago (allowance) — receta

Para cuando la cadena declara topes por cartera (`window_5h_cap_usd`,
`weekly_cap_usd`, `monthly_allowance_usd`, límites diarios) y **ningún proceso los
lee**: hay que construir el lector, no describir la brecha.

## 1. Dónde está el consumo real

En orden de calidad, la fuente del gasto:

1. **Base de datos de sesiones del cliente** (la que escribe el propio CLI/agente).
   Cada mensaje del asistente suele traer `providerID`, `modelID`, `cost`, `tokens`
   y, a veces, un bloque de facturación anidado. Es la única fuente que cubre TODO el
   tráfico, incluido el que no pasa por tus scripts.
2. Respuesta de la API: `usage` puede traer el desglose facturable aunque el campo
   plano `cost` venga a 0.
3. Un ledger propio, solo si instrumentas cada llamada — y entonces subestimas todo
   lo que llame un humano desde otra herramienta.

Filtrar siempre por proveedor (`providerID IN (...)`), no por nombre de modelo: el
mismo `modelID` aparece servido por varios proveedores con precios distintos.

## 2. Dos cifras, nunca una

- `cost_reportado`: suma del coste que el proveedor devolvió. Hecho.
- `cost_estimado`: reportado + (tokens sin coste × tarifa). Etiquetado.

Declarar además la **cobertura**: porcentaje de tokens con tarifa conocida. Un total
sin cobertura es una cifra inventada con formato numérico.

**El factor entre precio de lista y consumo facturable no es 1.** Un gateway por
suscripción puede imputar `allowance = 4 × list_cost`: el precio unitario que publica y
el consumo que descuenta del cupo son magnitudes distintas. Verifica el factor
comparando ambos campos en la misma respuesta real (dos llamadas, dos cuentas) antes de
multiplicar por nada; si el ledger solo guarda uno de los dos, el gasto se desvía
exactamente por ese factor y el porcentaje contra el tope sale falso.

## 3. Niveles de confianza de la tarifa

| Nivel | Origen | ¿Autoriza veredicto duro? |
|---|---|---|
| `alta` | ≥3 muestras de coste del propio endpoint | Sí |
| `medida` | 1 sonda directa que devolvió precio del propio endpoint | Sí |
| `baja` | 1 muestra propia | No → máximo "aviso" |
| `proxy` | precio del mismo modelo en otro proveedor | No → máximo "aviso" |
| `sin_dato` | solo tokens | No → `SIN_MEDIR`, no "0 %" |

Regla: **CRIT/EXCEDIDO exige precio propio**. Con precio prestado se emite aviso y se
guarda aparte qué habría sido (`veredicto_tarifa_fuerte`) para que el operador vea la
magnitud sin que el sistema afirme una cifra que no puede sostener.

## 4. Sonda de calibración (cuando el ledger no tiene ninguna muestra con coste)

1. Llamada de inferencia real con ~3–5 k tokens de relleno y `max_tokens` pequeño
   (80–160): el precio por token no depende del contenido y el coste de la sonda es
   del orden de milésimas de dólar — medible, no especulativo.
2. Leer el bloque de facturación de la respuesta (`usage.<proveedor>.list_cost`,
   `.allowance`, `.tokens`) y dividir coste entre tokens.
3. Congelar el resultado como constante declarada con su método y fecha de sondeo.
4. Repetir la sonda para cada cartera sin muestras; no extrapolar entre modelos de la
   misma familia.

Si el endpoint exige cabeceras de handshake (sesión de gateway, `User-Agent` de
navegador), la sonda debe llevarlas o devolverá un 400/403 que parece caída.

## 5. Salida y veredictos

Por cartera × ventana (5 h, 7 d, mes): tope, gasto, porcentaje, estado, llamadas,
tokens, tarifa, confianza. Veredicto global con el peor caso.

Estados: `OK` (<80 %) · `AVISO` (≥80 %) · `CRIT` (≥95 %) · `EXCEDIDO` (≥100 %).
Exit codes para poder encadenarlo como guarda: `0` OK · `1` aviso · `2` crítico ·
`3` error de entorno. Un `--guard` que devuelve 2 es lo que permite bloquear en vez
de solo informar.

## 6. Consolidación sospechosa que hay que vigilar

- Modelos servidos por el proveedor pero **sin cartera asignada**: consumen la
  asignación global sin tope propio. Reportarlos como "fuera de cartera" para que no
  desaparezcan del total.
- Carteras sin ninguna llamada: `SIN_MEDIR`, nunca `0 %` presentado como holgura.
- Ventana de 5 h móvil calculada desde el último mensaje, no desde el inicio del día.

## 7. Precisión: lo que la base de datos no guarda

- **El campo facturable suele faltar en el histórico.** Si el cliente no persiste
  `allowance`/`list_cost` por mensaje, las ventanas cortas (5 h) y la semanal solo son
  exactas para el tráfico posterior a la instrumentación. Declara esa cobertura en el
  snapshot en vez de presentar el histórico como si fuera medido.
- **El carril horario se ancla al inicio de la ventana.** Con tarifa peak/off-peak, una
  ventana que cruza el cambio no se mezcla: se etiqueta con el carril vigente cuando
  empezó. Etiquetar con "ahora" hace que el mismo consumo cambie de estado según la
  hora a la que se mire.
- **El reparto input/output/cache se estima con una muestra larga (≈90 d), no con la
  ventana.** En 5 h basta un mensaje con caché grande para que el mix caiga al 99 % de
  cache-read y la tarifa mezclada se desplome; comparar contra el tope con ese número
  produce holguras falsas.
- **La severidad se calcula por la ventana más estricta**, no por el mes: un 80 % en la
  ventana de 5 h es alerta aunque el mes esté al 10 %. Los topes encadenados (5 h = 20 %
  del mensual) garantizan que la ventana corta se agota primero.
