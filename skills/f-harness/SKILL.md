---
name: f-harness
description: "Centro de control unificado del Harness FloydIA (antes f-harness + f-harness-select + f-harness-workflow, fusionados 2026-10-13). Cuatro modos: (1) Operativa/SRE — routing de 11 motores $0.00, doctor de DSH, telemetría; (2) Selector de MODO — conmutar las 6 cadenas de prioridades (AGY, Nemotron, Kilo, Cloudflare, Pool Free); (3) Metodología WORKFLOW — roles Líder/Explorador/Implementador/Revisor para tareas complejas; (4) ESCANEO DE APIs + RANKING — auditoría empírica del .env, ranking de inteligencia y propuesta de redefinición de la cadena. USAR con /f-harness, /harness, /modo, /harness-mode, /harness-select, /harness-workflow, /elegir-modelo, /prioridades, /model-router, /api-scan, /escanear-apis, /ranking-modelos, /redefinir-harness o ante caídas de motores/DSH. NO USAR para descomponer proyectos (eso es f-orquestador-floydia) ni para consultas triviales."
version: 4.2.0
triggers:
  - /f-harness
  - /harness
  - /f-harness-select
  - /harness-select
  - /f-harness-workflow
  - /harness-workflow
  - /modo
  - /harness-mode
  - /elegir-modelo
  - /prioridades
  - /model-router
  - /routing
  - /api-scan
  - /escanear-apis
  - /ranking-modelos
  - /auditar-apis
  - /redefinir-harness
  - /harness-api-scan
  - harness floydia
  - cadena de motores
  - cambiar modo del harness
  - cambiar orden de motores
  - deepseek no arranca
  - dsh no arranca
  - dsh se cae
  - harness doctor
  - reparar dsh
  - arnes agéntico
  - harness-workflow
---

# Skill: f-harness — Centro Unificado del Harness FloydIA

> **Estado del harness (2026-10-29)**: el sistema vivo es **v4.3.4-ENTERPRISE · Modo 2
> `opencode_go_triad_r3_gate`** con tríada OpenCode Go de pago por allowance. Las secciones
> marcadas v4.1 son historia: manda el *Resumen operativo* y el SSOT `harness_mode.json`.
> Antes de citar precios, límites o modelos, leerlos del SSOT, no de este texto.
>
> **Fusión 2026-10-13**: unifica `f-harness` (operativa SRE), `f-harness-select` (selector de modo) y `f-harness-workflow` (metodología de roles). Cuerpos íntegros preservados en `references/` (carga bajo demanda).
>
> **Frontera con f-orquestador-floydia (INMUTABLE)**: este skill NO descompone proyectos ni define arquitectura. `f-orquestador-floydia` es el Arquitecto Director (diseña y delega); `f-harness` modo WORKFLOW gobierna la **ejecución** multi-agente de una tarea compleja ya definida (roles, evidencia, tests). Si la petición es "orquesta este proyecto", derivar a `f-orquestador-floydia`.

## 🎯 Enrutamiento interno (Regla Menu-First Obligatoria)

Al invocar `/f-harness`, `/harness`, `/modo` o cualquiera de sus alias, el agente DEBE:
1. **Preguntar siempre al usuario qué modo de harness desea utilizar** (presentando el selector de los 6 modos o usando `ask_question`).
2. Consultar el estado activo en `SCRIPTS/harness_mode.json`.
3. Ofrecer la activación de motores de pago de OpenCode Go dentro de la bolsa única de \$60 ponderados/mes (12/5h · 30/sem; PAYG bloqueado) si el usuario elige Modo 1 o Frontier.

| Modo | Triggers dominantes | Referencia a leer |
|---|---|---|
| **SELECTOR DE MODO (PREDETERMINADO)** | `/f-harness`, `/harness`, `/modo`, `/harness-mode`, `/f-harness-select`, `/elegir-modelo` | `references/select.md` |
| **OPERATIVA/SRE** | `/harness-doctor`, `/model-router`, caídas DSH, telemetría | `references/operativa.md` |
| **WORKFLOW (metodología)** | `/f-harness-workflow`, tarea compleja multi-agente | `references/workflow.md` |
| **ESCANEO DE APIs + RANKING** | `/api-scan`, `/escanear-apis`, `/ranking-modelos` | `references/api-scan.md` |


