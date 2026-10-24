
# Skill: Harness FloydIA v2 — Manual Operativo & SRE (`f-harness` v3.1.0)

> **Propósito**: Manual operativo y centro de comando del Harness FloydIA v2 bajo el **Protocolo v28**. 
> Centraliza el enrutamiento determinista por dificultad (4 tiers / 11 motores a $0.00), la rotación LRU de cuentas, la telemetría pasiva y el diagnóstico/rescate de caídas en DeepSeek Harness (DSH).

---

## 🎯 1. Menú Interactivo Menu-First

Al invocar `/f-harness`, `/harness`, `/model-router` o ante un reporte de fallo en motores o DSH, el agente **DEBE responder de inmediato presentando este menú Bento interactivo**:

```markdown
╔════════════════════════════════════════════════════════════════════════════════╗
║             🛸 F-HARNESS — CENTRO DE CONTROL DE MOTORES & DSH v3.1            ║
║                     Ecosistema FloydIA — Protocolo v28                         ║
╚════════════════════════════════════════════════════════════════════════════════╝

Selecciona una acción respondiendo con el número correspondiente:

1️⃣ 🧭 **Inspección de Enrutamiento & Cadenas Activas**
   ↳ Muestra los 4 tiers (dirección, razonamiento, medio, flash), orden de fallback
     y motores asignados (`python3 SCRIPTS/harness_dispatch.py --explain`).

2️⃣ 🩺 **Harness Doctor & Diagnóstico Pasivo de Salud ($0.00)**
   ↳ Valida consistencia de `~/.dsh/settings.yaml`, catálogo NIM vivo (`:8088/v1/models`),
     tombstones y sintaxis YAML con `python3 SCRIPTS/harness_doctor.py`.

3️⃣ 📊 **Telemetría Pasiva & Consumo de Cuentas (C1..C9 / Cloudflare)**
   ↳ Consulta el estado de cuotas de tokens, cooldowns LRU (`.session/pool_state.json`)
     y consumo diario de neuronas Cloudflare (`python3 SCRIPTS/pool_telemetry.py`).

4️⃣ 🚑 **Diagnóstico & Recuperación Anti-Caídas de DeepSeek Harness (DSH)**
   ↳ Rescata DSH ante fallos de boot (`settings.yaml` roto por sed, IDs huérfanos o caídas
     del proxy), aplicando sustitución canónica y prueba de humo (`dsh --dump-config`).

5️⃣ 🔄 **Reconfiguración Segura de la Cadena de Motores**
   ↳ Edita de forma determinista la cadena SSOT con respaldo automático
     (`python3 SCRIPTS/harness_chain.py <nueva_cadena.json>`).

6️⃣ 🛡️ **Suite Integral de Verificación y Auditoría del Harness (Protocolo v29)**
   ↳ Ejecuta la suite completa de 5 fases: Turno 0 + MCPs, Sonda de APIs + Dashboard HTML,
     Compilación AST, Enjambre Anclado con Citas (`--swarm --file`), y Registro Append-Only
     (`python3 SCRIPTS/run_harness_verification.py`).

7️⃣ 🔬 **Escaneo de APIs + Ranking de Inteligencia + Redefinición del Harness**
   ↳ Barrido empírico del `.env` (AUTH/LIVE, $0.00), cruce con Artificial Analysis
     + LMArena + OpenRouter + LiteLLM + models.dev, scoring ponderado F3 y PROPUESTA
     de cadena por tier. NUNCA auto-aplica: emite propuesta y exige confirmación
     humana (`python3 SCRIPTS/harness_api_scan.py --scan --rank --propose`).
     Detalle operativo: `references/api-scan.md`.

0️⃣ 🚪 **Salir**
```

---

## 🧠 2. Modelo Mental: 4 Tiers, Entrada por Dificultad

El harness NUNCA hace fallback "a ciegas". Clasifica la tarea y entra por su tier; solo desciende dentro de la cadena si el motor elegido falla.

