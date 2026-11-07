# HARNESS FLOYDIA v5.1 — Auditoría y rediseño dual (GO/FREE)

**Fecha**: 2026-11-06 (local) / 2026-11-07T03:0xZ · **Host**: HP15 (Debian 13, sin systemd) · **Auditor**: HermesHP15
**Estado**: `PROPUESTA_NO_APLICADA` — nada se ha escrito en los SSOT. Token humano pendiente.
**Veredicto**: **AMARILLO** — el sistema está vivo y el modo FREE es realmente $0,00, pero hay 1 MCP caído, 82 nombres no conformes, 4 IDs muertos en la allowlist y tres cifras de bolsa conviviendo.

Ruta de evidencias: `scratch/harness_v51/out/` (JSON/JSONL crudos, hashes de fixtures en `fixtures/SHA256SUMS.json`).

---

## 0. Resumen en una tabla

| Criterio de aceptación (§12.9) | Resultado | Evidencia |
|---|---|---|
| FREE con coste 0 y prueba negativa superada | ✅ | `out/negative_test.json` → `pass: true`, delta allowance 0,0 |
| GO ≤ 20 % ventana 5 h | ✅ 0,1195 $ de 12 $ = **1,0 %** | suma de `allowance` en 30 respuestas |
| Conmutación P99 ≤ 5 s | ✅ **P99 1,98 ms** en 80 conmutaciones | `out/switch_bench.json` · `SCRIPTS/harness_switch.py` |
| FREE ≥ 6/8 sin fallos críticos | ✅ **7/8** (T8: 1 rep con suma errónea) | `out/summary*.json` |
| GO ≥ 6/8 | ✅ **7/8** (T1 hero truncado) | ídem |
| Recall@1 ≥ 9/10 | ✅ **10/10 FREE · 10/10 GO** (tras arreglar recuperación y L1) | `out/recall_test.json` |
| 0 MCP caídos del SSOT | ✅ **0** (crawl4ai deshabilitado 2026-11-07) | `hermes mcp list` → `✗ disabled` |
| 0 nombres no conformes | ✅ **79/79** conformes (82 reescritos, 3 IDs muertos eliminados) | `--lint` → `{}`, exit 0 |
| Propagación + canario golden | ✅ **HP45 sincronizado y verificado** (3 md5 iguales, canario `CANARY-OK`) | §Aplicado-2 |
| `suite_cotejo.json` sin deriva | ❌ **29 derivas** (25 IDs inexistentes, 4 ctx) | `out/suite_cotejo.json`, exit 2 |
| Ninguna cifra sin traza | ✅ cada cifra de este informe apunta a un fichero de `out/` | — |

---

## 1. F0 — Preflight (todo ejecutado, $0,00 salvo sondas)