## Aliases preservados (transición)

Los antiguos comandos `/f-harness-select` y `/f-harness-workflow` siguen vivos como triggers de este skill y rutean a los modos 2 y 3 directamente. Las carpetas `f-harness-select/` y `f-harness-workflow/` originales viven en `.agents/archived-skills/fusionados-20261013/` (restaurables).

## ⚡ Resumen operativo (sin cargar referencias)

- **Modo activo del harness**: `cat SCRIPTS/harness_mode.json` · cambiar: `bash SCRIPTS/harness_mode.sh <N> < /dev/null` (modos 1–6, ver `references/select.md`).
- **Doctor de motores/DSH**: `python3 SCRIPTS/harness_doctor.py` (pasivo, $0.00).
- **Medidor de la asignación OpenCode Go** (antídoto de la brecha 2026-10-29): `python3 SCRIPTS/monitor_opencode_go.py --json` lee `~/.local/share/opencode/opencode.db` (tabla `message`) y compara contra `subscription_pool.model_carteras` en las ventanas 5 h / 7 d / mes. Dos cifras siempre: `cost_reportado` (hecho) y `cost_estimado` (reportado + tokens sin coste × tarifa calibrada). Veredicto duro (CRIT/EXCEDIDO) **sólo** con tarifa propia (`confianza=alta`); con `baja`/`proxy` se imputa AVISO. `--guard` → exit 2 en CRIT/EXCEDIDO.
- **Límites de OpenCode Go (docs oficiales, verificado 2026-10-29)**: los topes NO son independientes — 5 h = 20 % del mensual, semana = 50 %, mes = 100 %; se derivan del mensual del modelo, nunca se fijan a mano. El consumo cuenta por `usage.opencode.allowance`, y **`allowance = list_cost × 60 / monthly_limit_usd`** (la bolsa son \$60 por modelo; 170 y 1320 son sumas sin significado). DeepSeek V4 Pro/Flash duplican precio en peak (01-04 y 06-10 UTC, L-V). M (monthly_limit_usd, valor list de la bolsa): V4.1 Flash $80 · V4 Pro $15 · MiniMax M3 $60 · MiniMax M3.1 Flash $20 · Kimi K3.1 Pro $15 (el más caro: $8,43/1M). Antes de recomendar reasignar carga, leer `subscription_pool.precios_reales` del SSOT: no inventar precios por parecido de nombre.
- **Carriles medidos (2026-10-29, banco de 5 tareas)**: `deepseek-v4.1-flash` (pago, 1.4-1.7 s) **acierta** las trampas de razonamiento; `nemotron-3.5-lightning-30b` (NIM $0, ~250 ms) es 3/3 en tareas fáciles pero **falla** la trampa de velocidad relativa (dio 180 donde son 120); `nemotron-3-ultra-550b` (NIM $0) acierta pero tarda **9 s** en esa misma trampa. Conclusión operativa: carril rápido = lightning para volumen/auxiliar; carril de pensar = flash (o ultra si se acepta la latencia). Hermes **no** auto-escala por dificultad: el `fallback` solo dispara ante fallo; el tiering C0-C6 vive en `harness_dispatch.py` para trabajo delegado.
- **Guardia programada**: `python3 SCRIPTS/harness_daily_guard.py` = proxy + doctor + canario + gasto + **barrido de modelos gratis de OpenRouter** (`or_free_watch.py`) + **cupos por cuenta OpenRouter**, con Telegram sólo si ≠ VERDE (ROJO = infra/motor caído o credencial rechazada; AMARILLO = presupuesto o transitorio 429/5xx) y dedupe 6 h / 24 h. En cron: `0 */2 * * * monitor_opencode_go.py --alert --quiet` y `15 7,19 * * * harness_daily_guard.py`.
- **Veto de sondas**: `providers/probe_veto.yaml` (SSOT) + `SCRIPTS/probe_veto.py`. Bloquea modelos que cobran por petición/herramienta (`perplexity`, `morph`, `lyria`) en `c7_free_client.py`, en el canario y en la propuesta de `harness_api_scan.py`. Motivo medido: `perplexity/sonar-deep-research` = $0.286 por una sonda de 24 tokens, invisible en `usage.cost`.
- **Escaneo de APIs + ranking + propuesta de cadena**: `python3 SCRIPTS/harness_api_scan.py --scan --rank --propose` (R1, $0.00, **nunca auto-aplica**; detalle en `references/api-scan.md`).
- **Regla #vetado**: NUNCA borrar líneas sueltas con `sed` en `~/.dsh/settings.yaml` — sustituir el ID del modelo por el sucesor vivo.
- **Parser canónico del `.env`**: `SCRIPTS/env_loader.py` (`env_line`, `load_env`). Prohibido reintroducir `split("=", 1)`: el SSOT admite comentarios inline `# endpoint:`.
- **Evidencia antes de Afirmar**: ninguna conmutación o rescate se cierra sin mostrar el JSON/exit 0 resultante.
- **Obligación en Auditorías de APIs**: Toda evaluación, benchmarking o redefinición del arnés DEBE incluir por defecto pruebas activas de NVIDIA NIM (4 cuentas C1, C2, C7, C9 y proxy local :8088) y OpenRouter C7 (cuenta fondeada protegida, 1.000 req/día en modelos :free) junto a C1..C6. Prohibido omitirlas o darlas por supuestas.
- **Tombstone de motor**: `Kimi K3` está **EOL** (`410 Gone` en NIM, 2026-10-15) y no figura en ninguna cadena. La API directa de Moonshot es **de pago** y queda fuera del harness. Sustitutos: `nemotron-3-ultra-550b-a55b` y `nemotron-3.5-super-vl-120b-a12b`. No reintroducirlo. **Re-verificado 2026-11-06** a petición del operador («Kimi K3 gratis en NIM»): `kimi-k3` sigue 410, `kimi-k3.1-pro` es solo playground («no API key will authorize it») y `kimi-k2.6` figura en `/v1/models` pero devuelve `404 Function … Not found for account`. La ventana gratis de Kimi K3 fue 2026-09-22 → 2026-10-15; hoy no hay Kimi gratis en NIM.
- **Catálogo free de NIM (auditado 2026-11-06)**: 84 ids idénticos en C1/C2/C7/C9 y **15 endpoints gratis servibles de 17 probados**, no los 4 Nemotron que usa la cadena. Límite oficial: 40 RPM y sin coste por token (`build.nvidia.com/settings/credits`); el «10 000/día» de agregadores no está publicado. Medido con `SCRIPTS/nim_free_probe.py`: `google/diffusiongemma-26b-a4b-it` 493 ms y acierta la trampa 20/3 en 428 ms (mejor visión 525 ms y tools 3/3); `nemotron-3-nano-omni-30b-a3b-reasoning` 638 ms, tools 3/3 y trampa en 3,8 s (mejor `small_model`); `nemotron-3.5-bolt-e4b` 395 ms y tools 3/3 pero falla aritmética (trampa 16); `z-ai/glm-5.3-flash` 80,6 s en frío y **0,84 s caliente** (sustituye al glm de pago en los 10 slots auxiliares de Hermes); `deepseek-ai/deepseek-v4.1-flash` vivo y gratis pero con **159 s de TTFT** (solo lote nocturno, y el proxy lo tapa con `NIM_PROXY_NATIVE_DEEPSEEK=0`); `mistral-large-4-1t-a52b` timeout 300 s en la trampa; `poolside/laguna-xs-2.1` falla la trampa y no tiene multimodal.
- **Arranque frío de NIM = 80-160 s por cuenta y modelo.** Los tres «muertos por timeout» de auditorías anteriores (deepseek 159 s, glm 80,6 s, gpt-oss-20b 141,6 s) devuelven 200 y el modelo pedido si se espera. `FAST_HINTS` del proxy cortaba esos arranques en 25 s (35 sin streaming); desde el 2026-11-06 el perfil `fast` usa `read=90 s` y `default` 120 s. Antes de emitir veredicto, segunda llamada o espera larga — y si se cablea un flash a $0, subir ese perfil a ≥90 s.
- **La trampa 20/3 no distingue tamaño, distingue presupuesto.** `nemotron-3.5-lightning` y `nemotron-3.5-super-vl` «fallaban» solo porque `max_tokens=1500` se agotaba en el pensamiento (`reasoning_tokens == max_tokens`); con 6 000 aciertan en 15,3 s y 11,0 s. Corrige la nota de 2026-10-29 que los daba por incorrectos.
- **`nvidia/nemotron-3-super-120b-a12b` NO se sirve**: `404 Function not found` en C1, C2 y C7 (dos confirmaciones) desde el recorte del tier free del 2026-10-20. **Corregido 2026-11-06** en HP15 y HP45: retirado de `routing_policy`, del catálogo del SSOT (`~/.config/opencode/opencode.jsonc`), del DSH y de `fallback_providers` de Hermes; sustituto `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`. El alias `MODEL_FALLBACKS` del proxy que lo disfrazaba a super-vl también se retiró: ahora el id muerto responde **404 loud**.
- **`fallback:` y `small_model` NO son claves de Hermes.** El runtime resuelve la cadena en `fallback_providers`/`fallback_model` (`hermes_cli/fallback_config.py`) y los auxiliares en `auxiliary.*`; el `fallback:` que traía el config era decorativo y el fallback real llevaba tiempo sin lector. Al tocar modelos de Hermes, escribir en `fallback_providers` y comprobarlo con `hermes config get`. `hermes config set` acepta listas/dicts JSON y es la vía obligatoria: el editor de ficheros se niega a tocar `~/.hermes/config.yaml`.
- **Cableado $0 vigente (2026-11-06)**: `auxiliary.vision` = `nim_local/google/diffusiongemma-26b-a4b-it` (795 ms, 3/3 cifras en panel real; super-vl 2 332 ms y confundía filas); 10 slots de formato (`compression`, `title_generation`, `approval`, `mcp`, `skills_hub`, `profile_describer`, `monitor`, `curator`, `triage_specifier`, `voice_chat`) = `nim_local/z-ai/glm-5.3-flash` ($0, 0,84 s) y los 3 que DECIDEN (`kanban_decomposer`, `goal_judge`, `review`) = `opencode-go/deepseek-v4-pro` — un razonador no sirve para salidas de 60-150 tokens: devuelve `content: ""`; `small_model` y subagentes de OpenCode = `nano-omni`. Antigravity no enruta modelos por NIM (solo MCP), no hay nada que cambiar ahí.
- **El daemon del proxy elige intérprete**: `dsh_proxy_daemon.sh` usa `~/.local/share/nvidia-proxy/venv/bin/python` si existe (`NIM_PROXY_PYTHON` lo override). HP45 no tiene `aiohttp` en el `python3` del sistema y el proxy moría en cada reinicio. HP45 corría además un `nvidia_rate_limiter.py` del 2026-10-29 porque Dropbox no estaba replicando ese fichero: tras tocar el proxy, `rsync` explícito + `dsh_proxy_daemon.sh restart` en ambas máquinas.
- **Dónde consultar el estado completo**: `memory-bank/technical/HARNESS_FLOYDIA_V41_INDICE.md` (índice de una página) · `memory-bank/journal/2026-10-21_harness_floydia_v41_handoff.md` (handoff) · NotebookLM *"FLOYDIA - HARNESS v4.1 (SSOT 2026-10-21)"* (id `a94ef989-9cc9-4a01-a7c9-bac58fa6e038`).
- **SSOT del enjambre MCP**: `~/.gemini/config/mcp_config.json` es el árbitro; los clientes (Antigravity, OpenCode, Hermes, DSH) son config DERIVADA. `hermes mcp add` NO actualiza el SSOT, así que tras añadir un MCP por fuera hay que pulsar **🧬 Descubrir enjambre** en el cockpit (o llamar `discover_swarm_sources()` + `merge_swarm_into_ssot()`), o el servidor desaparece en la siguiente propagación. Un servidor HTTP (`serverUrl`) se renderiza como `url:` + `transport: http`; nunca `command:` vacío (deja el YAML inválido y tumba `hermes mcp list` con `TypeError: NoneType has no len()`).
- **Coste medido del enjambre (2026-11-04)**: ≈85 MB RSS por tenant Novamira (`node mcp-wordpress-remote`), ≈130-300 MB por crawl4ai con hijos; 17 servidores en 3 clientes = 3,2 GB. Para trabajar un sitio concreto usar el perfil canónico `cliente-wp` (un tenant + Obsidian + Crawl4AI) en vez de los 6 a la vez.
- **zram de esta máquina (ajustado 2026-11-04)**: `/etc/default/zramswap` con `ALGO=zstd`, `PERCENT=50` (5,8 GB) y `PRIORITY=100`; swapfile 3 GB como segundo nivel. `PERCENT=100` (valor anterior) era peligroso: un zram lleno con ratio 3:1 ocupa ~4 GB de RAM real en un equipo de 11. Con `vm.swappiness=100` + `vm.page-cluster=0` (`/etc/sysctl.d/99-zram-swappiness.conf`) el ratio medido sube a **3,89x**. Reinicio sin systemd: `/etc/init.d/zramswap restart`. `swapon`/`zramctl` viven en `/sbin` y NO están en el PATH del agente: llamarlos con ruta absoluta.
- **Motor por defecto del sistema**: el SSOT es `~/.hermes/config.yaml` (`hermes config get model`). Hoy **2026-11-07**: `model = deepseek-v4.1-flash` (provider `opencode-go`), `small_model = nim_local/deepseek-ai/deepseek-v4.1-flash` y `fallback_providers = [nim_local/deepseek-v4.1-flash, opencode-go/deepseek-v4-pro, nim_local/glm-5.3-flash]`. La nota anterior (`minimax/minimax-m3.1-flash:free` en los 4 campos) está **caducada** y ese ID **ya no existe** en el catálogo de OpenRouter: verificarlo con `GET /api/v1/models` antes de citarlo.
- **Allowlist C7 (regenerada 2026-11-07)**: `providers/c7_allowlist.yaml` se genera con `SCRIPTS/gen_c7_allowlist.py` desde `/api/v1/models`; prohibido editarla a mano. Medido: **13 IDs free con tools** de 424 del catálogo (criterio precio 0 + tools, no routers). Mayor contexto: `stealth/crouton-alpha` (1 M, visión). La versión anterior (2026-10-02) tenía 4 IDs muertos: `minimax-m3.1-flash:free`, `stealth/space-bunny-alpha`, `nemotron-3-super-120b-a12b:free`, `laguna-s-2.1:free`.
- **Identidad de motor**: la reescritura atribuida al proxy (`deepseek-ai/deepseek-v4.1-flash` → `nemotron-3.5-super-120b`) **no se reprodujo** el 2026-11-07: la respuesta devuelve `model: deepseek-v4.1-flash` y emite tool_calls. Queda `NO VERIFICADO` como comportamiento general; verificar con `python3 SCRIPTS/harness_api_scan.py --canary` antes de atribuir capacidades.

