# MODEL_NAMING v5.1 — gramática única y lint

## Gramática (un solo formato para todos los consumidores)

```
[<ESTADO>][<CTX>][<MODO>] Modelo Versión (rol)
[OK][1M][GO] DeepSeek V4.1 Flash (Backend/DOM)
[OK][?][F] Nemotron 3 Nano Omni 30B Reasoning (:8088)
```

| Campo | Valores | Quién lo escribe |
|---|---|---|
| `ESTADO` | `OK` · `DEGRADED` · `RETIRED` · **`?`** | el registro (`estado` + `existe`), nunca a mano. `?` = existencia no verificada (proveedor sin catálogo en la sonda) |
| `CTX` | `128k` · `200k` · `1M` · **`?`** | el registro (`ctx_real`). `?` = el proveedor no publica el límite y aún no se ha sondeado |
| `MODO` | `GO` (consume allowance) · `F` ($0) | el proveedor del modelo |
| Cuenta | `[OK][1M][GO·C5]` | opcional, separador explícito |

Reglas duras:

- `?` **no es un comodín**: en `CTX` solo se acepta cuando `ctx_real` es `null`; en `ESTADO` solo cuando
  `existe` es `null`. Un `?` con dato medido es un fallo. Ambos son **estados terminales**, no tareas abiertas:
  si el proveedor no publica el límite o no expone catálogo, el nombre lo dice y nadie inventa la cifra.
- La comparación es por **etiqueta normalizada**, no por bytes: 1 000 000 y 1 048 576 son ambos `1M`;
  262 144 es `256k` (÷1024) y 200 000 es `200k` (÷1000). Comparar cifras crudas producía 5 falsos positivos.
- La visión **no va en el nombre**: vive en el registro (`vision`, probada). Antes existía un sufijo `-V`
  que nadie validaba y desapareció de los 82 nombres.
- ID canónico `<proveedor>/<modelo>`; `:free` solo en OpenRouter y nunca en el display name.
- Prohibidos `:nitro`, `:online`, `openrouter/auto`.
- `RETIRED` se tacha en el selector o desaparece.

## Aplicado 2026-11-07

`SCRIPTS/apply_model_names.py --apply` (dry-run obligatorio antes) reescribió **82 nombres** en
`~/.config/opencode/opencode.jsonc` y purgó **9 `limit.context`** que contradecían el catálogo
(`glm-5.3-flash` 131 072 → 1 000 000; `claude-haiku-5-5` 200 000 → 1 000 000; `grok-4.7` 131 072 → 500 000;
más seis `1 048 576 → 1 000 000`).

Se eliminaron 3 bloques con ID inexistente: `nim_local/z-ai/glm-5.3`,
`openrouter/thinkingmachines/inkling:free` y `…inkling-small:free`. Catálogo resultante: **79 modelos**,
9 en `opencode_go`, 24 en `nim_local`, 10 en `openrouter`.

Lint: `python3 scratch/harness_v51/model_state_registry.py --lint` → `{}` · **exit 0**.

## Cobertura de `ctx_real`

| Fuente | Modelos | Método |
|---|---|---|
| Catálogo GO (`limit.context`) | 9 | `SCRIPTS/refresh_ctx_from_catalog.py` |
| Catálogo OpenRouter (`context_length`) | 10 | ídem |
| Google (`models.list → inputTokenLimit`) | 29 | ídem |
| NIM `:8088`, `opencode/*` legacy y Cerebras | 31 | **no publican límite** → `[?]` (estado terminal) |

Total: **48 VERIFIED · 31 UNPUBLISHED** (campo `ctx_status` del registro).

Medir contexto cuesta al menos una llamada por modelo y no se deduce del nombre: mientras no se sondee,
`?` es la única etiqueta honesta. `beam-free` es el caso vivo: el catálogo dice 1 048 576 y el nombre dice `1M`.

## Lint

```bash
python3 scratch/harness_v51/model_state_registry.py --lint   # exit 2 si hay deriva
```

Falla con: gramática no conforme · `CTX` ≠ `ctx_real` (por etiqueta) · `?` con contexto medido ·
ID inexistente en su catálogo · duplicado **dentro del mismo proveedor** · `:free` en display name.

Corre en F2, antes de cada propagación y semanalmente.
Salida: `out/model_names_lint.json`.