| Check | Salida | Evidencia |
|---|---|---|
| `harness_doctor.py` | `🟢 PASS (exit 0)`, 62 refs en config | consola |
| `GET :8088/health` | `ok`, **4 cuentas**, uptime 7 722 s, 33 RPM/cuenta, perfiles `fast` read=90 s / `default` 120 s | consola |
| `opencode_go_usage_api.py --json` | 5 h **3 %** · semana **30 %** · mes **48 %** (03:05Z) | `sha256 18b91307…` en la salida |
| Créditos OpenRouter C7 | comprados **24 $**, usados **24,464 $**, saldo **−0,464 $**, `is_free_tier: false` | `GET /api/v1/credits` + `/api/v1/key` |
| `hermes config get model` | `deepseek-v4.1-flash` / `opencode-go`; small = `nim_local/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | consola |

**Ancla de ventanas (tarea §3.2).** Las tres ventanas no son anidadas: la de 5 h es *rolling* (reset 07:02Z), la semanal es calendario (lunes 00:00Z, reset 09-nov) y la mensual es aniversario de la suscripción (reset 23-nov 20:00Z). Por eso 48 % mensual con 30 % semanal **no es incoherencia**: el ciclo mensual arrancó el 24-oct y las dos primeras semanas ya están consumidas; la ventana semanal sólo mira los últimos 7 días. No se promedia: se mide contra `resetsAt`, que es la única ancla.

**Factor de allowance, medido no deducido.** Una respuesta real de `deepseek-v4.1-flash` devolvió `list_cost=1,905e-05` y `allowance=1,143e-05` → ratio **0,6 = 60/100**. Confirma `allowance = list_cost × 60/M` con M=100, y **desmiente** el «allowance = 4 × list_cost» que afirma la skill.

---

## 2. F1 — Inventario con sonda realista

Sonda por modelo: 3 herramientas en un turno (se cuentan llamadas válidas por esquema), lectura de una captura con 3 cifras, y trampa aritmética («20 km en 3 min → km/h» = 400) con 6 000 tokens de presupuesto.

| Modelo | Fuente | tools | visión | trampa | p50 tools |
|---|---|---|---|---|---|
| deepseek-v4-pro | GO | 3/3 | no declara | ✅ | 3 574 ms |
| deepseek-v4.1-flash | GO | 3/3 | no declara | ✅ | 26 689 ms (frío) |
| glm-5.3-flash | GO | 3/3 | no declara | ✅ | 1 359 ms |
| gemini-4-argon | GO | 3/3 | **3/3** | ✅ | 3 389 ms |
| kimi-k3.1-pro | GO | **0/3** | no declara | **❌** | 3 583 ms |
| nemotron-3.5-lightning-30b-a3b | NIM | 3/3 | — | ✅ | 1 042 ms |
| nemotron-3-nano-omni-30b-a3b | NIM | 3/3 | **3/3** | ✅ | 768 ms |
| nemotron-3-ultra-550b-a55b | NIM | 3/3 | — | ✅ | 1 187 ms |
| diffusiongemma-26b-a4b-it | NIM | 3/3 | **3/3** | ✅ | 870 ms |
| z-ai/glm-5.3-flash | NIM | 3/3 | — (declara, no probado) | ✅ | 1 356 ms |
| nemotron-3.5-bolt-e4b | NIM | 3/3 | — | **❌** | 1 072 ms |

Datos crudos: `out/f1_probe.json`.

**Lo que cambia respecto al anexo del prompt:** `kimi-k3.1-pro` **no sirve como agente** (0 tool_calls, trampa incorrecta) pese a ser el rol «R3 con gate»; `bolt-e4b` confirma el fallo aritmético; `z-ai/glm-5.3-flash` en NIM es tan capaz como el de pago para tools. El catálogo NIM sigue listando `nvidia/nemotron-3-super-120b-a12b` **y no lo sirve**: la sonda devuelve `404 Function … Not found for account` en 399 ms, sin fallback silencioso (`out/negative_test.json`).

---

## 3. F3 — Banco congelado de 8 tareas web/SEO

Fixtures deterministas generados en `fixtures/` (HTML con defectos, CSS duplicado, volúmenes reales congelados, PNG con 3 métricas); `temperature=0`, `seed=42`, 3 repeticiones por tarea y modo, orden aleatorizado, evaluador ciego (graders en código, definidos antes de correr), fallos contados.

| Tarea | GO (modelo) | GO pass | FREE (modelo) | FREE pass | Coste GO/entrega |
|---|---|---|---|---|---|
| T1 hero responsive | v4.1-flash | **0/3** | nano-omni | **3/3** | 0,001096 $ |
| T2 corregir CLS | v4.1-flash | 3/3 | nano-omni | 3/3 | 0,000294 $ |
| T3 Schema.org Product+Breadcrumb | v4.1-flash | 3/3 | nano-omni | 3/3 | 0,000206 $ |
| T4 auditoría on-page 16 requisitos | v4.1-flash | 3/3 | nano-omni | 3/3 | 0,000360 $ |
| T5 brief con volúmenes reales | v4-pro | 3/3 | **ultra-550b** | 3/3 | 0,020801 $ |
| T6 refactor CSS sin cambio de render | glm-5.3-flash | 3/3 | lightning-30b | 3/3 | 0,000085 $ |
| T7 leer captura (3 cifras) | gemini-4-argon | 3/3 | diffusiongemma | 3/3 | 0,005408 $ |
| T8 bucle de 5 pasos con tools | glm-5.3-flash | 3/3 | nano-omni | **2/3** | ~0 |

**Hallazgo mayor (H-01).** El modo GO **pierde** la tarea de maquetación: `deepseek-v4.1-flash` gasta 2 891–5 476 tokens de razonamiento antes de escribir HTML y agota el presupuesto (`finish_reason: length`); con 6 000 tokens sólo 1 de 3 reps terminó el fichero (`out/t1_diag.json`). El FREE nano-omni entrega el hero completo en 4–6 s y pasa 7/7 checks. **No es incapacidad del modelo, es presupuesto de salida**: sin `max_tokens ≥ 12k` o sin streaming con continuación, un modelo de razonamiento no puede emitir artefactos largos.

**Hallazgo (H-02).** La ruta FREE propuesta en el prompt (nano-omni para keyword/SERP) **falla aritmética**: suma 46 600 donde el total real es 43 900 (0/3). Con `ultra-550b` —el modelo que el propio prompt asigna a ese rol— pasa 3/3. La tabla de routing hay que respetarla o el modo FREE incumple R12.

**Hallazgo (H-03).** T8 FREE falló 1 de 3 por suma final incorrecta con 5/5 tool_calls válidas: el bucle funciona, la aritmética no. Todo total que vaya a un entregable necesita verificador determinista, no confianza en el modelo.

Coste total de la fase: **0,1195 $ de allowance** (1,0 % de la ventana de 5 h), 30 llamadas GO, 30 llamadas FREE, 0 errores de transporte.

---

## 4. F2 — Frescura, contradictores y nombres

### 4.1 Contradicciones skill ↔ SSOT (lista completa)

| # | Afirmación | Fichero:línea | Verdad medida |
|---|---|---|---|
| C1 | «$170 allowance» | `.agents/skills/f-harness/SKILL.md:53` | bolsa ponderada **60 $** (`harness_billing_matrix.json`) |
| C2 | «allowance = 4 × list_cost» | `f-harness/SKILL.md:72` | `allowance = list_cost × 60/M`; medido **0,6** para v4.1-flash |
| C3 | «V4.1 Flash $80» | `f-harness/SKILL.md:72` | `monthly_limit_usd = 100`; factor 0,6 verificado en respuesta |
| C4 | «catálogo free = 15 IDs, 13 con tools, mayor contexto stealth/crouton-alpha» | `f-harness/SKILL.md:94` | **corregido 2026-11-07**: el catálogo free real (precio 0 + tools, sin routers) son **13 IDs**; `stealth/crouton-alpha` **sí existe** (1 M, visión) y es el de mayor contexto. Los 4 IDs muertos eran de la allowlist, no del catálogo |
| C5 | «el proxy reescribe a `private/nvidia/nemotron-3.5-super-120b-a12b`» | `f-harness/SKILL.md:95` | ese ID no está en el catálogo NIM (84 ids); la identidad real se mide con `harness_api_scan.py --canary` |
| C6 | «NIM local procesa con `nemotron-3-super-120b`» | `f-scraper/SKILL.md:33` | **404** desde el recorte del 20-oct; sustituto `nano-omni` |

Ninguna otra skill contradice cifras del SSOT (barrido sobre 83 skills; las 14 coincidencias de «ID de modelo inexistente» son rutas de fichero y nombres de servicio, no modelos enrutados).

### 4.2 Allowlist C7

10 entradas, **4 muertas**: `minimax/minimax-m3.1-flash:free`, `stealth/space-bunny-alpha`, `nvidia/nemotron-3-super-120b-a12b:free`, `poolside/laguna-s-2.1:free`. Además el documento afirma «saldo protegido de $0,65» cuando el saldo real es **−0,46 $**. Regenerar desde el registro antes de cualquier corrida FREE.

### 4.3 Nomenclatura

- **82 objetos de modelo**, **0** conformes a la gramática v5.1 (`[OK][262k][F] Nombre`). Todos usan la vieja `[1M-F]`.
- **5 discrepancias materiales** de contexto (el resto son redondeos 1M↔1 048 576):

| ID | Nombre declara | `limit.context` | Fuente canónica |
|---|---|---|---|
| `nim_local/deepseek-ai/deepseek-v4.1-flash` | 1M | 131 072 | **mentira** (nombre vs límite) |
| `opencode_go/glm-5.3-flash` | 128k | 131 072 | billing dice 1 000 000 → **tres valores** |
| `opencode_go/claude-haiku-5-5` | 200k | 200 000 | billing dice 1 000 000 |
| `cerebras/gpt-oss-120b` | 131k | 65 536 | nombre vs límite |
| `cerebras/qwen-3.8-27b` | 131k | 65 536 | nombre vs límite |

- IDs duplicados: 3 (`gemini-3.1-pro-preview`, `gemini-3.5-flash`, `gemini-3.8-flash`) pero **en proveedores distintos** (`google_c2…c6`), lo que es legítimo; el lint debe evaluar duplicados por proveedor.
- Lint ejecutable: `scratch/harness_v51/model_state_registry.py --lint` → `exit 2` con 82 hallazgos.

---

## 5. F4 — Propuesta (no aplicada)

`scratch/harness_v51/harness_mode_v51.propuesta.json` contiene:

- **Presupuesto** con ancla `resetsAt` y **plan de purga** de `1320,0` y `170` (con fichero:línea y valor vencedor).
- **Dos modos** con roles y evidencia medida por rol; `kimi-k3.1-pro` sale de la ruta agéntica.
- **Guardas**: aviso 80 %, parada no crítica 95 %, conmutación a FREE con <20 % mensual, circuit breaker 40k tokens / 0,25 $ por tarea, `max_tokens ≥ 12k` para artefactos.
- **Conmutador**: criterios explícitos; P99 **NO VERIFICADO** porque no se implementó.

**Cambios de routing que la medición obliga** (vs. la tabla del prompt):

1. Maquetación/hero → **FREE `nano-omni`** (3/3) o GO `glm-5.3-flash`; **no** `v4.1-flash` sin presupuesto de 12k.
2. Keyword/SERP FREE → **`ultra-550b`** (3/3), no `nano-omni` (0/3).
3. R3 con gate → **no** `kimi-k3.1-pro` hasta que emita tool_calls; hoy 0/3.
4. Visión FREE → `diffusiongemma` confirmado (698 ms, 3/3 cifras); GO `gemini-4-argon` 4,6 s y 0,0054 $/captura.

---

## 6. Registro de estado y nomenclatura

`out/model_state_registry.json` (propuesta, generado por `model_state_registry.py --build`): 82 entradas con `existe`, `tools`, `vision`, `ctx_real`, `ctx_declarado`, `last_verified`, `estado`, `coste.factor`, `TTL=7d`. Fuentes: catálogo GO (30 ids), NIM (84), OpenRouter (424, 13 free con tools) y `harness_billing_matrix.json`.

Estado actual por proveedor: GO **30 ids en catálogo, 22 utilizables y 7 bloqueados** por región/privacidad según el SSOT de facturación; NIM **84 listados con 1 fantasma verificado** (`nemotron-3-super-120b-a12b` → 404); OpenRouter **13 free con tools** de 424 (criterio precio 0 + tools). El registro detecta además **3 IDs muertos dentro de `opencode.jsonc`**: `nim_local/z-ai/glm-5.3`, `openrouter/thinkingmachines/inkling:free` y `…inkling-small:free`.

`MODEL_NAMING.md` (en esta carpeta) fija la gramática única, el mapeo de `:free` y las reglas del lint.

---

## 7. Memoria × MCP × skills

**7 capas**: L0 preflight (381 tokens, `boot_budget_check.py` PASS) · L1 `.env` (431 claves) · L2 memoria del agente · L3 skills (83, índice ≈ **2 640 tokens**) · L4 vault (`journal/`, `events/`) · L5 NotebookLM · L6 MCP (21). Mapa completo en `memory_map.md`.

**3 niveles de resolución**: L1 caché (`activeContext` 381 + `notes-next-session` 847 tokens) → L2 vault dirigido → L3 `grep` acotado. La prueba de recall confirma que **empezar por L3 funciona para localizar, pero no para responder**: 10/10 recuperaciones encontraron fichero, sólo 6/10 (FREE) y 5/10 (GO) dieron el dato exacto.

**Respuestas a las 6 preguntas exigidas:**

1. **Qué se pierde entre sesiones y por qué capa.** Se pierde la *decisión* (capa L4): 170 de 173 handoffs de los últimos 30 días no vuelven a mencionarse en ninguna sesión, log o `.session`. El bootloader sólo relee `activeContext` + `notes-next-session` (1 228 tokens): todo lo demás depende de que un humano lo pegue. La capa que falla es la **L4 sin índice de lectura**, no la memoria del modelo.
2. **Skills que contradicen el SSOT.** Las 6 de §4.1, lista completa.
3. **MCP en el SSOT que no responde / responde sin estar.** `crawl4ai` está en el SSOT (con `disabled: true`) y en Hermes como habilitado, y **no conecta** (timeout 30,2 s). Ningún servidor responde sin estar en el SSOT: 21 = 21.
4. **Tokens de arranque y no usados.** Índice de skills ≈ 2 640 tokens; bootloader 1 228; los 21 esquemas MCP suman el grueso (≈40k). En las últimas 10 sesiones: **6 MCP con 0 llamadas** (`notebooklm-mcp`, `obsidian-mcp`, `colab`, `google-cloud`, `google-ads-mcp`, `stitch`) y los 7 tenants `novamira-*` aparecen exactamente 63 veces = nº de peticiones, es decir **sólo en la definición de herramientas**, sin llamadas. 7 de 83 skills sin mención.
5. **¿El recall funciona sin el modelo grande?** Sí para recuperar (10/10 hits), no para responder con exactitud: FREE 6/10 vs GO 5/10. **El modelo grande no aporta recall**; aporta redacción. El cuello es la relevancia del snippet.
6. **Handoffs no leídos.** 170/173 (98,3 %) sin referencia externa; método: corpus de 842 ficheros de sesiones/logs/`.session` (1,17 MB) contra el nombre del handoff.

**7 fallos auditados**: F1 amnesia de sesión → confirmado (170/173) · F2 deriva SSOT↔realidad → confirmado (allowlist, `1320`, saldo) · F3 allowlist podrida → 4/10 · F4 tool drift MCP → `crawl4ai` (y 6 servidores que sólo se declaran) · F5 skills symlink → confirmado (`f-*` exigen editar `.agents/skills/*`) · F6 colisión de nombres → 3 IDs repetidos entre proveedores Google · F7 presupuesto de contexto → 2 640 tokens de índice + ~40k de MCP para tareas de 8 tareas distintas.

---

## 8. Propagación a HP45 y cotejo con la Suite

**Preparada, no ejecutada (R9).** Cadena propuesta:

```
~/.config/opencode/opencode.jsonc (catálogo)
  → sync_models_all.sh → XDG opencode · DSH profiles · plantilla SCRIPTS/dsh-settings.yaml · Hermes config
  → sync_models_hp45.sh → scp/rsync a operador@example.com
  → dsh_proxy_daemon.sh restart (ambas) → Suite 2.0 recarga
```

**Corrección al mapa del prompt:** `~/.dsh/settings.yaml` **no existe** en HP15; sólo hay `settings.yaml.bak-*`. El consumidor real es `~/.dsh/profiles/*/cordis.patch.yml` + la plantilla `SCRIPTS/dsh-settings.yaml` (que `sync_dsh_mcps.py` reescribe). Propagar al fichero fantasma no haría nada.

Cotejo con la Suite 2.0: `suite_cotejo.py` compara los 141 modelos declarados en `FLOYDIA/PUBLIC_REPOS/floydia-suite-desktop/modules/tab_radar.py` contra los catálogos vivos → **29 derivas** (25 IDs inexistentes, 4 contextos distintos), `exit 2`, 105 modelos de proveedor directo (Google/NVIDIA) quedan `NO VERIFICADO` porque su catálogo no está en la sonda. Ejemplos: `minimax/minimax-m3:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `z-ai/glm-5.2:free`, `poolside/laguna-s-2.1:free`, `thinkingmachines/inkling:free`; y `google/gemma-4-26b-a4b-it:free` declarado con 128k cuando el catálogo dice 262 144. Artefacto: `out/suite_cotejo.json`.

