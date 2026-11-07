# P1 — Verificación de ESTADO (¿está vivo y coherente?)

> Pégalo tal cual en una sesión nueva. Objetivo: decir en 5 minutos si el harness está sano, sin gastar allowance.
> Coste esperado: **$0,00**. Tiempo: ≤ 5 min.

## Rol

Eres SRE de plataforma. No arreglas nada: certificas el estado y entregas un veredicto binario.

## Objetivo

Producir un `GO / NO-GO` con evidencia de: proxy, gateway, cron, coherencia configuración↔disco, enjambre MCP y presupuesto leído en vivo.

## Pasos (en este orden; si uno falla, anótalo y sigue)

```bash
cd <PROYECTO>

# 1. Proxy y cuentas
curl -s --max-time 10 http://127.0.0.1:8088/health

# 2. Gateway y cron
pgrep -af 'gateway.*run' | grep -v grep
crontab -l | grep -E 'peak_guard|monitor_opencode|harness_daily'

# 3. Lo que el runtime cree que tiene (no lo que dice el fichero)
for k in model small_model fallback_providers auxiliary.title_generation auxiliary.review auxiliary.vision; do
  echo -n "$k -> "; hermes config get $k | head -2 | tr '\n' ' '; echo
done

# 4. Catálogo y nombres (debe salir {} y exit 0)
python3 scratch/harness_v51/model_state_registry.py --lint; echo "lint=$?"

# 5. Consumidores: la Suite no debe tener deriva
python3 scratch/harness_v51/suite_cotejo.py >/dev/null; echo "cotejo=$?"

# 6. Enjambre: habilitado ≠ caído
hermes mcp list | grep -E '✗|MCP Servers'

# 7. Presupuesto real (no el de un panel)
python3 SCRIPTS/monitor_opencode_go.py | head -20
```

## Contrato de salida

1. Tabla `eje | valor medido | fuente | estado (OK/NO)` con 7 filas.
2. **Una línea de veredicto**: `GO` o `NO-GO` + el eje que lo tumba.
3. Diferencias encontradas entre configuración declarada y runtime (si las hay), con la ruta del fichero.
4. Qué NO pudiste verificar y por qué.

## Criterios binarios

- Proxy `status ok` y `available_accounts ≥ 3`.
- Gateway vivo y `peak_guard` en cron.
- `lint` exit 0 y `cotejo` exit 0.
- Ningún MCP **habilitado** en estado de fallo (los `✗ disabled` son intencionales y no cuentan).
- Presupuesto leído de la fuente viva, no de un panel.


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

