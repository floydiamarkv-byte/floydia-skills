# Cotejo de los 4 agentes — 2026-11-07 11:29

**4 de 4 respondieron.** Tres certifican midiendo; Antigravity certifica **disintiendo** (revisión sin
herramientas, porque su ACP headless no ejecuta tools: 0 chars / 0 tokens en 1 196 s con prompt de
herramientas, y respuesta correcta con prompt de solo razonamiento).

| Campo | Hermes | OpenCode | DSH | Antigravity |
|---|---|---|---|---|
| Modo | medición | medición | medición | revisión adversarial |
| Catálogo | 79 | **79** | — | coincide |
| `model` | deepseek-v4.1-flash | opencode_go/deepseek-v4.1-flash | — | coincide |
| `small_model` | nim…/deepseek-v4.1-flash | nim…/deepseek-v4.1-flash | — | — |
| Nombres `[?]` | 31 | **31** | — | lo marca como riesgo |
| MCP SSOT / cliente | 21 / 20 | — | 21 / 4 | lo marca como riesgo |
| Lint | 0 | 0 | — | coincide |
| Inferencia propia | sí | sí | `DSH-VERIF-OK` | sí (solo razonamiento) |
| **Veredicto** | CERTIFICADO | CERTIFICADO | CERTIFICADO | **NO CERTIFICADO** |

## Certificación por intersección: 3 sí, 1 no → **AMARILLO**

`CERTIFICADO` exige los cuatro. Antigravity disiente, así que el sistema **no se declara certificado**
hasta adjudicar su disenso. Adjudicación, riesgo por riesgo:

| Riesgo de Antigravity | ¿Vale? | Evidencia |
|---|---|---|
| «DSH 48,9 s viola el límite de 20 s» | **No** | R4 tiene dos relojes: control ≤20 s, **inferencia 90-120 s**. Los 48,9 s son una inferencia con arranque de MCP dentro del perfil `default`. Confunde los relojes. |
| «`gemini-3.8-flash` ausente del endpoint local» | **No** | Es un modelo de **Google**, comprobado contra el catálogo NIM. Verificado en Google AI Studio: existe. Mismo error de categoría que cometió DSH. |
| «31 modelos con `[?]` sin verificar» | **Parcial** | Cierto que no están verificados; `[?]` es el **estado terminal documentado** (el proveedor no publica el límite). No es un defecto, es honestidad. |
| «MCP 20 vs 4 y `node_modules` como pseudo-perfil» | **Sí (menor)** | La disparidad es el `allow` por cliente (correcto). `node_modules` sí se cuela en el listado de perfiles de DSH: cosmético, corregible. |

**Resultado**: dos riesgos son errores de categoría (catálogo equivocado y reloj equivocado), uno es un
estado documentado y uno es real pero menor. El disenso **no tumba** la certificación, pero sí destapa
dos huecos de documentación que ya quedan anotados en la suite.

## Hallazgo cruzado que ningún agente vio solo

DSH y Antigravity cometieron **el mismo error**: validar un modelo de Google contra el catálogo NIM.
Regla añadida a la suite: *cada modelo se comprueba contra el catálogo de SU proveedor; el catálogo del
proxy no sirve para juzgar modelos de otra casa.*

## Fallos de ejecución (evidencia)

| Agente | Intento | Resultado |
|---|---|---|
| Antigravity | suite completa | `exit 124` a 900 s |
| Antigravity | versión reducida con herramientas | `{"chars": 0, "usage": {}, "seconds": 1195.9}` → ACP no ejecuta tools headless |
| Antigravity | **sin herramientas** | ✅ JSON con disenso argumentado |
| OpenCode | suite completa | `exit 1` a 350 s (escribió su propio probe, 401 de NIM, siguió explorando) |
| OpenCode | prompt mínimo (3 comandos) | ✅ JSON en ~2 min |
| DSH | suite completa | `exit 124` a 900 s |
| DSH | versión reducida | ✅ JSON en 487 s |

**Lección**: la suite completa no cabe en una ejecución headless de 15 min. El despachador debe usar
siempre la versión reducida (5-6 comandos, JSON al final), y Antigravity solo acepta prompts de
razonamiento puro.
