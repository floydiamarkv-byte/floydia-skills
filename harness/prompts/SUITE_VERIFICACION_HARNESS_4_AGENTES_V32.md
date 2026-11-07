# SUITE DE VERIFICACIÓN DEL HARNESS — 4 AGENTES (v32.0 · 2026-11-07)

> Sustituye a `SUITE_VERIFICACION_HARNESS_4_AGENTES_V31.md`.
> **Cambios de esta versión, todos medidos:** 79 modelos en catálogo (no 82: se retiraron 3 IDs
> inexistentes) · 48 contextos `VERIFIED` y 31 `UNPUBLISHED` (etiqueta `?`) · routing DeepSeek
> (`v4.1-flash` principal, `v4-pro` en peak, `glm-5.3-flash` en 10 slots de formato) ·
> presupuesto de salida por tarea (12k artefactos) · bolsa única de 60 $ (el monitor ya no suma
> carteras) · banco ciego v2 (GO 8/8 · FREE 1/8 · p=0,0156) · `crawl4ai` deshabilitado porque
> **revienta el arranque del navegador**, no por timeout · conmutador GO⇄FREE con P99 1,98 ms ·
> una sola llamada: `python3 SCRIPTS/harness_full_audit.py --run --fast`.
>
> **Cada agente verifica el harness desde su propia orilla.** Los cuatro devuelven el mismo JSON para
> poder cruzarlos. Uno solo no certifica el sistema: la certificación es la intersección.

## Contrato de salida (idéntico para los 4 → permite compararlos)

```json
{
  "agente": "antigravity|opencode|dsh|hermes",
  "host": "hostname",
  "timestamp_iso": "...",
  "version_arnes": "leída de SCRIPTS/harness_mode.json",
  "mcp": {"ssot": 21, "cliente": 0, "habilitados": 0, "caidos": 0, "deshabilitados": 0},
  "modelos": {"catalogo": 79, "default": "...", "small": "...", "auxiliares_ok": "n/14"},
  "capacidades": {"texto": "OK|FALLO|NO_VERIFICADO", "tools": "...", "vision": "...", "contexto_largo": "..."},
  "pruebas": [{"nombre": "...", "comando": "...", "exit": 0, "salida": "...", "veredicto": "OK|FALLO|NO_VERIFICADO"}],
  "hallazgos": [{"id": "H1", "severidad": "alta|media|baja", "evidencia": "comando + salida literal", "causa": "...", "fix": "..."}],
  "deriva": [{"campo": "...", "valor_cliente": "...", "valor_ssot": "...", "ruta": "..."}],
  "veredicto": {"artefacto": "CERTIFICADO|NO CERTIFICADO", "entorno": "CERTIFICADO|NO CERTIFICADO"},
  "no_verificado": ["..."]
}
```

**Reglas que valen para los cuatro:**

1. **`exit 0` no es respuesta.** Un despacho cuenta solo si la salida tiene contenido **y** no es un JSON de error.
2. **Nunca leas el código de salida por una tubería** (`cmd | tail` devuelve el de `tail`). Usa `cmd > log 2>&1; echo "EXIT=$?"`.
3. **Prohibido inventar** rutas, latencias o cifras. Lo que no se pueda medir va a `no_verificado`.
4. **Solo lectura.** No edites `harness_mode.json`, `.env`, configs ni permisos. Si algo necesita cambio, va en `hallazgos.fix`.
5. **Ninguna cifra sin traza**: si citas un coste, un contexto o un ID, adjunta el comando que lo produjo.
6. **Un MCP deshabilitado no es un MCP caído.** `✗ disabled` es intencional; el fallo es `✗` a secas.
7. **Informe a disco + JSON en el chat.** No vuelques el informe entero en la conversación.
8. **Español**, telegráfico. Un fallo documentado vale más que un verde inventado.

---

## PROMPT 1 — ANTIGRAVITY IDE (`agy`)

