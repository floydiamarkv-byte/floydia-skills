# Cotejo de los 4 agentes — 2026-11-07 11:23

**3 de 4 respondieron con JSON válido.** Antigravity no completó: 900 s sin salida (dos intentos:
suite completa y versión reducida). Se declara `NO_VERIFICADO`, no se inventa.

| Campo | Hermes | OpenCode | DSH | Antigravity |
|---|---|---|---|---|
| Modelos en catálogo | 79 | **79** | — | no verificó |
| `model` por defecto | deepseek-v4.1-flash | opencode_go/deepseek-v4.1-flash | — | — |
| `small_model` | nim_local/deepseek-ai/deepseek-v4.1-flash | nim_local/deepseek-ai/deepseek-v4.1-flash | — | — |
| Nombres con `[?]` | 31 (registro) | 31 | — | — |
| MCP SSOT / cliente | **21 / 20** | — | 21 / 4 | — |
| MCP caídos | 0 | — | — | — |
| Lint | exit 0 | exit 0 | — | — |
| Proxy NIM | ok, 4 cuentas | HTTP 200 | — | — |
| Inferencia propia | sí | sí | sí (`DSH-VERIF-OK`) | no |
| Veredicto artefacto | CERTIFICADO | CERTIFICADO | CERTIFICADO | NO VERIFICADO |
| Veredicto entorno | CERTIFICADO | CERTIFICADO | CERTIFICADO | NO VERIFICADO |

## Coincidencias (lo que sí se puede certificar)

- **79 modelos** en el catálogo y **31 nombres con `[?]`** — dicho por dos agentes independientes
  (Hermes contando el registro, OpenCode contando el JSONC).
- `model` = `opencode_go/deepseek-v4.1-flash` y `small_model` = `nim_local/deepseek-ai/deepseek-v4.1-flash`
  en los dos que lo declaran.
- **Lint en 0** desde dos clientes distintos.
- El proxy responde para los tres que lo probaron (OpenCode 200, Hermes `ok` con 4 cuentas).

## Diferencia esperada (no es deriva)

`mcp.cliente`: **20 en Hermes/Antigravity** vs **4 en DSH**. Es el `allow` por cliente de
`mcp_clients.json` (DSH solo declara ga4, gsc, notebooklm, obsidian). El SSOT dice 21 para todos.
Queda documentado para que nadie lo lea como fallo en la próxima corrida.

## Hallazgo cruzado (el valor del cotejo)

DSH reportó `gemini-3.8-flash` como **sustituto muerto** en `deprecated_models.yaml`. **Es un falso
positivo suyo**: comprobó el catálogo NIM (`:8088`) para un modelo de Google. Verificado contra Google
AI Studio: `gemini-3.8-flash` **existe**; lo que ya no existe es `gemini-2.0-flash`, que es justo la
entrada obsoleta que ese sustituto reemplaza. La entrada de DSH es correcta; su verificación usó el
catálogo equivocado.

## Lo que falló y por qué (evidencia)

| Agente | Resultado | Evidencia |
|---|---|---|
| Antigravity | `exit 124` a los 900 s, sin JSON | `antigravity_raw.txt`; dos intentos (suite completa y reducida) |
| OpenCode (1.º intento) | `exit 1` a los 350 s | se puso a escribir su propio probe, recibió **401 Invalid credential** de NIM y siguió explorando hasta el timeout |
| OpenCode (2.º intento, mínimo) | ✅ JSON válido | `opencode.json` |

**Lección operativa**: los prompts de suite completa no caben en una ejecución headless de 15 min;
hay que despachar la **versión reducida** (5-6 comandos, JSON al final) o dar 30+ min. Antigravity
necesita además aprobación interactiva para herramientas, que en ACP headless no llega.