---

## 9. Prueba negativa del coste cero (superada)

`out/negative_test.json`:

| Caso | Resultado |
|---|---|
| `openai/gpt-4o` por el cortafuegos C7 | aborta con `C7SyntaxViolationError` (exit 2) |
| `…:nitro` | aborta |
| `:free` fuera de allowlist (`deepseek-r1:free`) | aborta con `C7AllowlistViolationError` |
| ID muerto `nemotron-3-super-120b-a12b` en NIM | **HTTP 404 ruidoso** en 399 ms, sin fallback |
| `GET /usage` antes/después | delta **0,0** en las tres ventanas |

---

## 10. Hallazgos (formato del contrato)

| ID | Sev. | Hallazgo | Evidencia | Impacto web/SEO | Antídoto |
|---|---|---|---|---|---|
| H-01 | Alta | GO trunca artefactos largos por razonamiento (2,9–5,5k tokens) | `out/t1_diag.json` | hero/landing fallidos en GO, 3/3 en FREE | `max_tokens ≥ 12k` o maquetar en FREE |
| H-02 | Alta | Ruta FREE de keyword (nano-omni) falla aritmética: 46 600 ≠ 43 900 | `out/summary.json` | briefs con volúmenes falsos | usar `ultra-550b` + verificador |
| H-03 | Media | `kimi-k3.1-pro` sin tool_calls y falla trampa | `out/f1_probe.json` | el rol «R3 con gate» no es agéntico | retirar de la ruta |
| H-04 | Alta | 3 cifras de bolsa: 60 / 170 / 1 320 | `harness_mode.json:19,340`; `f-harness:53` | dashboards y alertas sobre base falsa | purga §5 del JSON |
| H-05 | Alta | Allowlist 4/10 muerta + saldo real −0,46 $ | `out/freshness_report.json`; `/credits` | FREE falla cerrado o gasta de más | regenerar desde registro |
| H-06 | Media | 82/82 nombres con gramática vieja; 5 ctx mentidos | `out/model_names_lint.json` | selección de modelo por contexto erróneo | lint + generación |
| H-07 | Alta | `crawl4ai` en SSOT `disabled:true`, en Hermes habilitado y sin conectar (30,2 s) | `hermes mcp test` | crawl on-page caído sin aviso | deshabilitar o timeout 60 s |
| H-08 | Media | `floydia-scraper` conecta en 19,4 s | `hermes mcp test` | roza el reloj de control 20 s | precalentar venv |
| H-09 | Media | Skills contradicen SSOT en 6 puntos | §4.1 | decisiones con cifras viejas | parche de skill (propuesto) |
| H-10 | Media | 170/173 handoffs sin lector | §7.6 | amnesia entre sesiones | índice de handoffs + lectura perezosa |
| H-11 | Baja | `~/.dsh/settings.yaml` no existe | `ls ~/.dsh` | propagación a fichero fantasma | documentar consumidor real |
| H-12 | Media | `hermes` apunta auxiliares de pago en `review`/`goal_judge`/`kanban_decomposer` | `config.yaml` | FREE no es $0 si corre kanban | re-apuntar a NIM |

