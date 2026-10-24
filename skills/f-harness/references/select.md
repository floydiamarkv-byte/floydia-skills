
# Skill: f-harness-select — Selector Menu-First del Modo de Harness v1.0

> **Propósito**: Permitir al usuario ver y cambiar la cadena de prioridades de motores del Harness FloydIA (qué modelo va primero, segundos y fallback) de forma interactiva, segura y verificable.
>
> **Nivel de riesgo**: R1 (modifica únicamente `SCRIPTS/harness_mode.json`, archivo de estado local y reversible). No toca `settings.yaml` ni credenciales.
>
> **Idioma**: TODA la interacción en español.

---

## 🗺️ 1. Alcance y Límites (IMPORTANTE)

| Qué SÍ cambia este skill | Qué NO cambia |
|---|---|
| La cadena de prioridades del bridge/rotador (`harness_mode.json`) | El `default_model` de la sesión DSH en curso (requiere editar `~/.dsh/settings.yaml` y reiniciar) |
| Efecto inmediato para delegaciones AGY / bridge / rotador NIM | Credenciales, pools ni listas de modelos |

Si el usuario pide cambiar qué modelo ejecuta **esta sesión** del agente, explicar que eso se hace editando `default_model` en `~/.dsh/settings.yaml` + reiniciar sesión, y ofrecer hacerlo aparte (R1, con backup).

---

## 🎯 2. Flujo Menu-First (OBLIGATORIO)

Al activarse el skill, el agente DEBE ejecutar estos pasos en orden:

### Paso 1 — Leer estado actual (verificación, no asunción)
```bash
cat /home/tec/Dropbox/ANTIGRAVITY_PROJECTS/SCRIPTS/harness_mode.json
```
(extraer `mode` y `mode_name`; si no existe, asumir modo 2 = default)

### Paso 2 — Presentar el menú SIEMPRE (marcar el modo activo con 🟢)

```markdown
╔════════════════════════════════════════════════════════════════╗
║   🏎️  HARNESS FLOYDIA — SELECTOR DE MODO (f-harness-select)   ║
╚════════════════════════════════════════════════════════════════╝

Modo actual: [N] <nombre>

Responde con el número para cambiar de cadena de prioridades:

1️⃣  Full Power       → AGY Gemini 3.1 Pro → DeepSeek V4.1 Flash → Nemotron 3.5 Super VL → Nemotron 3 Ultra 550B → Codestral → MiniMax → Pool Free
                        (máxima potencia, mejor calidad)
2️⃣  Working Horse    → MiniMax M3.1 Flash → Codestral 2508 → Nemotron 3.5 Super VL → DeepSeek V4.1 Flash → Nemotron Lightning → Pool Free
                        (equilibrio recomendado — DEFAULT)
3️⃣  NIM Only         → Super VL → Ultra 550B → Nemotron Super → Lightning (rotación 4 cuentas NIM)
                        (razonamiento denso sin AGY; sustituye al extinto Kimi Only)
4️⃣  AGY + Free       → AGY Gemini 3.1 Pro → DeepSeek V4.1 Flash → Codestral 2508 → Cloudflare R1 Distill → Pool Free
                        (ideal si el NIM está congestionado hoy)
5️⃣  Free Light       → Pool Free rotativo puro (Lightning :free → Super :free Kilo → Ministral 8B)
                        (ultra austero, cuotas al límite)
6️⃣  AGY Deep         → AGY Gemini 3.1 Pro → DeepSeek V4.1 Flash → Nemotron 3 Ultra 550B → Nemotron 3.5 Super VL → Pool Free
                        (dirección reforzada)

0️⃣  Salir sin cambios

ℹ️  NOTA — La cadena es RESPALDO, no paralelismo:
    se usa el primer motor disponible; los demás entran SOLO si el
    anterior falla (429/caída). No significa "todos trabajando a la vez".
    Para elegir motor según DIFICULTAD de la tarea: /f-harness-router
```

### Paso 3 — Leer la selección del usuario
Usar la herramienta de pregunta interactiva (`ask_user_question`) con las opciones 1–6 (0 = salir). NO asumir; el usuario elige.

