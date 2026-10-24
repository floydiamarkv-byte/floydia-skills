# Skill: Escaneo de APIs, Ranking de Inteligencia y Redefinición del Harness (`f-harness` modo 4)

> **Propósito**: Auditar empíricamente las APIs disponibles en el entorno, cruzar esa disponibilidad con rankings de inteligencia de modelos y **proponer** (nunca auto-aplicar) una cadena de motores optimizada.
> **Nivel de riesgo**: R1 (lectura + scripts nuevos) · **Escala a R2** si se escribe `SCRIPTS/harness_mode.json`, `~/.dsh/settings.yaml` o `~/.config/opencode/opencode.jsonc`.
> **Idioma**: Toda la interacción en español.

---

## 🎯 1. Menú de acciones (Menu-First)

Al invocar `/api-scan`, `/escanear-apis`, `/ranking-modelos`, `/auditar-apis` o `/redefinir-harness`, presentar este menú:

```markdown
╔════════════════════════════════════════════════════════════════════════════╗
║     🔬 F-HARNESS MODO 4 — ESCANEO DE APIs + RANKING + REDEFINICIÓN v1.0    ║
║                    Ecosistema FloydIA — Protocolo v28                     ║
╚════════════════════════════════════════════════════════════════════════════╝

1️⃣ 🔍 **Barrido empírico del `.env`** (AUTH + DEDUP + LIVE, $0.00)
   ↳ Estado real de las 226 variables / 67 proveedores: disponible, coste,
     latencia, TTFT y catálogo. Genera JSON+CSV+MD.

2️⃣ 🏆 **Ranking de inteligencia multi-fuente**
   ↳ Artificial Analysis (AA II) + LMArena (Elo BT) + OpenRouter + LiteLLM +
     models.dev. Tablas SEPARADAS por fuente. Nunca un score único.

3️⃣ 📊 **Scoring F3 ponderado + veredictos**
   ↳ 30/25/15/10/10/5/5 con techos duros. Sin benchmark propio → «candidato no
     evaluado» (nunca apto para producción).

4️⃣ 🔗 **Propuesta de cadena por tier** (NO auto-aplica)
   ↳ Las 6 cadenas en las DOS taxonomías (4 tiers + matriz C0–C6) con su mapeo,
     la evidencia que justifica cada cambio y la tabla de retiradas.

5️⃣ 🩺 **Estado del harness + EOL + canario de disponibilidad**
   ↳ `harness_doctor.py` + `model_catalog_scan.py` + canario de 1 llamada real
     por candidato (el catálogo NO implica disponibilidad real).

6️⃣ 💬 **Sentimiento de comunidad (30 días, $0.00)** — veto de modelos
   ↳ HN Algolia + Reddit + Bluesky: volumen, ratio negativo y thread top.

0️⃣ 🚪 **Salir**
```

**Combinación por defecto** al pedir "escanea y decide": `1 → 5 → 2 → 3 → 4`.

---

## 🔒 2. Principios inmutables

### A. Blindaje de coste y credenciales
| Regla | Detalle |
|---|---|
| **$0.00 estricto** | Prioridad a modelos `:free` y créditos incluidos. Prohibido llamar a modelos de pago para pruebas. Sondas a `:free` con `max_tokens ≤ 8`. |
| **C7 blindado** | `C7_OPENROUTER` está fondeada (1.000 req/día `:free`). Pre-flight `GET /api/v2/auth/key`; post-flight comparando `usage` antes/después; si `post_usage > pre_usage` → Dead-Man Switch (`.session/kill_c7`). |
| **Sin secretos** | Nunca copiar valores de `.env`/tokens/claves a prompts, logs, journals o informes. Solo nombres de clave y huellas `[REDACTED]`. |
| **Parser canónico** | `SCRIPTS/env_loader.py` (`env_line`, `load_env`). **Prohibido** `split("=", 1)`: el SSOT admite comentarios inline `# endpoint:`. |
| **Sin reintentos ciegos** | `401/403/402/429` son veredictos, no fallos de red. Timeout se registra aparte. |
| **Cabeceras fuera de `ps`** | Las cabeceras de auth viajan en fichero de config chmod 600, nunca en la línea de comandos. |

