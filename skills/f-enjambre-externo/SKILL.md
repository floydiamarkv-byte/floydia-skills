---
name: f-enjambre-externo
description: "Ejecuta fan-out por API y sitios manuales con fan-in automatico hacia COTEJO.md y MANIFEST.sha256. Activar para empaquetar consultas, ingerir respuestas multi-sitio, o generar matriz de cotejo. No usar para conducir el navegador en rondas interactivas."
version: 1.0.0
license: MIT
metadata:
  cost: "0.00 USD (free tiers + NIM local)"
  depends-on: "SCRIPTS/enjambre, NIM :8088, ~/.secrets/antigravity.env"
  brother-skill: "f-investiga"
---

# f-enjambre-externo — consulta multi-modelo con cotejo

> **Fan-out por API oficial + humano en el bucle. Fan-in automatico.**
> No conduce el navegador, no copia perfiles, no oculta senales de automatizacion.

## Cuando usar / cuando no

| Usar | No usar |
|---|---|
| "Pregunta esto a varios modelos y coteja" | "Investiga X en la web" → `f-investiga` |
| "Tengo 6 respuestas en una carpeta, cotéjalas" | "Resume este documento" |
| "Quiero segunda opinion de N modelos" | Decisiones de un solo criterio |

## Preflight (obligatorio)

```bash
python3 SCRIPTS/enjambre/enjambre.py doctor --probe
```

- Si hay **< 2 canales en `[OK]`**, detener y reportar; no lanzar el run.
- `[BLOQUEADO]` (Groq por region, Mistral por plan) y `[SIN CLAVE VALIDA]` no son fallos del sistema.
- Nunca imprimir valores de claves; solo nombres de variable.

## Flujo

### 1. Paquete
```bash
python3 SCRIPTS/enjambre/enjambre.py pack --topic "<tema>" --context <documento.md>
```
Genera `run_id`, `prompts/canonical.md`, 12 variantes y `manifest.json`.

### 2. Envio por API
```bash
python3 SCRIPTS/enjambre/enjambre.py send --run <run_id> --dry-run   # plan
python3 SCRIPTS/enjambre/enjambre.py send --run <run_id>             # real
```
Resuelve solo la clave valida por proveedor (prueba clave x modelo, cachea el nombre 12 h).
Canales activos medidos: Gemini, Z.ai, OpenRouter, DeepSeek, NIM local.

### 3. Sitios manuales
```bash
python3 SCRIPTS/enjambre/enjambre.py manual --run <run_id>
```
Crea `MANUAL.md` e `inbox/`. ChatGPT, Claude, Grok y LMArena **siempre** son manuales
(ToS/Cloudflare). El usuario pega, envia y guarda la respuesta en `inbox/`.

### 4. Ingesta
```bash
python3 SCRIPTS/enjambre/enjambre.py ingest --run <run_id> --inbox <run_dir>/inbox
```
Normaliza md/txt/html/pdf, quita ` thinking`, calcula SHA256, atribuye proveedor y
descarta el eco del propio prompt.

### 5. Cotejo
```bash
python3 SCRIPTS/enjambre/enjambre.py cotejo --run <run_id> --verify-urls
python3 SCRIPTS/enjambre/enjambre.py cotejo --run <run_id> --taxonomy <temas.json>
```
- Motor por defecto: `findings` (extrae bloques `H1..H10` y "3 correcciones").
- `--engine llm`: usa NIM local para texto libre, validando cita literal.
- `--taxonomy`: obligatorio si la consulta **no** es una auditoria con hallazgos.

### Todo en uno
```bash
python3 SCRIPTS/enjambre/enjambre.py run --topic "<tema>" --context <doc.md> --inbox <dir>
```

## Taxonomia propia (formato)

```json
{"topics":[
  {"id":"throttling","label":"Control de flujo",
   "groups":[["throttling","rate limit"],["canal","nodo"]]}
]}
```
Presencia = al menos una palabra de **cada** grupo, dentro de una ventana de 320 caracteres.

## Reglas duras

1. Nunca automatizar el envio en ChatGPT, Claude, Grok ni LMArena.
2. Nunca copiar `~/.config/google-chrome` ni perfiles: son credenciales.
3. `ia6` (Google Pro) fuera de cualquier automatizacion.
4. No ocultar `navigator.webdriver` ni resolver captchas: si un sitio lo exige, sale del set.
5. El consenso no es veracidad: pesar grupos independientes y URL viva + fecha.
6. Coste objetivo $0.00; un modelo de pago exige confirmacion humana.

## Evidencia y reporte

Cada run deja:
```
scratch/enjambre/<run_id>/
  manifest.json  prompts/  responses/
  send_report.json  ingest_report.json  MANUAL.md
  cotejo/COTEJO.md  cotejo/assertions.json  cotejo/MANIFEST.sha256
```

En la respuesta final: ruta relativa + SHA256 de `COTEJO.md` y del manifiesto.
No volcar transcripts ni claves en el chat.

## Fallos tipicos

| Sintoma | Causa | Accion |
|---|---|---|
| `NO_KEY` | ninguna clave responde 200 | revisar variable en `.env`; `doctor --probe` |
| respuesta de 4 palabras | modelo de razonamiento sin presupuesto | subir `min_max_tokens` del proveedor |
| matriz vacia | taxonomia no coincide | pasar `--taxonomy` con los temas de la consulta |
| `401/403` | clave caducada o region bloqueada | no insistir; marcar y seguir con los demas |