| Tier | Criterio de Entrada | Cadena de Motores (en orden, derivado de `harness_mode.json` v4, recalibrado 2026-10-21) |
|---|---|---|
| **direccion** (duda/consenso) | Ambigüedad o arbitraje de arquitectura | `AGY Gemini 3.1 Pro` (p50 39.1 s / p95 91 s, Elo 1486,9 👁️) ➔ `DeepSeek V4.1 Flash` (1112/2000, Elo 1474,6) ➔ `Nemotron 3.5 Super VL 120B` NIM (351/500, Elo 1415,9 👁️) |
| **razonamiento** | Tarea compleja / lógica profunda / LRM | `DeepSeek V4.1 Flash` (1112/2000, Elo 1474,6) ➔ `Nemotron 3 Ultra 550B` NIM (684/1200, Elo 1426,0) ➔ `Cloudflare R1 Distill 32B` (474/800) |
| **medio** | Código estándar / refactor / análisis | `MiniMax M3.1 Flash` (1050/1800, cap 94 %) ➔ `Mistral Codestral 2508` (430/900) ➔ `Nemotron 3.5 Super VL 120B` (351/600) ➔ `DeepSeek V4.1 Flash` (1112/2000) ➔ `Nemotron Super` (716/2000) ➔ `North Mini Code` (383/600) ➔ `Laguna S 2.1` (3297) |
| **flash** (default) | Trivial / chat / formato / consultas rápidas | `Nemotron 3.5 Lightning 30B` NIM (191/350, Elo 1351,3) ➔ `Ministral 8B` (532/900) ➔ `Nemotron 3.5 Lightning :free` OR (228/400) ➔ `Nemotron Super :free` Kilo (847) |

> [!NOTE]
> **Vault (nunca automático)**: Kimi directo (Moonshot, **de pago**) y OpenRouter C9 únicamente con `--break-glass` o solicitud explícita del usuario.
> **Kimi K3 (NIM) está RETIRADO** (`410 Gone`, EOL 2026-10-15): no figura en ninguna cadena. Sustitutos verificados: `nemotron-3-ultra-550b-a55b` (razonamiento) y `nemotron-3.5-super-vl-120b-a12b` (sincrónico).

> [!IMPORTANT]
> **Criterio de ordenación (2026-10-21)**: el orden **NO** es un ranking de calidad. Es intención de *fallback* dentro de cada carril: el dispatcher coge el **primero del carril cuyo p95 no supere el techo**, y si todos lo superan, baja de carril. La posición se recalibró con el **Elo de LMArena** (que sí distingue, con IC 95 % sin solapar) porque la medición local de capacidad (11 tareas, n=22, ±15 pp) no podía separar Super VL (92 %), DeepSeek V4.1 (93 %) y MiniMax M3.1 (94 %). `AGY` mantiene la cabecera de `direccion` por ser el **único con visión**, no por ranking.

---

## 🚑 3. Protocolo de Resolución de Caídas en DeepSeek Harness (DSH)

### Regla Permanente Anti-Rotura (#vetado):
> **SUSTITUIR el ID del modelo por el sucesor vivo; NUNCA borrar líneas sueltas con `sed` en `~/.dsh/settings.yaml`.**
> El borrado crudo de líneas de IDs elimina la clave `- id:`, dejando bloques con `name:` huérfano que provocan que `dsh web` aborte el arranque silenciosamente.

### Procedimiento de Rescate Determinista ante Caídas:
1. **Paso 1: Diagnóstico Pasivo**
   ```bash
   python3 SCRIPTS/harness_doctor.py
   ```
   Detecta automáticamente entradas sin `- id:`, tombstones y estado del proxy NIM.
2. **Paso 2: Backup Inmediato antes de Modificar**
   ```bash
   cp ~/.dsh/settings.yaml ~/.dsh/settings.yaml.bak.$(date +%Y%m%d_%H%M%S)
   ```