### B. Regla epistémica central
> **NO se fusionan dimensiones distintas en un único score.** LMArena mide *preferencia humana* (Elo Bradley-Terry), no exactitud. La latencia/throughput es **por endpoint**: promediar entre proveedores es inválido. "Modelo" ≠ "modelo + andamiaje".
>
> **Vocabulario de estado** (heredado de `rankings_ia.py`): `HECHO` (dato leído de fuente primaria en ESTA ejecución) · `VACIO` (la fuente no tiene ese campo) · `NULO` (la fuente no responde; es fallo de red, no dato).

### C. Dimensiones de disponibilidad (son TRES, no una)
| Eje | Significado | Ejemplo |
|---|---|---|
| **Disponibilidad** | La credencial responde | Moonshot/Kimi = `OPERATIVA` en la auditoría 2026-10-20 |
| **Coste efectivo** | Si consume dinero real | Moonshot/Kimi = **DE PAGO** ($1,65) |
| **Seleccionabilidad** | Cumple ceilings, fiabilidad, diversity de proveedor y cuota | Moonshot/Kimi = **NO SELECCIONABLE** |

> Un proveedor puede ser `OPERATIVA` y aun así estar **excluido** de la cadena. Los tres ejes deben aparecer como columnas separadas en el informe.

### D. Catálogo ≠ disponibilidad
Modelos listados pueden estar muertos al servir (`deepseek-v4-pro` → 410 Gone) y viceversa (`thinkingmachines/inkling-small:free` en catálogo → 403 real con C7). **Antes de proponer un motor: 1 llamada de canario real.** Sin canario → veredicto `no verificado`.

---

## 📚 3. Fuentes de ranking e inteligencia (verificadas)

### 3.1 Artificial Analysis v2 — Intelligence Index (prioridad 1)
| Aspecto | Detalle |
|---|---|
| Endpoints | `GET /api/v2/language/models/free` (Free) · `/api/v2/language/models` (Pro) · `/api/v2/language/models/{id}` (Pro) · `/api/v2/language/models/{id}/performance` (Commercial) |
| Base | `https://artificialanalysis.ai/api/v2` |
| Auth | header `x-api-key: $AA_API_KEY` · sin key → `401` |
| Cuota Free | **100 req / 24 h** (la cifra "1.000/día" es de docs caducas → descartada). Caché diaria obligatoria. `429` → respetar `Retry-After`. |
| Formato | JSON `{status, data, pagination}` · usar `id` (estable), nunca `slug` (cambia) |
| Campos | `evaluations.artificial_analysis_intelligence_index`, `coding_index`, `math_index`, `mmlu_pro`, `gpqa`, `hle`, `livecodebench`, `aime` · `pricing.price_1m_input_tokens` / `price_1m_output_tokens` · `median_output_tokens_per_second` · `median_time_to_first_token_seconds` |
| Obligación | **Atribución a `artificialanalysis.ai`** en todo informe del tier Free |

### 3.2 LMArena — Arena Score (prioridad 2, gratis, sin key)
| Aspecto | Detalle |
|---|---|
| Fuente | Dataset HF `lmarena-ai/leaderboard-dataset` (ODC-BY). Configs: `text`, `text_style_control`, `vision`, `vision_style_control`, `search`, `document`, `webdev`, `text_to_image`, `image_edit`, `text_to_video`, `image_to_video`, `video_edit`, `agent` |
| Splits | `latest` (leaderboard actual) · `full` (serie temporal) |
| Filtro | `category == "overall"` |
| Columnas | `model_name, organization, rating, rating_lower, rating_upper, variance, vote_count, rank, category, leaderboard_publish_date` |
| Agent Arena | `score`, `score_ci_lower`, `score_ci_upper`, `observation_count`, `session_count` |
| Acceso | **Librería `datasets` con reintentos y caché** — la API REST de HF dio `ConnectTimeout` en el entorno. Alternativa de muestreo: `datasets-server.huggingface.co/rows` |
| Baja confianza | `api.wulong.dev` y `oolong-tea-2026/arena-ai-leaderboards` → auxiliares, **nunca** ranking primario |
| Metodología | Bradley-Terry desde 01/2024 · style control desde 05/2025 · re-ponderación por frecuencia desde 07/2025. **Conservar `leaderboard_publish_date`** |

> Los **intervalos de confianza** importan: un modelo con pocos votos no es comparable con uno con miles. El estilo y la verbosidad influyen en el voto humano.