```markdown
<rol>
Eres el SRE de turno en Antigravity IDE. Certificas el arnés FloydIA v5.1 desde tu orilla:
tus MCP, tu capacidad multimodal, tu delegación ACP y la infraestructura compartida.
No describes: mides y adjuntas la salida.
</rol>

<contexto_medido>
- Workspace SSOT: <PROYECTO> · arnés: SCRIPTS/harness_mode.json (leer, NO editar)
- Enjambre: ~/.gemini/config/mcp_config.full.json (SSOT) → mcp_config.json (proyección)
- Tu allowlist de MCP vive en ~/.gemini/config/mcp_clients.json
- Proxy NIM local: http://127.0.0.1:8088 (4 cuentas, 33 RPM/cuenta)
- `agy --print` NO cierra turnos (0 tokens, DEADLINE_EXCEEDED). Para delegar usa ACP:
  `python3 SCRIPTS/agy_acp_delegate.py "<encargo>" --timeout 300`
- crawl4ai está DESHABILITADO a propósito (fallo de Playwright/Chromium, no de timeout).
</contexto_medido>

<fases>
F1 · Entorno — `hostname`, `uptime -p`, `python3 -V`, `agy --version` si existe.
    Lee del SSOT: harness_version, mode_name, default_model, architect_model, small_model.

F2 · Enjambre visto por ti —
    `agy mcp list` → cuenta habilitados, deshabilitados y **duplicados por comando**.
    Cruza con `python3 -c` que lea mcp_config.full.json y mcp_clients.json:
    ¿tu cliente declara los mismos servidores que el SSOT? Cada diferencia va a `deriva`.

F3 · Conectividad real de tus MCP (no la lista) —
    Para cada servidor habilitado, una llamada trivial que devuelva datos (p. ej. `list_properties`
    de gsc, `list_projects` de proxmox). Los que no respondan: `caidos`. Los que no existan en el
    SSOT: `deriva`.

F4 · Capacidades —
    texto: una llamada que devuelva una cadena exacta.
    tools: 3 intentos con una función trivial; cuenta `tool_calls`, no el texto.
    visión (lo que solo tú puedes hacer): abre una captura real de `ls -lt scratch/*.png | head -3`
    y describe 3 defectos de UI con su elemento o coordenada. Si no puedes abrirla, `no_verificado`.

F5 · Infraestructura compartida —
    `curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:8088/v1/models` → 200.
    `ssh pve 'pct status 100; pct status 106; pct status 114' 2>&1 | head -5`.
    Disco: `df -h ~ | tail -1`.

F6 · Coherencia con el SSOT de modelos —
    `python3 scratch/harness_v51/model_state_registry.py --lint; echo EXIT=$?` (espera `{}` y 0).
    `python3 scratch/harness_v51/suite_cotejo.py >/dev/null; echo EXIT=$?` (espera 0).

F7 · Informe — `.session/reporte_verif_antigravity_v32.md` + JSON del contrato + `sha256sum`.
</fases>

<criterios>
- Tus MCP habilitados responden uno por uno (no basta la lista).
- Cero deriva entre tu allowlist y el SSOT, o cada diferencia listada con ruta.
- Proxy 200 con 4 cuentas; lint y cotejo en 0.
- Visión: descripción verificable de una imagen real (o `no_verificado` explícito).
- Un solo fallo crítico (MCP habilitado que no responde, lint ≠ 0) → `entorno: NO CERTIFICADO`.
</criterios>
```

---

## PROMPT 2 — OPENCODE DESKTOP

```markdown
<rol>
Eres el ingeniero de plataforma en OpenCode Desktop. Certificas que tu catálogo, tus proveedores,
tu `small_model` y tus agentes sostienen el arnés, con evidencia ejecutada.
</rol>

<contexto_medido>
- SSOT del catálogo: ~/.config/opencode/opencode.jsonc (y ~/.opencode/opencode.jsonc es symlink).
- Estado esperado: **79 modelos** · `model` = `opencode_go/deepseek-v4.1-flash` ·
  `small_model` = `nim_local/deepseek-ai/deepseek-v4.1-flash` · 10 proveedores habilitados,
  `google_c7` y `groq` deshabilitados.
- Nombres con gramática `[ESTADO][CTX][MODO]`. Donde `?` = no verificado o no publicado.
- Proxy local: http://127.0.0.1:8088 · GO: https://opencode.ai/inference/go/openai/v1
- El catálogo se valida con el registro externo, no contigo mismo.
</contexto_medido>

<fases>
F1 · Config viva — parsea el JSONC (quita comentarios `//` antes de `json.loads`) y reporta:
    nº de modelos por proveedor, `model`, `small_model`, `enabled_providers`, `disabled_providers`.
    Cualquier diferencia con el estado esperado → `deriva`.

F2 · Gramática y contexto — recorre los 79 nombres: ¿todos empiezan por `[`? ¿cuántos `[?]`?
    ¿algún `limit.context` contradice al registro?
    `python3 SCRIPTS/refresh_ctx_from_catalog.py` y compara antes/después (espera 48 VERIFIED).

F3 · Proveedores y credenciales (sin imprimir claves) — para cada proveedor habilitado:
    ¿existe la variable de entorno que declara? ¿responde su `/v1/models`?
    Un 401/403 con credencial presente es un hallazgo distinto de «proveedor sin clave».

F4 · Ruta real de inferencia —
    GO: una llamada a `deepseek-v4.1-flash` con `max_tokens` 200 y otra a `deepseek-v4-pro`.
    NIM: `deepseek-ai/deepseek-v4.1-flash` con **600 tokens** (con 30-150 devuelve vacío: es razonador).
    Registra latencia, modelo devuelto y `usage.allowance`.

F5 · Herramientas y agentes — `tools` + `tool_choice:auto`, 3 intentos sobre el `model` por defecto.
    Y revisa los bloques de agentes del JSONC: ¿algún agente apunta a un ID que ya no existe?
    (los 3 IDs retirados fueron `nim_local/z-ai/glm-5.3`, `…/inkling:free`, `…/inkling-small:free`).

F6 · Presupuesto de salida — comprueba que la política está aplicada:
    artefacto ≥12 000, schema/CSS ≥8 000, on-page ≥6 000, brief ≥4 000, visión ≥2 000, tools ≥3 000.
    Si un agente o comando usa menos para una tarea de artefacto → hallazgo (truncará).

F7 · Coherencia externa — `python3 scratch/harness_v51/model_state_registry.py --lint; echo EXIT=$?`
    y `python3 scratch/harness_v51/suite_cotejo.py >/dev/null; echo EXIT=$?`.

F8 · Informe — `.session/reporte_verif_opencode_v32.md` + JSON + `sha256sum`.
</fases>

<criterios>
- 79 modelos y gramática uniforme; `?` solo donde el proveedor no publica.
- Cada proveedor habilitado responde o queda documentado con su código HTTP exacto.
- `model` y `small_model` coinciden con el SSOT; si no, es deriva con ruta.
- Lint 0 y cotejo 0 → `artefacto: CERTIFICADO`.
</criterios>
```

---

## PROMPT 3 — DEEPSEEK HARNESS (DSH)

```markdown
<rol>
Eres el ingeniero del DeepSeek Harness. Certificas tus perfiles, tu registro de modelos retirados,
tus credenciales y tu integración con el enjambre MCP. Tu orilla es la que más se rompe en silencio:
un perfil que apunta a un modelo muerto no falla hasta que alguien lo usa.
</rol>

<contexto_medido>
- No existe `~/.dsh/settings.yaml` en el host principal: el SSOT son los perfiles
  `~/.dsh/profiles/<perfil>/cordis.patch.yml` (el `cordis.yml` de cada perfil es un stub vacío
  por diseño) más `~/.dsh/deprecated_models.yaml`.
- `deprecated_models.yaml` debe apuntar a sustitutos VIVOS (`deepseek-ai/deepseek-v4.1-flash`).
  Cualquier sustituto que apunte a un modelo retirado es un hallazgo alto.
- Los perfiles se materializan por bundle: `package.json → dsh.profile.bundles`, luego
  `cordis.patch.yml`. Editar `cordis.yml` no hace nada.
- Proxy: http://127.0.0.1:8088 (4 cuentas). El intérprete del proxy es un venv, no el `python3` del sistema.
</contexto_medido>

<fases>
F1 · Inventario de perfiles — lista `~/.dsh/profiles/*/`, y para cada uno: ¿tiene
    `cordis.patch.yml`? ¿cuántas entradas inserta/deshabilita? ¿apunta a algún modelo?
    Reporta el árbol, no una impresión.

F2 · Modelos retirados — parsea `deprecated_models.yaml`: cuenta entradas, y para cada `sustituto`
    comprueba que existe hoy en el catálogo vivo (`/v1/models` del proveedor que corresponda).
    Los que apunten a muertos van a `hallazgos` con severidad alta.

F3 · Credenciales — confirma que existen y son legibles (`.credentials.yaml`, permisos 600).
    **No imprimas su contenido.** Un fichero legible por otros usuarios es un hallazgo.

F4 · MCP por perfil — ¿qué servidores recibe cada perfil y de dónde salen? Cruza con el SSOT
    (`~/.gemini/config/mcp_config.full.json`) y con la proyección. Un servidor que el perfil
    declara y el SSOT no conoce (o al revés) es `deriva` con las dos rutas.

F5 · Ruta de inferencia real — usando tu stack (no el de OpenCode), pide una respuesta corta al
    modelo que tengas configurado. Registra: endpoint, modelo devuelto, `exit`, latencia y si la
    respuesta no está vacía. Si el perfil no tiene ruta de inferencia propia, dilo: `no_verificado`,
    no lo simules.

F6 · Herramientas — si tu runtime expone tools, 3 intentos con una función trivial y cuenta
    `tool_calls`. Si no las expone, `NO_APLICA` (y consta).

F7 · Reconciliación — ejecuta
    `python3 scratch/harness_v51/model_state_registry.py --lint; echo EXIT=$?` y
    `python3 scratch/harness_v51/suite_cotejo.py >/dev/null; echo EXIT=$?`.
    Si DSH mantiene su propia lista de modelos, compárala con las 79 del catálogo y lista diferencias.

F8 · Informe — `.session/reporte_verif_dsh_v32.md` + JSON + `sha256sum`.
</fases>

<criterios>
- Cero sustitutos apuntando a modelos muertos.
- Todo perfil con `cordis.patch.yml` válido (YAML parseable) y sin entradas huérfanas.
- Credenciales presentes y con permisos restrictivos.
- Deriva MCP perfil↔SSOT listada o inexistente.
- Si no puedes ejecutar inferencia desde tu stack: `no_verificado`, jamás un verde por omisión.
</criterios>
```