---

## 11. Efectividad

| Métrica | GO | FREE |
|---|---|---|
| Tareas superadas (estricto) | 7/8 | 7/8 |
| Retrabajo (reps fallidas / totales) | 3/24 | 1/24 |
| Latencia p50 por tarea | 1,6–28,7 s | 0,2–5,7 s |
| Coste por 8 entregables | **0,02825 $** | **0,00 $** |
| Escalaciones `free_insufficient` | — | 0 (no se ejercitó el escape) |

Coste humano por entregable aceptado: no medido (requiere sesiones reales, no banco sintético) → `NO VERIFICADO`.

---

## 12. Veredicto y siguiente acción

**AMARILLO.** El modo FREE es $0,00 verificable, la prueba negativa pasa y las 8 tareas se completan en ambos modos con routing corregido. Bloquean el verde: (a) las tres cifras de bolsa y la allowlist podrida, (b) `crawl4ai` caído, (c) 82 nombres no conformes, (d) Recall@1 6/10.

**Siguiente acción (una sola):** aplicar el token para (1) purgar 1320/170 → 60 $, (2) regenerar `providers/c7_allowlist.yaml` desde el registro, (3) corregir los 6 puntos de la skill `f-harness` y los auxiliares de pago de Hermes. Eso convierte H-04, H-05, H-09 y H-12 en cerrados sin tocar routing ni HP45.