## Runbook v5.1 — de la auditoría al SSOT (aplicado 2026-11-07)

Pipeline determinista. Cada paso deja un artefacto en `scratch/harness_v51/out/` y **no aplica nada**
hasta el paso 5, que exige token humano (R3).

| # | Comando | Artefacto | Gate |
|---|---|---|---|
| 1 | `python3 scratch/harness_v51/model_state_registry.py --build` | `out/model_state_registry.json` (79 entradas, TTL 7 d) | `existe` por catálogo vivo, no por config |
| 2 | `python3 SCRIPTS/refresh_ctx_from_catalog.py` | `ctx_real` desde `limit.context` (GO), `context_length` (OR) y `inputTokenLimit` (Google) | **48 `VERIFIED` · 31 `UNPUBLISHED`** → `ctx_status` + `[?]` terminal |
| 3 | `python3 SCRIPTS/apply_model_names.py [--apply]` | nombres `[ESTADO][CTX][MODO]` + purga de `limit.context` falso | dry-run primero; backup `.bak-<ts>` |
| 4 | `python3 scratch/harness_v51/model_state_registry.py --lint` | `out/model_names_lint.json` | **exit 0** o no se propaga |
| 5 | `bash SCRIPTS/sync_models_hp45.sh 192.168.1.10 tec` | 9 ficheros a HP45 | 8 md5 idénticos + canario `CANARY-OK` + `/health` 4 cuentas |
| 6 | `python3 SCRIPTS/gen_c7_allowlist.py` · `suite_overlay_gen.py` · `suite_cotejo.py` | allowlist C7 · overlay Suite · cotejo | cotejo `SIN_DERIVA` (exit 0) |
| 7 | `python3 SCRIPTS/harness_switch.py --bench 40` | `out/switch_bench.json` | conmutación GO⇄FREE atómica (`os.replace`), P99 ≤ 5 s |
| 8 | `python3 scratch/harness_v51/recall_test.py` | `out/recall_test.json` | Recall@1 ≥ 9/10 con `SCRIPTS/memory_recall.py` |
| 9 | `QA_DIR=…/harness_v5_2 BENCH_TAG=_v2 python3 scratch/harness_v51/bench_publicable.py --run --evaluate [--only FREE]` | `out/publicable_*_v2.json` | ciego, seed 42, ≥3 reps, McNemar; `max_tokens` por techo real. **Resultado v2: GO 8/8 · FREE 1/8 · p=0,0156** |
| 10 | `python3 SCRIPTS/peak_guard.py --apply` (cron */30) | `.session/peak_guard_state.json` | en peak 01-04/06-10 UTC el principal baja a `v4-pro` |
| 11 | `python3 SCRIPTS/harness_dashboard.py` | `scratch/harness_v51/dashboard.html` | cifras leídas de los artefactos, ninguna a mano |