3. **Paso 3: Sustitución Limpia del Modelo Retirado**
   - Si un modelo fue descontinuado (ej. `deepseek-ai/deepseek-v4-flash-0731`), sustituir su identificador por el modelo activo sucesor (ej. `deepseek-ai/deepseek-v4.1-flash`) preservando las 4 líneas del bloque (`id`, `name`, `contextWindow`).
4. **Paso 4: Prueba de Humo Obligatoria (Smoke Test)**
   ```bash
   dsh --profile web --dump-config >/dev/null && echo "✅ Configuración DSH íntegra"
   ```
5. **Paso 5: Reinicio Limpio de DSH Web (si aplica)**
   ```bash
   bash SCRIPTS/launch-dsh-web-desktop.sh
   ```

---

## 📁 4. Archivos Vivos del Harness (SSOT)

| Archivo | Rol Operativo | Regla de Edición |
|---|---|---|
| `SCRIPTS/harness_mode.json` | Cadena de 11 motores (SSOT v3) | Editar ÚNICAMENTE vía `harness_chain.py` |
| `SCRIPTS/providers_registry.json` | Proveedores, base_urls, keys_env, cuotas | Manual con validación JSON |
| `SCRIPTS/harness_dispatch.py` | Dispatcher y motor de inferencia | Python compilado con `py_compile` |
| `SCRIPTS/harness_doctor.py` | Validador sintáctico, tombstones y DSH dump | Ejecución pasiva ($0.00) |
| `SCRIPTS/harness_api_scan.py` | Orquestador escaneo+rank+propuesta de cadena (R1, no auto-aplica) | Python compilado con `py_compile` |
| `SCRIPTS/pool_call.py` | Invocador pool con rotación LRU y cooldowns | Respetar presupuesto Cloudflare |
| `SCRIPTS/pool_telemetry.py` | Estado por cuenta y neuronas Cloudflare | Solo lectura de métricas |
| `SCRIPTS/env_loader.py` | **Parser canónico del `.env`** (comentarios inline `# endpoint:`) | Prohibido reintroducir `split("=", 1)` |
| `~/.dsh/settings.yaml` | Configuración bare-metal de DeepSeek Harness | Sustitución de IDs; nunca sed suelto |

---

## 🛡️ 5. Guardrails Inmutables & Token Economics

1. **Inferencia a Coste $0.00 Obligatoria**: Prioridad absoluta a tiers `:free` y créditos NIM incluidos. Prohibido ejecutar llamadas de pago para pruebas de conectividad o healthchecks.
2. **Probes Estrictamente Pasivos**: Las sondas de salud (`harness_doctor.py`) consultan únicamente `/v1/models` (metadatos sin coste) y sintaxis de disco.
3. **Prueba de Humo Previa a Cierre**: Ningún incidente de harness o settings se cierra sin verificar `harness_doctor.py` exit 0 y `test_harness_doctor.py` 4/4 OK.
4. **Escritura Segura de Archivos (Anti-Volcado Masivo)**: Prohibido volcar archivos o documentos extensos (>15-20 KB o >300 líneas) en un único tool call (`write_to_file` con `CodeContent` gigante). Todo documento o script extenso debe generarse por partes incrementales, modificarse quirúrgicamente o escribirse mediante scripts locales directos en Python o Bash para evitar saturación de buffer y caída del stream SSE.

---

## 🔬 6. Definición de Motores Post-Escaneo de APIs (Consulta Externa + Enjambre)

> **Cuándo**: tras un escaneo preliminar de APIs (`references/api-scan.md` / sondas pasivas) que confirme claves vivas, NO se define el orden de motores por intuición. Se ejecuta este protocolo de **triple contraste**.

