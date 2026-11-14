---
name: f-scraper
description: "Extrae contenido web y de redes sociales por capas mediante MCP y CLI, desde MarkItDown y Crawl4AI hasta Obscura CDP y Agent-Reach. Activar para extraccion podada fit_markdown, esquemas JSON, o mapeo recursivo con Crawlee. No usar para dialogos de 4 rondas en navegador."
version: 1.0.0
license: MIT
---

# Skill: FloydIA Smart Scraping Router & Servidor MCP (`f-scraper` v1.0)

> **Extractor Unificado por Capas (Protocolo v28.2 / Harness v4.1)**
> Cero sobrecarga de RAM en HP15 · Conexión remota a Proxmox CT114 (`ws://192.168.1.238:3000/playwright` y `:8191`)
> Inferencia cognitiva a coste \$0.00 vía Micro-proxy NIM local (`:8088`).

---

## 🧭 1. Matriz de Decisión Operativa (¿Qué herramienta usar?)

| Nivel / Necesidad | Herramienta Canónica | Nivel Riesgo | Cuándo Usar | Coste |
|:--|:--|:--:|:--|:--|
| **Nivel 0: Documentos** | `smart_scrape(url)` | **R0** | URLs o rutas locales a `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.csv`, `.zip`. Convierte directo a Markdown con MarkItDown. | \$0.00 |
| **Nivel 1: Vía Rápida** | `smart_scrape(url)` | **R0/R1** | 80% de consultas web (documentación, blogs, noticias). Crawl4AI en CT114 con poda heurística `fit_markdown` (ahorro ~65% tokens). | \$0.00 |
| **Nivel 1.5: Stealth Scrapling** | `scrapling extract fetch <url> <salida.md>` | **R1** | Sitios con Cloudflare Turnstile, interstitial o fingerprinting agresivo. Bypass nativo local sin levantar browser pesado. | \$0.00 |
| **Nivel 2: Evasión Antibot** | `smart_scrape(url)` | **R1** | Traspaso automático si el Nivel 1 detecta bloqueo Cloudflare (403/503/Turnstile). Resuelto con FlareSolverr CT114. | \$0.00 |
| **Nivel 2.5: Obscura CDP (CT114)** | `obscura --stealth fetch <url>` / CDP `:9222` | **R1** | Capturas de pantalla ultra-rápidas (85ms), PDF y CDP headless en CT114 consumiendo solo 5.1MB de RAM con token. | \$0.00 |
| **Nivel 3: Datos Estructurados** | `extract_structured_data(url, schema_json, instruction)` | **R1** | Extracción de esquemas JSON estrictos (catálogos, precios, tablas) procesados por NIM local (`deepseek-ai/deepseek-v4.1-flash`, :8088). | \$0.00 |
| **Nivel 3: Mapeo de Sitios** | `crawl_domain_map(start_url, max_pages)` | **R1** | Rastreo recursivo de sitios completos con Crawlee Python y control de concurrencia. | \$0.00 |
| **Nivel 4: Navegación Interactiva** | `browser_autonomous_action(url, task_prompt, max_steps)` | **R2** | Sitios ultra-complejos que exigen interacción humana real (logins, formularios, clics, scroll infinito) vía Browser-use en CT114. | \$0.00 |
| **Nivel Social $0.00: Redes** | `agent-reach <canal> <accion>` | **R0/R1** | X (Twitter), Reddit, YouTube (transcripciones/subtítulos) y GitHub sin pagar APIs oficiales. | \$0.00 |

---

## 💻 2. Invocación desde MCP y CLI

### Desde Servidor MCP (`floydia-scraper`):
```python
# 1. Extracción web podada
result = await call_tool("floydia-scraper", "smart_scrape", {"url": "https://docs.python.org/3/"})

# 2. Extracción de esquema JSON
schema = '{"version": "string", "release_date": "string", "highlights": ["string"]}'
json_data = await call_tool("floydia-scraper", "extract_structured_data", {
    "url": "https://www.python.org/downloads/release/python-3130/",
    "schema_json": schema
})

# 3. Mapeo recursivo
site_map = await call_tool("floydia-scraper", "crawl_domain_map", {
    "start_url": "https://example.com",
    "max_pages": 10
})

# 4. Acción interactiva
action = await call_tool("floydia-scraper", "browser_autonomous_action", {
    "url": "https://example.com",
    "task_prompt": "Haz clic en el enlace 'Learn more' y lee el título resultante",
    "max_steps": 5
})
```

### Desde Terminal / Bash (`SCRIPTS/safe_run_cli.sh`):
```bash
# Extracción básica
floydia-scrape --url "https://example.com"

# Extracción forzando refresco y salida JSON
floydia-scrape --url "https://example.com" --force-refresh --json

# Extracción estructurada
floydia-scrape --url "https://example.com" --action extract --schema '{"title": "string"}'

# Mapeo de sitio
floydia-scrape --url "https://example.com" --action map --max-pages 10

# Nivel 1.5: Scrapling Stealth (Cloudflare Turnstile local sin API)
scrapling extract fetch "https://sitio-protegido.com" /tmp/resultado.md

# Nivel 2.5: Obscura Headless Browser (CT114 CDP puerto :9222, 5.1MB RAM)
obscura --stealth fetch "https://sitio.com" --eval "document.title"

# Nivel Social $0.00: Agent-Reach (X, Reddit, YouTube)
agent-reach youtube search "tema a investigar"
agent-reach github search "repo-o-libreria"
agent-reach read "https://x.com/usuario/status/123456"
```

---

## 🛡️ 3. Reglas Inmutables y Salvaguardas

1. **HP45 Bloqueado (`#vetado`)**: NUNCA sincronizar ni ejecutar en `192.168.1.205`.
2. **Cero Sobrecarga de RAM**: Todo navegador se ejecuta prioritariamente en CT114 (`ws://192.168.1.238:3000/playwright`). Fallback local pasivo a `/usr/bin/chromium` únicamente en caso de caída de CT114.
3. **Caché SQLite**: Las consultas se persisten en `/home/tec/.local/share/floydia/scraper_cache.db` con TTL de 3600s para respuestas instantáneas (<15ms).