Invariantes que el runbook hace cumplir:

- **Una sola verdad numérica**: la bolsa son 60 $ ponderados (`shared_windows_usd.mensual`); el monitor
  NO suma carteras (sumaba 870 y antes 1 320).
- **Ningún nombre se teclea**: `ESTADO` y `CTX` salen del registro; `?` sólo si `ctx_real` es null.
- **La Suite consume, no posee**: `cache/models_overlay.json` retira los ids muertos al cargar
  (`tab_radar.py`), con fallback a la lista literal si el overlay falta.
- **DSH no tiene `settings.yaml`**: el SSOT son `~/.dsh/profiles/*/cordis.patch.yml` + `deprecated_models.yaml`.
- **`rsync --mkpath`**: sin él, los perfiles nuevos de DSH fallan en silencio en HP45.
- **La conmutación se mide, no se describe**: `harness_switch.py` reescribe `model:` con `os.replace`
  (nunca un config a medias) y publica P50/P95/P99; con 80 cambios dio P99 **1,98 ms**.
- **El presupuesto de salida es parte del routing**: `routing_policy.presupuesto_salida` fija 12 000 para
  artefactos, 8 000 schema/CSS, 6 000 on-page, 4 000 brief, 2 000 visión, 3 000 tools. Con 2 000 el hero
  daba 0/8 y con 12 000 dio **8/8** — mismo modelo, mismo prompt.