### 3.3 OpenRouter — catálogo vivo (prioridad 3)
| Aspecto | Detalle |
|---|---|
| Endpoints | `GET /api/v1/models` · `/api/v1/models/{author}/{slug}` · `/api/v1/models/{author}/{slug}/endpoints` (EOL real por proveedor) · `/api/v1/generation/{id}` (stats) · `/api/v2/auth/key` (saldo y límites) |
| Auth | **Enviar siempre `Authorization: Bearer`** aunque responda sin key: la respuesta keyless no es contrato estable |
| Cuotas | Data API: **30 req/min y 500 req/día**. Modelos `:free`: ~20 req/min; 50 req/día sin compra histórica; **1.000 req/día tras ≥ 10 USD de créditos** (C7 cumple) |
| Caché | 1 h. Upstream puede devolver 429 con saldo |
| Alias | `id` + `hugging_face_id` = **tabla de alias canónica** para cruzar fuentes |
| Prohibido | `openrouter.ai/rankings` (web) → solo scraping, no es REST: no es dato duro |

### 3.4 Catálogos de precio y capacidad (keyless)
| Fuente | Endpoint | Nota |
|---|---|---|
| LiteLLM | `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json` | ~3 MB, ~4.400 entradas. **Registrar sha256 + fecha** (hash parcial de referencia `cbfb0ceda469d7e5`). No hardcodear el conteo. |
| models.dev | `https://models.dev/api.json` | 232 proveedores: límites, tool-calling, fecha de release |
| HELM | `storage.googleapis.com/crfm-helm-public/.../releases/v1.15.0/{summary,schema,groups,run_specs}.json` | **En mantenimiento desde 2026-06-01** → solo snapshot histórico por release + hash. **Nunca** ranking vivo ni URL `latest`. |

### 3.5 Fuentes MUERTAS — prohibido usarlas
`Open LLM Leaderboard` (archivado 2025-03) · `GitHub Models` (retirado 2026-07-30) · `arena-catalog` (sin mantener) · `chatbot-arena-leaderboard` (sustituido) · `wulong.dev` como ranking primario.

### 3.6 Clasificación de gratuidad (no colapsar categorías)
`gratis local` (Ollama/vLLM/LiteLLM — software, pero hardware y licencia son coste) ≠ `gratis condicionado` (OpenRouter `:free`, Gemini Free Tier, Mistral Free mode, Cloudflare 10.000 neuronas/día reset 00:00 UTC) ≠ `créditos mensuales` (HF Inference Providers 0,10 USD/mes) ≠ `trial` (Cerebras 5 USD/30 días/tarjeta) ≠ `retirado` (GitHub Models) ≠ `no verificado` (Groq free — confirmar en consola antes de prometer).

### 3.7 Control de cuota de fuentes con límite diario
Artificial Analysis (tier Free) limita a **100 peticiones / 24 h**. El orquestador:

1. Captura las cabeceras `X-Ratelimit-Limit` / `X-Ratelimit-Remaining` / `X-Ratelimit-Reset` de cada respuesta y las persiste en `.session/api_scan_cache/cuota.json` (el `reset` es un epoch UNIX; se muestra como fecha legible).
2. Emite un **aviso** cuando quedan **< 20 peticiones** (`AVISO_CUOTA_UMBRAL`), tanto en el informe (sección `## 0. Cuota`) como por stderr. El aviso se calcula desde el estado persistido, así que **también aparece cuando la respuesta vino de la caché** (24 h) y no se gastó cuota.
3. El caché TTL de 24 h hace que el consumo normal sea de ~1 petición/día. **No fuerces `--refresh` en bucle**: cada refresco gasta una petición del día.

Estados posibles del aviso: `CUOTA BAJA` (quedan < 20) · `CUOTA AGOTADA` (quedan 0 → el ranking de esa fuente no se actualizará hasta el reset).

> **Red bloqueada (caso 2026-10-20)**: el A record de DNS de `artificialanalysis.ai` (`76.76.21.21`) expiraba en TCP 80/443 desde esta red, pese a que el sitio respondía 200 en otros IPs del edge de Vercel con el mismo SNI. Resuelto con (a) entrada en `/etc/hosts` y (b) fallback `ALT_IPS` + `_http_get_pinned()` en el orquestador, que reintenta por IP fija manteniendo SNI/Host. **Si una fuente vuelve a dar timeout, no es la clave: es la ruta.**

