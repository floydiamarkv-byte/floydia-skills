# Mapa de fuentes — estado VERIFICADO (2026-09-28)

> No confíes en la memoria: cada estado de esta tabla se obtuvo con una consulta real.
> Regenerar con: `python3 scripts/doctor.py --out inventory.json`

## ✅ FUNCIONAN (probadas con respuesta real)

| Fuente | Key | Evidencia | Uso |
| :-- | :-- | :-- | :-- |
| **crawl4ai MCP** | no | `scrape` devolvió markdown completo | **Ingesta y lectura de páginas** |
| **LMArena dataset HF** | no | CC-BY-4.0, `lastModified 2026-09-28T03:02:13Z`, 52.819 descargas | **Rankings de modelos** (22 subsets × 2 splits) |
| **OpenRouter `/api/v1/models`** | no | HTTP 200, 460 modelos con precios | **Precios y longitud de contexto** |
| **HN Algolia** | no | 289 hits con filtro de 7 días | Señal técnica fresca |
| **Bluesky `api.bsky.app`** | no | HTTP 200 con engagement | Señal social |
| **OpenAlex** | no | HTTP 200 | Académico |
| **arXiv** | no | HTTP 200, Atom XML | Académico |
| **Wikipedia API** | no | HTTP 200 | Contexto general |
| **Jina Reader** `r.jina.ai` | no | HTTP 200 con `Title/URL Source/Published Time` | **Leer cualquier URL como markdown** |
| **Reddit `.rss`** | no | HTTP 200 | Social (`.json` NO funciona) |
| **`last30days` v3.19.0** | no | `--preflight` → "Ready to research" | Reddit + HN + Polymarket + GitHub. **REACTIVADO 2026-09-28** (ya no en `_archive`) |
| **`agy` (Antigravity) v1.2.12** | suscripción | turno real de 129 s con `structured_output` | **1ª opción de delegación** |
| **Playwright CT114** `:3000` | no | handshake TCP OK | QA visual y navegación |
| **FlareSolverr CT114** `:8191` | no | handshake TCP OK | Anti-bot |
| **Chromium 154** | no | `/usr/bin/chromium` | Navegación local |

## ❌ ROTO O BLOQUEADO (no lo intentes)

| Fuente | Síntoma | Workaround |
| :-- | :-- | :-- |
| **`web_search` (DSH)** | HTTP 402 *Insufficient Balance* | Apunta a `api.deepseek.com` (cuenta de chat, sin saldo). **SUSTITUIDO por Serper** (`C7_SERPER_API`, Google real) + 7 keyless. Ver `WEB_SEARCH_SIN_SALDO.md` |
| **Serper** `google.serper.dev` | `C7_SERPER_API` | ✅ **search + news + images OK**. Google real. **1 crédito por consulta**, con caché de 24 h. Única fuente que consume cuota |
| **DuckDuckGo HTML** | HTTP 202 con 0 resultados (mayoría) | ⚠️ **Degradado, no bloqueado**: funcionó 1 vez de ~10. Último recurso, nunca fuente única |
| **Reddit `.json`** | HTTP 403 | Usar `.rss` |
| **Bluesky `public.api.bsky.app`** | HTTP 403 | Usar `api.bsky.app` |
| **Semantic Scholar** | HTTP 429 | Pool compartido, necesita backoff |
| **Nitter** | repo archivado; instancias dan 0 tweets o 403 | Ninguno |
| **xcancel.com** | HTTP 451 | — |
| **X syndication** | HTTP 200 con **cuerpo vacío** (timeout en descarga) | Inútil |
| **X API v2** | HTTP 401 sin OAuth | No hay tier gratuito |
| **GDELT** | HTTP 429 | Intermitente |
| **Lobste.rs** | HTTP 400 en `search.json` | — |
| **GitHub API sin key** | rate limit 60/h | Usar `raw.githubusercontent.com` o `codeload` |
| **agentskills.io** | inalcanzable | Spec en `code.claude.com/docs/en/skills.md` |
| **Artificial Analysis** | DNS resuelve, conexión timeout | Posible bloqueo de ruta; requiere key |

## 🔑 REQUIEREN ALTA (todas con tier gratis SIN tarjeta)

| Servicio | Gratis | Nota |
| :-- | :-- | :-- |
| **Tavily** | 1.000 créditos/mes | 1 search = 1 crédito |
| **Serper** | 2.500 queries | Búsqueda Google |
| **Firecrawl** | 1.000 créditos/mes | scrape + search |
| **Exa** | $10/mes + $10 alta | ⚠️ NO VERIFICADO (docs 403) |
| **Brave** | $5 créditos/mes | ⚠️ NO VERIFICADO (dashboard 403) |

## 🤖 MODELOS `:free` DE OPENROUTER (probados con cuenta a $0)

**Conclusión: el free tier es del ENDPOINT, no de la cuenta.** Las 7 cuentas sirven igual.

| Modelo | Estado | Fallo |
| :-- | :-- | :-- |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | ✅ limpio | — |
| `dots-studio/dots-3-note-preview:free` | ✅ limpio | — |
| `nvidia/nemotron-3.5-lightning:free` | ⚠️ | devuelve el **razonamiento**, no la respuesta |
| `cohere/north-mini-code:free` | ⚠️ | `content: null`, solo `reasoning` |
| `liquid/lfm-2.5-2.6b:free` | ⚠️ | `content: null`, solo `reasoning` |
| `poolside/laguna-s-2.1:free` | ❌ | `Provider returned error` |
| `qwen/qwen3.8-27b:free` | ❌ | 429 *rate-limited upstream* |
| `thinkingmachines/inkling-small:free` | ❌ | *only available on age-verified accounts* |

