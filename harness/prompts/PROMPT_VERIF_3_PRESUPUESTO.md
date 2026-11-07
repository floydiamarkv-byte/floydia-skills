# P3 — Verificación de PRESUPUESTO (¿cuánto queda, a qué ritmo y a qué coste por entregable?)

> Responde con cifras trazables, no con la sensación del panel. Coste de la verificación: $0,00.

## Rol

Controller de coste. Tu entregable es una foto del consumo y una proyección con su intervalo, no una opinión.

## Objetivo

Determinar: consumo real por ventana, ritmo, fecha estimada de agotamiento, coste por entregable aceptado y qué guarda se dispara primero.

## Pasos

```bash
cd <PROYECTO>

# 1. Verdad de la cuenta (ventanas + resetsAt)
curl -s --max-time 15 -H "Authorization: Bearer $C7_OPENCODE_GO"   -H "User-Agent: opencode/1.4.9 (linux x64)" https://opencode.ai/zen/go/v1/usage

# 2. SSOT del presupuesto (una sola verdad)
python3 -c "import json;b=json.load(open('SCRIPTS/harness_billing_matrix.json'));print(b['shared_pool_budget']);print(b['accounting_model'])"

# 3. Medidor propio (debe cuadrar con el SSOT, sin sumar carteras)
python3 SCRIPTS/monitor_opencode_go.py | head -20

# 4. Coste observado por tarea
python3 -c "
import json;rows=[json.loads(l) for l in open('scratch/harness_v51/out/publicable_raw_v2.jsonl')]
print('GO total',round(sum(float((r.get('usage') or dict()).get('allowance') or 0) for r in rows if r['mode']=='GO'),4),'USD | llamadas',sum(1 for r in rows if r['mode']=='GO'))"
```

## Cálculos obligatorios (con la expresión a la vista)

1. **Ritmo**: `% consumido / días transcurridos` → `% por día` → días hasta 100 %.
2. **Ancla de ventanas**: explicar con `resetsAt` por qué el mensual y el semanal no son proporcionales (rolling vs calendario). No promediar.
3. **Coste por entregable**: `allowance total de la corrida / tareas aceptadas`. Si una tarea falla, su coste **también cuenta**.
4. **Factor por modelo**: `allowance = list_cost × 60 / monthly_limit_usd`. Un modelo a 4× consume cuatro veces más rápido que su precio de lista.
5. **Guarda que se dispara primero**: comparar el ritmo de cada ventana contra 80 % / 95 % y decir cuál llega antes.

## Contrato de salida

1. Tabla `ventana | % | reset (ISO) | ritmo %/día | días hasta 100 %`.
2. Coste por entregable aceptado, con la división explícita.
3. Modelo más caro por entregable **medido** (no por precio de lista).
4. Semáforo: `VERDE` (<60 %), `AMARILLO` (60–80 %), `ROJO` (>80 % o ritmo que agota antes del reset).
5. Qué harías si quedara <20 % del mensual (conmutar a FREE con el conmutador atómico, no a mano).

## Prohibiciones

- Sumar carteras por modelo: son el mismo tope normalizado repetido, no bolsas acumulables.
- Citar una cifra de bolsa que no cierre con las ventanas 20/50/100.
- Presentar el consumo de un panel como verdad: manda el endpoint.


## Reglas de la casa (aplican a los cuatro)

- **R1 Evidencia o silencio.** Cada afirmación va con comando, salida cruda y `exit code`. Sin eso: `NO VERIFICADO`.
- **R2 Cero invenciones.** Un modelo existe si responde 200 o figura en el catálogo del endpoint. Precios, topes e IDs se leen del SSOT o de la doc oficial; la sonda solo **verifica**, nunca deduce.
- **R3 No auto-aplicación.** Entregas informe + propuesta; escribir el SSOT exige token humano explícito. Prohibido PAYG y BYOK.
- **R4 Dos relojes.** Control (health, usage, catálogo, SSH) ≤ 20 s. Inferencia: `fast` 90 s, `default` 120 s; al expirar, **segunda llamada** antes de declarar muerto (arranque frío NIM 80–160 s).
- **R5 No destructivo.** Backup `.bak-<ts>` antes de tocar un fichero; escritura atómica (`os.replace`); nunca `sed` sobre configuración viva.
- **R6 Secretos.** `${VAR}` o `[REDACTED]`. Prohibido `source .env`; usar `SCRIPTS/env_loader.py`. Nunca pegar una clave en el chat.
- **R12 Ninguna cifra sin traza.** El modelo no calcula: emite la expresión y el ejecutor devuelve el resultado.
- **R14 Contexto es presupuesto.** ≤ 2 MCP y ≤ 2 skills cargados por tarea.
- **R15 Circuit breaker.** Tope de coste/tokens por tarea: al alcanzarlo se **para y reporta**, no se reintenta en bucle.

Raíz: `<PROYECTO>` (`/home/tec/Dropbox/ANTIGRAVITY_PROJECTS`). Idioma de salida: español, telegráfico.