### 6.1 Flujo obligatorio
1. **Inventario local verificado**: proveedores/rotación desde `opencode.jsonc` + `/health` del proxy `:8088` + `SCRIPTS/providers_registry.json`. (Hoy: los 5 motores principales van por **NVIDIA NIM** vía proxy multi-cuenta `127.0.0.1:8088` — buckets C1/C2/C7/C9).
2. **Consulta externa deliberada**: enseñar a una IA externa (chat web Libre, humano en el bucle) el inventario y pedirle orden de inteligencia mayor→menor + capacidades exactas, usando el prompt 6.2.
3. **Enjambre propio**: mientras tanto, lanzar subagentes paralelos con webfetch a fuentes primarias (fichas NVIDIA/HF, leaderboards verificables: Artificial Analysis Intelligence Index, LMArena) y registrar citas URL+fecha.
4. **Cotejo de 3 vías**: local vs externa vs enjambre. Registrar disonancias (ej.: LMArena solo lista a los modelos con(style control) activo; AA II sitúa `nemotron-3-ultra-550b` por encima de `nemotron-3-super-120b`). La cadena final se fija por **evidencia + coste $0.00 + latencia medida**, no por un solo ranking.
5. **Persistencia**: ranking y decisiones a `memory-bank/journal/` (append-only) y, si cambia el orden, editar `SCRIPTS/harness_mode.json` SOLO vía `harness_chain.py`.

### 6.2 Prompt canónico para IA externa (copiar/pegar tal cual, sustituir `[INVENTARIO]`)

```text
Actúa como analista de modelos LLM. Tengo este inventario de motores con APIs válidas ya verificadas:

[INVENTARIO: lista de modelos + proveedor + contexto + coste]

Contexto de uso: los uso en un harness multi-modelo clasificando tareas por dificultad:
- "razonamiento" (lógica profunda, arquitectura, matemáticas),
- "medio" (código estándar, refactor, análisis),
- "flash" (trivial, formato, latencia <1s),
con fallback en cadena dentro del mismo tier y prioridad $0.00.

Te pido, con citas verificables (URL + fuente):
1. Ranking de mayor a menor INTELIGENCIA general (razonamiento+código) de los modelos del inventario con confidence por posición.
2. Capacidades exactas de cada modelo: parámetros (totales/activos si MoE), contexto real, modalidades, tool-calling, benchmarks clave.
3. Metodología y latencia típica reportada.
4. Discrepancias explícitas si distintas fuentes discrepan entre sí.
Responde en español, tablas preferidas. Marca como NO VERIFICADO lo que no tengas con fuente.
```

### 6.3 Semilla vigente 2026-10-20 (enjambre propio + 7 IAs externas cotejadas + medición local)
> **TOMBSTONE**: la semilla 2026-10-12 quedaba headed por `Kimi K3` (II=44). Kimi K3 está **EOL** (`410 Gone` en NIM, 2026-10-15) y **ya no es candidato**. La semilla se recalibra sin él.

**Orden por Artificial Analysis Intelligence Index v4.3.2** (NUNCA mezclar versiones del índice; los "48/36" de prensa/aggregadores son v4.1 y están rebasados). Solo se listan valores **verificados en fuente**:

| # | Modelo | AA II (v4.3.2) | LMArena | Estado |
|---|---|---:|---|---|
| 1 | `deepseek-ai/deepseek-v4.1-flash` | **39** | — | VERIFICADO · Terminal-Bench rey 90.6 |
| 2 | `nvidia/nemotron-3-ultra-550b-a55b` | **23** | — | VERIFICADO · 550B MoE (55B activos) |
| 3 | `nvidia/nemotron-3-super-120b-a12b` | **12.8** | — | VERIFICADO |
| — | `nvidia/nemotron-3-nano-omni-30b-a3b` | ~10 (estimado) | — | NO VERIFICADO en fuente · sub-agente de percepción, no generalista |

> **Sin AA II verificable en las fuentes cargadas** (no inventar valores): `MiniMax M3.1 Flash`, `Mistral Codestral 2508`, `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`, `cohere/north-mini-code:free`, `nvidia/nemotron-3.5-lightning-30b-a3b`, `nvidia/nemotron-3.5-super-vl-120b-a12b`. Para estos, la evidencia disponible es **medición local** (`harness_mode.json`: capacidad % + p50/p95).