> Los ⚠️ los resuelve `fanout_models.py` automáticamente. El script **aborta** ante modelos de pago antes de llamar (el error de saldo de OpenRouter es opaco: sin `code`, sin mensaje).

## 💳 CUENTAS OPENROUTER (verificado vía `/api/v1/credits`)

| Variable | Total | Restante | Nota |
| :-- | :-- | :-- | :-- |
| C1–C5 | $0 | **negativo** | Exhaustas |
| C6 | $0 | $0 | Nunca usada |
| **C7** | **$24** | **$0.205** | La única con saldo |
| C9 | — | — | ⚠️ **ALIAS de C7** |
| `OPENROUTER_API_KEY` | — | — | ⚠️ **ALIAS de C7** |

> 🚨 **Solo hay 7 cuentas reales, no 9.** Las tres últimas comparten hash SHA-256.
> Contarlas por separado infla la capacidad y provoca 429 antes de lo previsto.
> `doctor.py` y `fanout_models.py` deduplican por hash automáticamente.

## 🧠 MOTORES OPEN SOURCE PARA ADAPTAR

| Proyecto | Licencia | Veredicto |
| :-- | :-- | :-- |
| [`assafelovic/gpt-researcher`](https://github.com/assafelovic/gpt-researcher) 0.16.1 | Apache-2.0 | **Motor recomendado**: librería sin servidor, 21 retrievers keyless |
| [`crawl4ai`](https://github.com/unclecode/crawl4ai) 0.9.4 | Apache-2.0 | **Ya instalado como MCP** |
| [`aiwithremy/claude-skills-llm-council`](https://github.com/aiwithremy/claude-skills-llm-council) | MIT | **Molde de skill**: 10 subagentes + anonimización |
| [`hex/claude-council`](https://github.com/hex/claude-council) | — | Consulta a CLIs con auth por suscripción (incluye `agy`) |
| ~~`langchain-ai/open_deep_research`~~ | MIT | ❌ **ARCHIVADO** |
| ~~`stanford-oval/storm`~~ | MIT | ❌ **MUERTO** 12 meses, `archived:false`, 31.5k★ |
| ~~`camel-ai/owl`~~ | **SIN LICENCIA** | ❌ Todos los derechos reservados |
| ~~`local-deep-researcher`~~ | MIT | ❌ Depende de DuckDuckGo |

## ⚠️ PROYECTOS QUE NO EXISTEN (myth-busting)

Verificados con 404 literal + búsqueda:

`HKUDS/DeepCodeAgent` · `mshumer/gpt-agent` · `Alibaba-NLP/WebDancer` (repo
autónomo) · `chatgpt-infinity` · `lmarena-ai/arena-hard-auto`

> ⚠️ **CORRECCIÓN 2026-09-28 (2ª ronda)**: `oolong-tea-2026/arena-ai-leaderboards`
> **SÍ EXISTE**. Lo había marcado como inventado sin comprobarlo bien. Verificado:
> HTTP 200, **37★, MIT, push 2026-09-28**, 10 leaderboards, API REST en
> `api.wulong.dev`. **Lesson: "no lo encontré" ≠ "no existe". Verificar con
> codeload/raw antes de declarar inexistente.**

También falsos: *"Open LLM Leaderboard v2 activo"* (la org es `open-llm-leaderboard-old`; no hay v3) y *"Terminal-Bench va por 2.1"* (va por **4.0**).

---

## Scripts que sirven estos datos

| Fuente | Script | Comando |
| :-- | :-- | :-- |
| LMArena (Elo, 22 configs) | `scripts/rankings_ia.py` | `--arena text --top 15` |
| Precios y contexto (460 modelos) | `scripts/rankings_ia.py` | `--precios` |
| Leaderboards de agentes | `scripts/rankings_ia.py` | `--agentes` |
| Bluesky · HN · Reddit · Lobste.rs | `scripts/senal_social.py` | `--query "..." --canal todos` |
| X por URL concreta | `scripts/senal_social.py` | `--url-tweet "https://x.com/a/status/1"` |

**Trampas de API documentadas (verificadas 2026-09-28):**

| Trampa | Síntoma | Nota |
| :-- | :-- | :-- |
| HN Algolia `q=` en vez de `query=` | **HTTP 400 silencioso** | Parece "sin resultados" pero es un 400. Fijado por el test E10 |
| HN `numericFilters` con `>` sin codificar | HTTP 400 | Debe ser `%3E` |
| Lobste.rs `search.json` | HTTP 400 / HTML | Usar `search.rss` |
| Reddit `.json` | HTTP 403 | Usar `.rss` |
| Bluesky `public.api.bsky.app` | HTTP 403 | Usar `api.bsky.app` |
| X syndication | HTTP 200 con **cuerpo vacío** | Inútil: 200 no significa que funcione |
| `httstatus.io/api` | 404 | No usarlo como verificador |

> **Regla derivada**: un `200` no prueba que una fuente funcione, y un `400` no
> prueba que no haya datos. Hay que mirar el **cuerpo** y el **esquema**.