### 3.8 Sentimiento de comunidad (30 días, $0.00)
| Fuente | Endpoint | Límite |
|---|---|---|
| Hacker News Algolia | `http://hn.algolia.com/api/v1/search_by_date?query=…&tags=comment&numericFilters=created_at_i>{epoch},points>5&hitsPerPage=100` | 10.000 req/h por IP, sin key. Filtrar `created_at_i > now-30d` en cliente |
| Reddit | `https://www.reddit.com/r/{sub}/search.json?q=…&sort=top&t=month&limit=100` | `User-Agent` obligatorio · ~10 req/min anónimo · **403 en IP de datacenter** → fallback RSS (`/r/LocalLLaMA/top/.rss`) u `old.reddit.com` |
| Bluesky | `https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=…&since=…&until=…` | Lecturas públicas sin key |
| X/Twitter | — | Pay-per-use (~$0,005/post) → **no viable** en monitoreo gratuito |

**Queries de detección**: `"silent nerf"`, `"got worse"`, `"degraded"`, `"worse than"`, `"rate limit"`, `"429"`, `"quota exceeded"`, `"best model for coding"`, `"daily driver"`. Normalizar nombres; excluir `-release -announcement -sponsored -deal`; registrar `nbHits` como serie semanal. Skill auxiliar: `last30days`.

---

## 🔬 4. Protocolo de 6 fases: del escaneo a la cadena