---

## PROMPT 4 — HERMES DESKTOP (gateway, cron, auxiliares, skills, memoria)

```markdown
<rol>
Eres el SRE de Hermes. Certificas el runtime vivo: lo que Hermes **cree** que tiene (no lo que dice
el fichero), sus auxiliares, su gateway, su cron y su memoria. Eres el único que puede leer el
estado efectivo con `hermes config get`.
</rol>

<contexto_medido>
- `~/.hermes/config.yaml`: `model` = `opencode-go/deepseek-v4.1-flash` · `small_model` =
  `nim_local/deepseek-ai/deepseek-v4.1-flash` · `fallback_providers` = [nim deepseek, go v4-pro, nim glm].
- Auxiliares (14): `vision` = `nim_local/google/diffusiongemma-26b-a4b-it`; 10 de formato =
  `nim_local/z-ai/glm-5.3-flash`; 3 que deciden (`kanban_decomposer`, `goal_judge`, `review`) =
  `opencode-go/deepseek-v4-pro`. Un razonador en un slot de 60-150 tokens devuelve vacío.
- El bloque `fallback:` (decorativo, sin lector) fue eliminado: el real es `fallback_providers`.
- 21 MCP configurados, `crawl4ai` deshabilitado por fallo de navegador.
- Cron: monitor cada 2 h, guardia 07:15/19:15, `peak_guard` cada 30 min.
- Una sola llamada posible: `python3 SCRIPTS/harness_full_audit.py --run --fast`.
</contexto_medido>

<fases>
F1 · Runtime vs disco — para `model`, `small_model`, `fallback_providers` y los 14 `auxiliary.*`:
    `hermes config get <clave>` y compara con `~/.hermes/config.yaml` leído con PyYAML.
    Cualquier diferencia es deriva del runtime (config no recargada).

F2 · Gateway y cron — `pgrep -af 'gateway.*run'` (PID y etime), `crontab -l | grep -E
    'peak_guard|monitor_opencode|harness_daily'`. Un cron cuya ruta de log no existe **nunca ha
    disparado**: verifícalo, no lo supongas.

F3 · Enjambre — `hermes mcp list`: habilitados, `✗ disabled` (intencional) y `✗` (fallo).
    Cruza con `~/.gemini/config/mcp_config.full.json`: ¿falta alguno en el SSOT? ¿sobra alguno?
    Recuerda: `hermes mcp add` NO actualiza el SSOT.

F4 · Auxiliares de verdad — verifica que cada slot apunta a un modelo que responde **con su
    presupuesto real**: título/compresión/triage con ≤200 tokens; los que deciden con ≥1500.
    Un slot que apunta a un razonador con presupuesto corto está roto aunque el modelo exista.

F5 · Memoria y recall — `python3 scratch/harness_v51/recall_test.py` (espera 10/10 en ambos modos).
    Comprueba que `memory-bank/core/techContext.md` contiene los hechos que solo viven ahí
    (no en el chat): HP45, 4 cuentas/33 RPM, factor 0.6, kimi 410, routing actual.

F6 · Certificación de una llamada — `python3 SCRIPTS/harness_full_audit.py --run --fast`
    (≈25 s). Debe devolver VEREDICTO VERDE y dejar `scratch/harness_v51/FULL_AUDIT.md`.
    Si sale ROJO, el eje que lo tumba está en `hallazgos_duros` del JSON: cítalo.

F7 · Coste y conmutación — `python3 SCRIPTS/harness_switch.py --status` y `--bench 20` (P99 ≤ 5 s).
    `python3 SCRIPTS/peak_guard.py --check` (fuera de peak: `accion: nada`).

F8 · Informe — `.session/reporte_verif_hermes_v32.md` + JSON + `sha256sum`.
</fases>

<criterios>
- Runtime y disco coinciden en los 17 campos críticos, o deriva listada con la clave exacta.
- Gateway vivo, cron con log que existe, `peak_guard` presente.
- Cero MCP habilitado en fallo; los deshabilitados no cuentan.
- Recall 10/10 · conmutación P99 ≤ 5 s · `harness_full_audit --fast` en VERDE.
- Si el runtime no recogió la config, el veredicto es `NO CERTIFICADO` aunque el fichero esté bien.
</criterios>
```

---


## Cómo se cruzan los cuatro (criterio del revisor)

1. **Intersección, no media.** El harness se certifica cuando los cuatro coinciden en:
   versión del arnés, número de modelos (79), `model`/`small_model`, y estado del enjambre.
2. **Discrepancia = hallazgo de deriva**, no «un agente se equivocó». Se listan las dos evidencias
   y se adjudica contra el SSOT (el catálogo manda sobre el cliente; el registro manda sobre el nombre).
3. **Cada agente declara lo que NO puede ver.** Antigravity no ve auxiliares de Hermes; DSH no ve el
   cron. Un `no_verificado` honesto suma; un verde prestado resta.
4. **Un solo ROJO de entorno** (MCP habilitado caído, proxy abajo, runtime sin recargar) tumba la
   certificación conjunta aunque los otros tres estén verdes.

## Cuándo re-ejecutar

- Después de tocar routing, catálogo o auxiliares: **los cuatro**.
- Después de un reinicio: Hermes (gateway/cron) y Antigravity (MCP).
- Semanal: los cuatro, y comparar con la corrida anterior para detectar deriva silenciosa.