### Paso 4 — Aplicar la conmutación
Si elige 1–6, ejecutar:
```bash
bash /home/tec/Dropbox/ANTIGRAVITY_PROJECTS/SCRIPTS/harness_mode.sh <N> < /dev/null
```

### Paso 5 — Verificación por evidencia (Protocolo v28)
Nunca afirmar el cambio sin confirmarlo:
```bash
cat /home/tec/Dropbox/ANTIGRAVITY_PROJECTS/SCRIPTS/harness_mode.json
```
Presentar al usuario el resultado: modo nuevo, `mode_name` y `updated_at` literales del JSON.

---

## 📋 3. Tabla de referencia de los 5 modos

| Nº | Nombre | Cadena | Cuándo usarlo |
|----|--------|--------|----------------|
| 1 | `full_power` | AGY → DeepSeek V4.1 Flash → Super VL → Ultra 550B → Codestral → MiniMax → Pool Free | Máxima potencia/calidad |
| 2 | `working_horse` | MiniMax M3.1 Flash → Codestral → Super VL → DeepSeek V4.1 Flash → Lightning → Pool Free | Equilibrio diario (DEFAULT) |
| 3 | `nim_only` | Super VL → Ultra 550B → Nemotron Super → Lightning (rotación NIM C1→C2→C7→C9) | Razonamiento denso sin AGY (sustituye al extinto `kimi_only`) |
| 4 | `agy_free` | AGY → DeepSeek V4.1 Flash → Codestral → Cloudflare R1 Distill → Pool Free | NIM congestionado ese día |
| 5 | `free_light` | Lightning :free → Super :free Kilo → Ministral 8B | Cuotas al límite |
| 6 | `agy_deep` | AGY → DeepSeek V4.1 Flash → Ultra 550B → Super VL → Pool Free | Dirección reforzada |

> **Reordenación 2026-10-21 (criterio: Elo de LMArena + capacidad local).** La cadena por tier se recalibró con el ranking externo, que sí distingue donde la medición local no podía (±15 pp de margen): `DeepSeek V4.1 Flash` (Elo 1474,6, IC [1468,1481]) y `MiniMax M3.1 Flash` (94 % de capacidad) van por delante de los Nemotron en los carriles de trabajo (`Ultra 550B` 1426,0 · `Super VL` 1415,9 — CI sin solapar con DeepSeek).
> **AGY conserva la cabecera de `direccion`** por ser el **único motor con visión** (QA visual obligatorio, contrato 16), no por ranking.

> **TOMBSTONE — Kimi K3 retirado (2026-10-15, `410 Gone` en NIM).** Ya no es ningún motor de la cadena.
> Sustitutos verificados: `nvidia/nemotron-3-ultra-550b-a55b` (C4, deliberación) y `nvidia/nemotron-3.5-super-vl-120b-a12b` (C1/C5, sincrónico).
> La API directa de Moonshot (`C7_KIMI_PLATFORM_API`) es **de pago** (saldo $1,65) y queda **fuera del harness por decisión del operador** (2026-09-29): solo a mano, con `--break-glass` o petición explícita.

---

## 🛡️ 4. Reglas duras

- **Confirmación humana siempre** antes de ejecutar el cambio (el usuario elige número).
- Comando de conmutación con `< /dev/null` (anti-hang, sin prompts interactivos).
- Si `harness_mode.sh` devuelve error, mostrar el error literal y no reintentar más de 1 vez.
- Prohibido modificar `~/.dsh/settings.yaml` desde este skill.
- Si el usuario solo pidió "ver el modo", ejecutar Paso 1 y mostrar el estado sin ofrecer cambio.
- Registrar cambios relevantes como evento append-only en `.session/memory_events.jsonl` solo si el usuario lo pide.

---

## ✅ 5. Criterio de éxito del skill

- Menú presentado con el modo real marcado.
- Conmutación con exit 0 y JSON persistido verificado y mostrado literalmente.
- Cero cambios no solicitados.