- **Un banco con `max_tokens` corto mide truncamiento, no calidad**: el hero dio 0 % con 2 000 tokens y
  **3/3** con 12 000 (razonamiento 927–2 587). Al comparar modos, fija el presupuesto de salida en el
  techo real de la tarea o el resultado acusará al modelo de un límite de la rúbrica.
- **`?` es un estado, no un pendiente**: `[?][?]` significa «el proveedor no publica límite / no expone
  catálogo». El lint lo exige y lo acepta; inventar la cifra sí es un fallo.
- **Un brazo contaminado se re-mide entero, no se interpreta**: 7 de 48 llamadas murieron con
  `429 circuit breaker` del proxy. `bench_publicable --only FREE` re-mide ese brazo con espera y
  reintento; aquí reprodujo el mismo 1/8, lo que convierte el dato en sólido en vez de dudoso.
- **Inestable ≠ incapaz**: FREE saca 67 % por repetición en 6 de 8 tareas (2 de 3 reps), no un fallo
  sistemático. La respuesta es un reintento automático antes de escalar a GO con
  `reason=free_insufficient` (67 % → ~89 % a $0), no cambiar el modelo ni bajar la rúbrica.
- **El recall no se arregla con un modelo más grande**: con el mismo par de modelos, pasar de
  grep-por-patrón a párrafos puntuados (`memory_recall.py`) y añadir los hechos a `techContext.md`
  llevó 6/10 → **10/10**.