**Reparto por dominio (accionable para tiers)**: `nemotron-3-ultra-550b` → tier **razonamiento** (550B MoE, 684 ms p50 medidos) · `deepseek-v4.1-flash` → tier **medio/agéntico** (Terminal-Bench 4.0 26.8 vs 12.6; Automation 68.9%) · **flash**: `nemotron-3.5-lightning-30b` (191 ms p50, el más rápido de la flota) o `deepseek-v4.1-flash` con `reasoning_effort=1` · **dirección**: `AGY Gemini 3.1 Pro` (único con visión nativa, p50 39.1 s) · `nemotron-3.5-super-vl-120b` como respaldo multimodal.

**Trampas operativas verificadas**: (a) `reasoning_effort` por defecto `max` en razonadores de NIM → fijar `low` en tiers no-expertos; (b) ctx 1M de Ultra/Super requiere enablement — en NIM servido a 262k (coincide con `opencode.jsonc`); (c) **parámetros ≠ inteligencia** (Ultra 55B activos < V4.1 8–16B en II); (d) las latencias de fuentes externas son de proveedores comerciales: NIM free ~40 RPM → **medir TTFT propio**; (e) el **catálogo miente por omisión**: un modelo listado puede estar muerto al servir (`deepseek-v4-pro` 410) y viceversa → validar con `model_catalog_scan.py` + canario de 1 llamada.

**Precedente de medición propia que corrige al ranking externo** (batería propia `bench_battery.py`, 2026-10-04, `reps=2`, **provisional** — n=2 no decide): `deepseek-reasoner` **90/100** (~1,6 s) · `nemotron-super` 78/100 (~1,3 s) · `kimi-k3` 75/100 (2–14 s), con McNemar pareado `deepseek` 3 discordantes / `kimi` 0. → **Regla de oro: el ranking externo NUNCA compensa un fallo propio; la medición propia pesa ≥55 % del score.**

**Persistencia del poll**: 7 respuestas externas en `/home/tec/Descargas/ww/` + enjambre propio; consenso 6/7 en la cabecera de la semilla 2026-10-12 (mayoría Kimi, hoy irrelevante por EOL) y disidente `duck.ai` (Super#2).

### 6.4 Mandato de Cobertura de APIs en Auditorías (Lección Inmutable 2026-10-19)
En toda auditoría de APIs, benchmarking o redefinición del arnés (`f-harness`, `scan_apis_*`, `eval_*`):
1. **NVIDIA NIM**: Es **OBLIGATORIO** probar activamente las 4 cuentas (`C1_NVIDIA`, `C2_NVIDIA`, `C7_NVIDIA`, `C9_NVIDIA_API`) y el proxy local `http://127.0.0.1:8088/v1/models` y `/chat/completions` (`deepseek-ai/deepseek-v4.1-flash`, `nemotron-3.5-lightning`, `nemotron-3.5-super-vl`, `nemotron-3-ultra-550b`).
2. **OpenRouter C7 Privileged Free Tier & Pool**: Es **OBLIGATORIO** auditar el catálogo de modelos `:free` de OpenRouter distinguiendo:
   - **`C7_OPENROUTER`**: Cuenta fondeada con cuota privilegiada de **1.000 req/día** para modelos `:free` protegida por el cortafuegos `c7_free_client.py` a $0.00.
   - **`C1_OPENROUTER` a `C6_OPENROUTER`**: Cuentas libres rotativas (50 req/día cada una).
3. **Prohibición Estricta**: Queda TERMINANTEMENTE PROHIBIDO excluir NVIDIA NIM u OpenRouter C7 bajo la asunción de que "ya se conocen" o "corren en segundo plano". Toda auditoría debe emitir evidencia empírica verificada de ambos.