---

### Anexo — Cómo reproducir

```bash
cd <PROYECTO>/scratch/harness_v51
python3 f2_freshness.py                 # frescura + allowlist + skills
python3 model_state_registry.py --build # registro con TTL
python3 model_state_registry.py --lint  # exit 2 si deriva
REPS=3 python3 bench_v51.py             # banco GO/FREE (≈0,12 $)
python3 f1_probe.py                     # inventario tools/visión/trampa
python3 negative_test.py                # prueba negativa del coste cero
python3 recall_test.py                  # Recall@1 sin modelo grande
```

Hashes de los fixtures: `fixtures/SHA256SUMS.json`. Ningún fichero de SSOT fue modificado.


---

# APLICADO — 2026-11-06 23:33–23:45 (token humano: opción 3, «usa DeepSeek»)

Todo con backup `.bak-<ts>` junto al fichero. `opencode.jsonc` **no se tocó** (md5 `2a7dcfd7…` idéntico).

| # | Cambio | Verificación real |
|---|---|---|
| A1 | `harness_mode.json`: `total_monthly_allowance_usd` 1320.0 → **60.0**; notas reescritas (bolsa única compartida; 170/1320 sin significado) | 15 rutas cambiadas listadas; `json.load` OK |
| A2 | `monitor_opencode_go.py`: deja de sumar carteras (sumaba 870/1320); lee `shared_windows_usd.mensual` | `load_caps()` → `allowance_total 60.0 · declarado 60.0 · inconsistente False` |
| A3 | `providers/c7_allowlist.yaml` **regenerada** por `SCRIPTS/gen_c7_allowlist.py` desde `/api/v1/models` | 13 free con tools de 424; 4 IDs muertos fuera; `stealth/crouton-alpha` 1 M visión incluido |
| A4 | 10 slots `auxiliary.*` de Hermes → `opencode-go/deepseek-v4.1-flash` (DeepSeek, C7, orden humana); `vision` queda en `nim_local/diffusiongemma-26b` | `hermes config get auxiliary.title_generation` → `opencode-go / deepseek-v4.1-flash` |
| A5 | `fallback_providers` → `nim_local/deepseek-ai/deepseek-v4.1-flash`, luego `opencode-go/deepseek-v4-pro` (eran Nemotron) | `hermes config get fallback_providers` |
| A6 | `crawl4ai` → `enabled: false` (arranque 30,2 s) | `hermes mcp list` → `crawl4ai … ✗ disabled` |
| A7 | `f-harness/SKILL.md` 5 correcciones (`$170`, `allowance = 4 × list_cost`, M, allowlist, identidad de motor) · `f-scraper` 1 (modelo NIM muerto) | backups + asserts por cadena |
| A8 | `routing_policy.roles`: `trivial_y_fondo` y `trabajo_estandar` → DeepSeek; `auxiliares_hermes` → DeepSeek con excepción de visión | diff estructural de 15 rutas |