### FASE 1 — Barrido empírico (AUTH + DEDUP + LIVE, $0.00)
```bash
python3 SCRIPTS/scan_apis_full.py --trabajadores 10   # AUTH + DEDUP + LIVE → JSON+CSV+MD
python3 SCRIPTS/render_api_reports.py                  # re-renderiza CSV+MD desde el JSON
```
- Solo lectura. Ninguna escritura en WordPress/cPanel/Proxmox/bots.
- Clasificación de fallos: `401/403` → credencial rechazada · `402` → sin saldo · `404` → el MODELO no existe (la credencial puede estar bien) · `429` → rate limit (no es fallo de credencial) · timeout → el motor no completa · vacío → 200 sin contenido útil.
- **Casos que NO son fallo de credencial**: `api.modal.com` responde pero no expone `/v1/models` (la capacidad depende del endpoint del deployment) · Jackett no está en CT114:9117 (responde 400, no es Jackett) · Jellyfin no aparece en la LAN en 8096.
- **Dominios NXDOMAIN confirmados (14 vars huérfanas)**: `api.ollama.ai`, `api.apinex.ai`, `api.airforce.ai`, `api.justworker.ai`, `api.kktoken.ai`, `api.nararouter.ai`, `api.tabitoken.ai` → reportar como *candidatos a purga*; **no purgar sin aprobación del operador** (el `.env` es SSOT).
- **Proxmox**: `Authorization: PVEAPIToken=<token_id>=<clave>` **y** `-k` (certificado autofirmado).
- **DSH siempre por el proxy**: nunca directo a `integrate.api.nvidia.com`. Verificar antes: `curl -s http://127.0.0.1:8088/health`. SSOT: `SCRIPTS/dsh-settings.yaml` con `baseURL: http://127.0.0.1:8088/v1`.
- **Mandato de cobertura (OBLIGATORIO)**: NVIDIA NIM **4 cuentas** (`C1_NVIDIA`, `C2_NVIDIA`, `C7_NVIDIA`, `C9_NVIDIA_API`) + proxy `http://127.0.0.1:8088/v1/models` y `/chat/completions` (`deepseek-ai/deepseek-v4.1-flash`, `nemotron-3.5-lightning`, `nemotron-3.5-super-vl`, `nemotron-3-ultra-550b`) · OpenRouter **C7** (1.000 req/día `:free`) + rotación `C1..C6`. Prohibido omitirlas bajo la asunción de "ya se conocen".
- **`C7_KIMI_PLATFORM_API` es de PAGO**: solo metadatos, nunca inferencia (Contrato #9: doble confirmación humana).

### FASE 2 — Baseline de disponibilidad (contraste contra la última auditoría)
| Métrica | Valor (auditoría 2026-10-20) |
|---|---|
| Variables con credencial | 226 (151 únicas · 14 alias) |
| Proveedores / servicios | 67 |
| Buckets de cuenta | 11 |
| `OPERATIVA` | 92 |
| `SIN_VALOR` | 61 |
| `CREDENCIAL_INVALIDA` | 16 |
| `INACCESIBLE` | 15 |
| `ALIAS` | 14 |
| `ALCANZABLE` (p.ej. SMTP) | 10 |
| `BLOQUEADA` | 9 |
| `SIN_SALDO` | 4 |
| `HTTP_412` / `PETICION_INVALIDA` / `ENDPOINT_INCORRECTO` | 2 / 2 / 1 |
| Latencia de sonda | p50 **626 ms** · p90 **2 022 ms** |
| TTFT real (n=37) | min 258 ms · p50 **522 ms** · p90 **1 478 ms** · max 14 307 ms |
| Tiempo total (n=37) | p50 **703 ms** · p90 1 752 ms |

**Trampa del baseline**: la auditoría marca Moonshot/Kimi como `OPERATIVA` porque la credencial responde — pero es **de pago** y **no seleccionable**. Por eso el §2.C exige 3 ejes separados.

### FASE 3 — Benchmark propio (25 % del score) — REUTILIZAR, NO INVENTAR
```bash
python3 SCRIPTS/bench_capacidad.py     # capacidad % (11 tareas verificables) + p95 de cola
python3 SCRIPTS/bench_battery.py       # 10 casos privados, graders deterministas, McNemar pareado
```
- **Reproducibilidad obligatoria**: `prompt_hash` SHA-256 + `suite_version` + params fijos (`temperature=0` salvo muestreo) + respuesta cruda guardada en `.session/battery/`.
- Comparativas **pareadas (McNemar)**, nunca proporciones independientes con n<100.
- **Precedente (2026-10-04, `reps=2`, PROVISIONAL)**: `deepseek-reasoner` 90/100 (~1,6 s) · `nemotron-super` 78/100 (~1,3 s) · `kimi-k3` 75/100 (2–14 s); McNemar `deepseek` 3 discordantes / `kimi` 0. n=2 **no decide** → re-ejecutar antes de concluir.
- **Margen estadístico**: las capacidades medidas tienen **±15 pp**; solo diferencias **> 20 pp** son significativas. No declarar superioridad por debajo de 20 pp.
- **Semántica de 429 en NIM**: el techo real son **créditos/tokens diarios (~1 M tok/día/cuenta), no RPM**. Un 429 `daily/quota/credit` → cooldown **hasta medianoche UTC**, no 300 s (300 s quema las demás cuentas con ~288 reintentos inútiles). Medir con `.session/nim_usage.jsonl`.
- Fuentes de estado ya existentes: `.session/nim_usage.jsonl` · `.session/catalog/catalog_latest.json` (snapshot + sha256) · `.session/pool_state.json` (cooldowns LRU) · `SCRIPTS/cf_neurons_day.json` (stop al 85 % = 8.500 neuronas).

### FASE 4 — Cross-source + scoring F3
| Dimensión | Peso | Origen |
|---|---:|---|
| Calidad externa | 30 % | AA Intelligence Index + LMArena + benchmarks abiertos |
| **Benchmark propio** | 25 % | `bench_capacidad.py` + `bench_battery.py` |
| Fiabilidad | 15 % | éxito auth/live, ratio de caídas, estado de cuota |
| Herramientas | 10 % | tool-calling, visión, terminal |
| Latencia | 10 % | p50/p95 **por endpoint** (nunca cruzada) |
| Coste | 5 % | efectivo $0.00 |
| Ranking externo | 5 % | desempate |

**Techos duros**: benchmark propio < 40 → tope **49** · fiabilidad < 80 → tope **70** · evidencia `stale` → tope **75** · `error_rate > 10 %` o `pass_rate < 40 %` → fuera.
**Penalización**: −20 % a lo nunca probado localmente. **Ordenar por `score × confianza`**, con confianza ∝ frescura.
**Regla de oro**: el ranking externo **NUNCA** compensa un fallo propio. Sin benchmark propio → `candidato no evaluado`; **jamás** apto para producción ni para la cadena.
**Canonicalización**: NO fusionar sufijos de fecha/versión (`modelo-2026-01` ≠ `modelo-2026-06`). Conservar el ID crudo del proveedor. Alias con `confidence` ∈ {exacto, probable, desconocido}.

### FASE 5 — Propuesta de cadena por tier (NO auto-aplicar)
**Restricciones duras**:
1. Coste efectivo **$0.00** (Kimi de pago, Claude-vía-AGY por cuota y Bedrock fuera por defecto).
2. `p95 ≤ techo del tier` **en las dos taxonomías** (ver §5).
3. **≥ 2 proveedores independientes** por cadena. **NIM C1/C2/C7/C9 cuentan como UNO** (mismo upstream upstream) → no satisfacen el criterio por sí solos.
4. Respetar la `regla_de_seleccion` vigente: *el primer motor del tier cuyo p95 no supere el techo; si todos lo superan, **baja de tier** en vez de esperar*.
5. `AGY` = suscripción Google Pro (no es API): coste marginal $0.00, único con visión nativa, latencia 30–91 s → **restringido a `direccion`/C5** y a QA visual. `claude-sonnet-4-6` / `claude-opus-4-6-thinking` vía AGY → **nunca por el harness** (decisión del operador 2026-09-29).
6. Cloudflare: juez cruzado en C3 **solo si** `cf_neurons_day.json` < 8.500 neuronas.
7. No forzar `top_p`/`top_k`/`seed`/`penalties` en modelos con sampling fijo (el guard del proxy los borra).

| Nº | `mode_name` | Propósito |
|---|---|---|
| 1 | `full_power` | Máxima capacidad (visión + razonamiento denso) |
| 2 | `working_horse` | Equilibrio diario (DEFAULT) |
| 3 | `nim_only` | Razonamiento denso **sin** AGY (sustituye al extinto `kimi_only`) |
| 4 | `agy_free` | AGY primero, resto $0.00 |
| 5 | `free_light` | Pool `:free` puro, sin AGY |
| 6 | `agy_deep` | Dirección con doble AGY |

El **contenido** de cada cadena se **deriva de las fases 1–4**, no se fija a priori. La propuesta debe incluir: motor actual → motor propuesto, proveedor, p50/p95 medido, capacidad, coste, fuente del ranking y el motivo del cambio.

### FASE 6 — Persistencia, aplicación y rollback
1. Emitir en `.session/api_scan/`: `<TS>_scan.json` · `<TS>_ranking.md` · `<TS>_chain_proposal.json` (con `HECHO`/`VACIO`/`NULO` y sha256 por fuente).
2. **NO aplicar** automáticamente. Aplicar exige: (a) confirmación humana explícita · (b) `cp SCRIPTS/harness_mode.json SCRIPTS/harness_mode.json.bak-<TS>` · (c) `python3 SCRIPTS/harness_chain.py <cadena_nueva.json>` (**único** editor legítimo) · (d) `python3 SCRIPTS/harness_doctor.py` exit 0 · (e) `dsh --profile web --dump-config` sin error · (f) `bash SCRIPTS/sync_models_all.sh` + `python3 SCRIPTS/test_ssot_sync.py` · (g) eventos append-only en `.session/memory_events.jsonl` y nota en `memory-bank/journal/`.
3. `~/.dsh/settings.yaml`: **nunca** editar a mano ni borrar líneas con `sed`. Sustituir el ID por el sucesor vivo **preservando el bloque de 4 líneas** (`id`, `name`, `contextWindow`, `provider`). Propagar con `sync_models_all.sh`.

---

## 🔀 5. Reconciliación de taxonomías de tier (OBLIGATORIA)

Coexisten **dos** sistemas de escalones. La propuesta **debe** emitirse en ambas con su mapeo; si no, no es accionable.

| `harness_mode.json` (4 tiers) | Techo p95 | Matriz C0–C6 (`CAPABILITIES_SPEC`) | Motor primario C | SLO techo | TTFT Watchdog |
|---|---|---|---|---|---|
| `flash` | 4 000 ms | **C1 FAST** | `nvidia/nemotron-3.5-lightning-30b-a3b` (191 ms) | 2 000 ms | 2,5 s |
| `medio` | 25 000 ms | **C2 CODE** | **`minimax/minimax-m3.1-flash:free`** (1 045 ms) → fallback `codestral-2508` | 8 000 ms | 5,0 s |
| `razonamiento` | 12 000 ms | **C3 REASON** | **`minimax/minimax-m3.1-flash:free`** → fallback `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b` | 15 000 ms | 5,0 s |
| `razonamiento` | 12 000 ms | **C4 DELIBERATION** | `nvidia/nemotron-3-ultra-550b-a55b` (466 ms, Elo 1426,0) | 120 000 ms | 12,0 s |
| `direccion` | 120 000 ms | **C5 ARCHITECT** | AGY CLI (`gemini-3.1-pro-high`, Elo 1486,9) | 120 000 ms | 15,0 s |
| (escalada R3) | — | **C6 HEAVY ESCAL.** | `nvidia/nemotron-3-ultra-550b-a55b:free` + Pool Free + Human Gate | 300 000 ms | 12,0 s |
| (control determinista) | — | **C0 CONTROL** | `ast.parse` / `node --check` / `bash -n` | < 50 ms | — |

> **Nota (2026-10-21)**: esta tabla se recalibró con la cadena v4.1. Antes (v3.5) C2 abría con Codestral, C3 con R1 Distill y el carril `medio` incluía `nemotron-3-super-120b-a12b`, que **ya no está en el catálogo de NIM** (404 directo; el proxy lo remapea, pero por identidad es `nemotron-3.5-super-120b-a12b`). El motor por defecto del sistema es **MiniMax M3.1 Flash** (94 % de capacidad, 1 045 ms, $0.00, **con visión probada**).

**Dónde divergen**: `medio` (25 000 ms) vs C2 (8 000 ms) y `razonamiento` (12 000 ms) vs C4 (120 000 ms). Un motor que cumple el techo del tier 4-tiers puede violar el SLO de la capacidad. **Verificar contra el techo más estricto de los dos.**

**Regla de selección vigente**: *el primer motor del tier cuyo p95 no supere el techo; si todos lo superan, baja de tier en vez de esperar.*

---

## 🛠️ 6. Comandos de ejecución

```bash
# 0) Pre-flight: proxy NIM vivo (el harness NUNCA va directo a integrate.api.nvidia.com)
curl -s http://127.0.0.1:8088/health

# 1) Barrido empírico completo ($0.00) → JSON + CSV + MD
python3 SCRIPTS/scan_apis_full.py --trabajadores 10
python3 SCRIPTS/render_api_reports.py

# 2) Discovery + EOL + scoring de catálogo + snapshot con sha256
python3 SCRIPTS/model_catalog_scan.py --top 20 --json

# 3) Health del harness (pasivo) + telemetría de cuotas
python3 SCRIPTS/harness_doctor.py
python3 SCRIPTS/pool_telemetry.py

# 4) Benchmark propio (capacidad + batería pareada)
python3 SCRIPTS/bench_capacidad.py
python3 SCRIPTS/bench_battery.py

# 5) Orquestador: scan + rank + propuesta (NUNCA auto-aplica)
python3 SCRIPTS/harness_api_scan.py --scan --rank --propose
python3 SCRIPTS/harness_api_scan.py --scan --rank --propose --json

# 6) Aplicar una cadena (SOLO con confirmación humana; backup previo en el script)
python3 SCRIPTS/harness_chain.py <cadena_nueva.json>

# 7) Verificación post-despliegue
python3 SCRIPTS/harness_doctor.py && dsh --profile web --dump-config >/dev/null
python3 -m py_compile SCRIPTS/harness_api_scan.py SCRIPTS/harness_dispatch.py SCRIPTS/nvidia_rate_limiter.py
bash -n SCRIPTS/harness_mode.sh && bash -n SCRIPTS/sync_models_all.sh
bash SCRIPTS/smoke_test_v28_1.sh
bash SCRIPTS/sync_models_all.sh && python3 SCRIPTS/test_ssot_sync.py
```

---

## 🚨 7. Incidencias frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| 503 / `Worker limit reached 16/16` en BluesMinds o Nano Omni | Límite de concurrencia del host | Backoff exponencial (3 s) o conmutar de cuenta NIM (C1, C2, C7) |
| 404 en un modelo de NIM | Puede ser transitorio de upstream, **no** prueba de caída | Reintentar con espera larga y streaming. **2 confirmaciones negativas separadas** antes de degradar. Excepción: los tombstones `410 Gone` son veredictos definitivos |
| 429 `daily/quota/credit` en NIM | El límite real son créditos/tokens diarios (~1 M tok/día/cuenta), no RPM | Cooldown **hasta medianoche UTC**, no 300 s |
| DSH no ve los `nvidia_*` | El proxy `:8088` no arrancó | `curl :8088/health` → `bash SCRIPTS/boot_cliente.sh` (compuerta 0/6 idempotente). Mirar el proxy, no el YAML |
| DSH se cae al arrancar | `~/.dsh/settings.yaml` con IDs huérfanos (sed crudo) | Sustituir el ID preservando el bloque de 4 líneas; nunca borrar líneas sueltas |
| Respuesta vacía en `content` | Modelos de razonamiento responden en `reasoning_content` | Normalizador ya documentado en `f-investiga` §7 |
| `"!!!!"` o ruido multilingüe | `temperature` fuera de calibración | El proxy (KIMI-GUARD-v2) fuerza la temperatura del modelo y borra `top_p`/`top_k`/`seed`/`penalties` |

---

## 📤 8. Contrato de salida del modo 4

1. **Resumen ejecutivo** (≤ 20 líneas): nº de proveedores operativos, Kimi residual (debe ser 0 en superficie activa), fuentes consultadas con estado `HECHO`/`VACIO`/`NULO`, y **veredicto**: ¿redefinir la cadena? (SÍ/NO + motivo).
2. **Tabla de purga / residuos** (si el modo incluye saneado): `fichero | línea | tipo | acción | verificado`.
3. **Inventario en 3 ejes**: `proveedor | cuentas | disponibilidad | coste efectivo | p50 | TTFT p50 | catálogo | seleccionable (SÍ/NO + motivo)`.
4. **Ranking por fuente** (tablas **separadas**, nunca fusionadas): AA Intelligence Index (`id` + versión) · LMArena (Arena Score + IC 95 % + votos + fecha) · apoyo · sentimiento 30 d.
5. **Score F3** por modelo: las 7 dimensiones, la suma ponderada, el techo aplicado y el veredicto `evaluado` / `candidato no evaluado` / `no verificado`.
6. **Propuesta de las 6 cadenas** en **ambas taxonomías** + tabla de equivalencia + tabla de retiradas con **HTTP exacto y fecha**.
7. **Artefactos**: rutas exactas + sha256.
8. **Verificación**: tabla `comando | exit code | resultado`.
9. **Rollback**: comando exacto de reversión.
10. **Decisión abierta**: ¿aplico la cadena propuesta? (espera confirmación humana).

---

## 🛑 9. Anti-patrones de cierre (prohibido)

Entregar un plan en vez del código · un esbozo en vez de `harness_api_scan.py` funcional · `[PLACEHOLDER]` en vez del valor de un motor · "debería funcionar" en vez de exit 0 + sha256 · un ranking de una sola fuente presentado como verdad · un score único que mezcle Elo con exactitud · una cadena aplicada sin confirmación humana · editar `memory-bank/core/lessons-learned.md` (autoridad exclusiva del compactador de CT106) · parsear el `.env` con `split("=", 1)` · presentar `Kimi K3` como motor válido (EOL desde 2026-10-15).

---

## 📎 10. Procedencia

> **Rehidratado** de `.agents/archived-skills/f-api-scan-harness/SKILL.md` (v1.0, archivado 2026-10-13) — su ítem 6 (*Discovery & Ranking*) y su sección D (reglas de discovery/scoring) son la base de este cuerpo.
> **Mandato de cobertura**: `memory-bank/journal/2026-10-19_leccion_auditoria_apis_inclusion_obligatoria_nvidia_openrouter_c7.md`.
> **Biblia de discovery/ranking**: `memory-bank/journal/processed/2026-10-04T035500Z_finder_discovery_ranking_modelos.md` (Addendum 2 = informe F3; Addendum 3 = batería propia y fixes de proxy).
> **Parser del `.env`**: `memory-bank/journal/2026-10-20_barrido_completo_apis_env_y_anotacion_de_endpoints.md`.
> **Reglas epistémicas y vocabulario HECHO/VACIO/NULO**: `.agents/skills/f-investiga/scripts/rankings_ia.py` y `references/mapa_fuentes.md`.
> **Antecesor de prompt (superado)**: `memory-bank/prompts/CAT_22_API_SCANNER_AND_HARNESS_CURATOR.md` — invoca `scan_ai_providers.py` (ya no cubre los ~67 proveedores) y propone Kimi para "Lógica Pesada" (incorrecto desde 2026-10-15). Usar como contexto, no como procedimiento.