## Estado de la ruta DeepSeek, medido después de aplicar

| Ruta | Resultado |
|---|---|
| `opencode-go/deepseek-v4-pro` | **200 · 1 941 ms** |
| `opencode-go/deepseek-v4.1-flash` | **429 upstream «overloaded»** ×5 en 4 min (ventana peak 01–04 UTC) |
| `nim_local/deepseek-ai/deepseek-v4.1-flash` | **200 · 1 210 ms** ($0; con `max_tokens` 30 devuelve texto vacío: el razonamiento consume el presupuesto) |

**Riesgo vivo**: los auxiliares apuntan a `deepseek-v4.1-flash` por GO y ese modelo está 429 en peak. El fallback ya está en DeepSeek (`nim_local` → `v4-pro`), pero la primera llamada puede fallar. Mitigación pendiente (una línea): mover los 10 auxiliares a `nim_local/deepseek-ai/deepseek-v4.1-flash` ($0) y dejar GO solo para el modelo principal.

## Nomenclatura: NO aplicada (bloqueada en la raíz)

`SCRIPTS/apply_model_names.py` (dry-run verificado) reescribe `[ESTADO][CTX][MODO]` desde el registro. **No se aplicó**: 67 de 82 modelos tienen `ctx_real = None` (la sonda no midió contexto) y 4 tienen conflicto real (`glm-5.3-flash` 1 M vs 128k declarado; `claude-haiku-5-5` 1 M vs 200k). Aplicar sólo 15 nombres produciría una gramática mixta: peor que el estado actual. Requiere medir `ctx_real` primero.


---

# APLICADO 2 — 2026-11-07 00:02 (token: «sí a todo»)

| # | Cambio | Verificación real |
|---|---|---|
| A9 | 12 slots `auxiliary.*` → DeepSeek (ver A13: el reparto final es Pro donde decide, GLM flash donde solo formatea); `vision` en `diffusiongemma` | `hermes config get auxiliary.*` |
| A10 | `apply_model_names.py --apply`: **82 nombres** `[ESTADO][CTX][MODO]`, 9 `limit.context` purgados al valor del catálogo, 3 bloques con ID inexistente eliminados (79 modelos) | `--lint` → `{}` exit 0 · JSONC válido |
| A11 | `small_model` → `nim_local/deepseek-ai/deepseek-v4.1-flash` (era Nemotron nano-omni) | `json.load` del JSONC |
| A12 | **HP45**: backup remoto `.bak-20261107-000229`, `sync_models_hp45.sh` (4 archivos), verificación | 3 md5 idénticos local↔remoto · canario `deepseek-v4.1-flash` → `CANARY-OK` · proxy `ok`, 4 cuentas |

## Preflight de HP45 (lo que un checksum no cubre)

| Check | Resultado |
|---|---|
| Host / intérprete | `mx` · Python **3.13.5** |
| Proxy y dependencia real | `~/.local/share/nvidia-proxy/venv/bin/python` · `aiohttp 3.14.5` |
| Disco | 31 G libres (71 % usado) |
| Proxy health | `{"status":"ok","available_accounts":4}` |
| Checksums | `.config/opencode/opencode.jsonc`, `.hermes/config.yaml`, `provider_models_cache.json` → **iguales** |
| Canario end-to-end | `deepseek-ai/deepseek-v4.1-flash` → `CANARY-OK`, 47 tokens |

**Gap declarado**: `~/.dsh/settings.yaml` no existe en HP15, así que el de HP45 **no se actualizó** (queda en su versión previa). El consumidor real de DSH es `~/.dsh/profiles/*/cordis.patch.yml`; propagarlo exige decidir antes cuál es el SSOT de DSH.

## A13 — Por qué los auxiliares NO quedaron todos en DeepSeek flash

Medido después de aplicar, con el modelo ya en producción:

| Modelo | `max_tokens` | Resultado real |
|---|---|---|
| `nim_local/deepseek-v4.1-flash` | 60 | 1 222 ms · `out=60` · `finish=length` · **contenido vacío** |
| `nim_local/deepseek-v4.1-flash` | 150 | 1 569 ms · `out=150` · `finish=length` · **contenido vacío** |
| `nim_local/deepseek-v4.1-flash` | 400 | **429 circuit breaker «repetitive»** (bucle de razonamiento) |
| `opencode-go/deepseek-v4-pro` | 80 / 200 | 7 185 / 7 819 ms · `finish=stop` · título correcto · 397-479 tokens |
| `opencode-go/deepseek-v4.1-flash` | 200 | **429 overloaded** (ventana peak) |

Un modelo que razona no sirve para salidas de 4 palabras: gasta el presupuesto pensando y devuelve vacío.
Por eso el reparto final es **DeepSeek Pro en los tres slots que deciden** (`kanban_decomposer`, `goal_judge`,
`review`) y **GLM 5.3 Flash en los diez que solo formatean** (título, compresión, triage, voz): $0 y 0,84 s.
`deepseek-v4.1-flash` queda como **fallback** y como modelo de trabajo largo, donde sí rinde.

## Nomenclatura: del bloqueo a la aplicación

El bloqueo era real: 63 de 82 modelos tenían `ctx_real = null` y 4 contradecían el catálogo. Se resolvió
en tres pasos medidos: `refresh_ctx_from_catalog.py` (19 modelos con límite publicado), etiqueta `?` para
los 60 que no lo publican, y purga de los 9 `limit.context` falsos. El lint pasó de **82 hallazgos** a **0**,
y de paso se corrigió a sí mismo: comparaba cifras crudas (5 falsos positivos) y marcaba duplicados entre
proveedores distintos.


---

# BANCO PUBLICABLE §6 — ejecutado 2026-11-07 (ciego, congelado, McNemar)

`scratch/harness_v51/bench_publicable.py` · fixtures en `qa/fixtures/harness_v5/` con manifiesto de
hashes · mocks de herramientas servidos por `mcp_vcr.json` (mismos bytes en ambos modos) · orden
aleatorizado `seed=42` · 3 repeticiones · frío/caliente separados · **evaluación ciega**: el evaluador
recibe `(anon_id, tarea, texto)` y nunca el modo · rúbrica congelada **antes** de correr.

| Tarea | GO (pass_rate) | FREE (pass_rate) |
|---|---|---|
| T1_hero | 0 % | 0 % |
| T2_cls | 100 % | 67 % |
| T3_schema | 100 % | 67 % |
| T4_onpage | 100 % | 67 % |
| T5_brief | 100 % | 67 % |
| T6_css | 33 % | 67 % |
| T7_vision | 100 % | 100 % |
| T8_tools | 100 % | 67 % |

**Totales `pass_all`**: GO **6/8** (0,0223 $) · FREE **1/8** (0,0040 $) · McNemar `p = 0,0625`
(b=5 tareas solo-GO, c=0 solo-FREE) → con n=8 **no hay significancia**: es regresión, no ranking.

**Validación del resultado**: en la primera pasada 7 de 48 llamadas murieron con `429 circuit breaker`
del proxy, así que el brazo FREE se re-midió entero (24 llamadas, `--only FREE`, con espera y reintento
al detectar el breaker). El resultado **se reprodujo idéntico** (1/8, mismas tasas por tarea): los cortes
no alteraron el veredicto. Coste total de las tres pasadas: **0,075 $** (0,052 $ de ellas quemadas por un
bug mío al no persistir el texto completo; corregido en `bench_v51.run_task` → `text_full`).

## El 0 % del hero no es incapacidad: es presupuesto

Prueba complementaria con el mismo prompt y `max_tokens = 12 000`: **3/3 PASS** (927–2 587 tokens de
razonamiento, 22–32 s). Con los 2 000 tokens congelados en la rúbrica, el razonamiento agota el
presupuesto y `finish_reason` llega en `length`. Evidencia: `out/t1_12k_check.json`.

Consecuencia operativa: cualquier tarea de artefacto en GO necesita `max_tokens ≥ 12 000`; el techo
de 2 000 del banco mide truncamiento, no calidad. La rúbrica v2 (12 k) es un cambio de banco → nueva
corrida y nueva congelación, no una reinterpretación de esta.

## Estado de contexto en el registro (cierre)

| Estado | Modelos | Fuente |
|---|---|---|
| `VERIFIED` | **48** | GO `limit.context`, OpenRouter `context_length`, Google `inputTokenLimit` |
| `UNPUBLISHED` | **31** | NIM `:8088` (24), `opencode/*` legacy (5), Cerebras (2): **no publican límite** |

`UNPUBLISHED` es **estado terminal**, no tarea abierta: el nombre lleva `[?]` y el lint lo acepta solo
cuando `ctx_real` es `null`. Igual para `ESTADO = ?` (existencia no verificada, 7 modelos de proveedores
sin catálogo en la sonda).


---

# BANCO v2 — presupuesto de salida realista (decisión tomada 2026-11-07)

La rúbrica v1 congelaba `max_tokens` en 2 000–2 200, cifra que **mide el techo de tokens, no la
capacidad**: un razonador gasta 900–2 600 tokens antes de escribir. v2 sube el techo al real de cada
tarea (`T1` 12 000 · schema/CSS 8 000 · on-page 6 000 · brief 4 000 · visión 2 000 · tools 3 000) y se
re-congela en `qa/fixtures/harness_v5_2/` — v1 queda intacto y comparable.

| Tarea | GO v2 | FREE v2 | GO v1 | FREE v1 |
|---|---|---|---|---|
| T1_hero | **100 %** | 67 % | 0 % | 0 % |
| T2_cls | **100 %** | 67 % | 100 % | 67 % |
| T3_schema | **100 %** | 67 % | 100 % | 67 % |
| T4_onpage | **100 %** | 67 % | 100 % | 67 % |
| T5_brief | **100 %** | 67 % | 100 % | 67 % |
| T6_css | **100 %** | 67 % | 33 % | 67 % |
| T7_vision | **100 %** | 100 % | 100 % | 100 % |
| T8_tools | **100 %** | 67 % | 100 % | 67 % |

**GO 8/8 `pass_all`** (0,0234 $) · **FREE 1/8 `pass_all`**, con 67 % de acierto por repetición en 6 de
8 tareas · McNemar **b=7, c=0, p=0,0156** → ahora **sí hay diferencia significativa** con n=8.

## Lectura correcta

- El techo de tokens era el fallo de GO: con 12 000 pasa de 0/8 a **8/8** en el hero. Aplicado al SSOT
  (`routing_policy.presupuesto_salida`).
- FREE no es incapaz: es **inestable** (2 de 3 reps). Un reintento automático por tarea sube la
  fiabilidad efectiva de 67 % a ~89 % a $0, y el segundo fallo escala a GO con `reason=free_insufficient`
  (ya previsto en la guarda 5). Se mantiene DeepSeek en el carril FREE por orden del operador.
