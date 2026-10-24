# Consulta externa a IAs web — plantilla

> Copia el bloque correspondiente, pégalo en ChatGPT / Claude / Perplexity, y trae la respuesta.
> El agente la verificará con `verify_citations.py` antes de creerla.

---

## ⚠️ Antes de enviar

- [ ] **Redactado**: sin valores de `.env`, tokens, claves, datos de clientes, PII, ni NDA
- [ ] Solo **nombres** de variables si hacen falta: `OPENROUTER_API_KEY=[REDACTED]`
- [ ] Redacta **antes** de enviar, nunca después: cualquier IA externa puede retener el prompt

---

## 🔴 RONDA 0 — Verificación adversarial (empieza aquí)

> Las dos respuestas de advisors externos anteriores contenian 9 afirmaciones erroneas
> en total. Esta ronda mide si la disciplina de citas corrige ese patron.

```
Actúa como auditor adversarial de un informe técnico. Tu trabajo NO es estar de
acuerdo: es encontrar lo que está mal.

CONTEXTO
Un agente local (Linux, DeepSeek Harness) construye un skill orquestador de
investigación en enjambre: audita herramientas, reparte la investigación en
canales paralelos (web, GitHub, rankings de IA, redes sociales, académico) y
cierra con verificación cruzada.

HERRAMIENTAS VERIFICADAS EN RUNTIME (no las pongas en duda; úsalas de referencia):
- crawl4ai MCP: funciona
- Playwright remoto 192.168.1.238:3000 y FlareSolverr :8191: alcanzables
- Chromium 154 local: instalado
- SIN API KEY funcionan: HN Algolia, OpenRouter /models (460 modelos),
  LMArena dataset en HuggingFace (22 subsets, diario, CC-BY-4.0), OpenAlex,
  arXiv, Jina Reader, Wikipedia
- Bluesky: usar api.bsky.app. OJO: public.api.bsky.app devuelve 403
- Reddit: .json da 403, .rss funciona
- last30days v3.19.0: motor arranca (reddit, hackernews, polymarket, github)
- DuckDuckGo HTML: INTERMITENTE (~1 de cada 4 intentos devuelve resultados)
- Nitter: muerto. X API v2: 401 sin key
- OpenRouter: solo 7 cuentas reales (C7, C9 y OPENROUTER_API_KEY son la misma)

AFIRMACIONES A VERIFICAR O REFUTAR
Para cada una: VERIFICADA / REFUTADA / NO VERIFICABLE, con una URL que hayas
REALMENTE abierto.
1. El repositorio oolong-tea-2026/arena-ai-leaderboards existe y publica
   snapshots diarios de rankings de Arena.
2. Existe una API REST pública oficial de LMArena en api.arena.ai.
3. El proyecto HKUDS/DeepCodeAgent existe y es un agente de deep research.
4. El proyecto mshumer/gpt-agent existe y está activo.
5. El proyecto Alibaba-NLP/WebDancer implementa búsqueda web profunda.
6. STORM (stanford-oval/storm) está mantenido y recibe commits recientemente.
7. langchain-ai/open_deep_research está archivado.
8. Existe un MCP oficial de OpenAI que permita consultar ChatGPT desde un agente.
9. Terminal-Bench va por la versión 2.1.

PREGUNTAS ADICIONALES
10. ¿Existe algún endpoint OFICIAL y documentado para consultar ChatGPT, Claude o
    Grok desde código usando solo una suscripción web (sin API key)? Cita los
    términos de servicio concretos que lo prohíban o permitan.
11. ¿Cuál es la forma más robusta y legal de obtener contenido de X.com sin API key?
12. ¿Qué alternativas a DuckDuckGo funcionan hoy para búsqueda web sin clave?

FORMATO — SOLO JSON VÁLIDO, sin markdown, sin texto antes o después:
{
  "consulta": "verificacion-adversarial-v1",
  "fecha_corte": "2026-09-28",
  "verificaciones": [
    { "afirmacion": "texto evaluado",
      "veredicto": "VERIFICADA|REFUTADA|NO_VERIFICABLE",
      "confianza": "alta|media|baja",
      "citas": [ { "url": "https://...", "titulo": "...",
                   "fecha": "YYYY-MM-DD",
                   "fragmento": "cita textual EXACTA de máximo 30 palabras" } ] }
  ],
  "respuestas": [
    { "pregunta": "número y texto", "respuesta": "máximo 150 palabras",
      "citas": [ { "url": "...", "titulo": "...", "fecha": "YYYY-MM-DD",
                   "fragmento": "cita EXACTA de máximo 30 palabras" } ] }
  ],
  "contradicciones": ["..."],
  "vacios": ["qué no pudiste verificar"],
  "confianza_global": "alta|media|baja"
}

REGLAS INNEGOCIABLES (si las incumples, tu respuesta se descarta):
1. Cada verificación y respuesta lleva ≥1 cita. Sin cita => mover a "vacios".
2. Cita SOLO URLs que hayas abierto y leído en esta sesión. Prohibido inventar,
   reconstruir de memoria o adivinar. URL no visitada = null.
3. "fragmento" debe ser texto LITERAL de la página. Si no lo copias exacto,
   la cita es inválida.
4. Prefiere fuentes primarias (docs, repos, papers) sobre agregadores y blogs.
5. Ante duda, baja la confianza y anótalo en "vacios". No rellenes por completitud.
6. Si no puedes verificar algo, dilo. Una respuesta corta y honesta vale más que
   una larga y especulativa.
7. Prohibido mencionar credenciales, tokens o datos de clientes.
```

---

## 🟡 RONDA 1 — Revisión adversarial de la arquitectura

```
Actúa como arquitecto de sistemas de agentes. Revisión ADVERSARIAL, no refuerzo.

PROPUESTA: skill "f-swarm-research" con 3 capas
  Capa 1 DOCTOR   → inventariar herramientas en 6 estados (encontrado, configurado,
                    probado, falla, archivado, ausente). Nunca imprimir valores.
  Capa 2 ENJAMBRE  → fan-out de subagentes en PARALELO, uno por canal. Cada uno
                    devuelve JSON estricto: claim, confidence, sources[{url,tier,
                    fecha,quote}], contradicts, word_count. Tope 150-300 palabras.
  Capa 3 VEREDICTO → dedup por SHA-256 de URL, verificar citas con Wayback,
                    clasificar [HECHO]/[INFERENCIA]/[DISPUTADO]/[NO_VERIFICABLE],
                    emitir MANIFEST.sha256.
  Consulta externa: humano en el bucle. El agente prepara el prompt, el usuario
  lo pega en ChatGPT/Claude, pega la respuesta, y el agente verifica antes de fusionar.

CONTEXTO
- Motor principal: agentes de texto sin GPU + OpenRouter modelos :free.
- Ya existe un skill hermano "f-investiga" con foco en calidad epistémica.
  Hay conflicto de triggers.

PREGÚNTAS
1. ¿Qué fallo estructural NO veo en este diseño? Sé concreto.
2. ¿La frontera entre "investigación" (f-investiga) y "deliberación multi-opinión"
   está bien puesta? ¿La replantearías?
3. ¿El contrato JSON por subagente basta para evitar contaminación de contexto?
   ¿Añadirías algún campo?
4. ¿Qué harías con afirmaciones en conflicto entre subagentes? Mecanismo exacto,
   no el principio.
5. ¿El modo HIL de consulta externa es la mejor opción, o hay alternativa
   programática que respete los ToS?

FORMATO — SOLO JSON VÁLIDO:
{
  "consulta": "revision-arquitectura-v1",
  "fecha_corte": "2026-09-28",
  "hallazgos": [
    { "afirmacion": "problema o propuesta concreta y atómica",
      "tipo": "FALLO|PROPUESTA|OBJECION",
      "severidad": "alta|media|baja",
      "confianza": "alta|media|baja",
      "citas": [ { "url": "...", "titulo": "...", "fecha": "YYYY-MM-DD",
                   "fragmento": "cita EXACTA de máximo 30 palabras" } ] }
  ],
  "respuestas": [ { "pregunta": "...", "respuesta": "máximo 150 palabras", "citas": [] } ],
  "contradicciones": ["..."],
  "vacios": ["..."],
  "confianza_global": "alta|media|baja"
}

MISMAS REGLAS INNEGOCIABLES que en Ronda 0.
```

---

## 🔵 RONDA 2 — Investigación de dominio

> Rellena `[TEMA]` y `[Corte]`.

```
Actúa como investigador técnico riguroso. Tema: [TEMA]
Fecha de corte: [YYYY-MM-DD]. Solo información publicada hasta esa fecha.

PROCESO
1. Descompón el tema en 4-6 subpreguntas DISJUNTAS.
2. Para cada una busca en fuentes de TIPOS DISTINTOS: ≥1 primaria (docs oficiales,
   repositorio, paper, norma) y ≥1 secundaria (análisis técnico identificable).
   NUNCA solo agregadores.
3. Para cada hallazgo extrae la fecha del HECHO, no la de la página.
4. Busca activamente la CONTRADICCIÓN: ¿qué no cuadra entre las fuentes?
5. Marca como "vacío" todo lo que no hayas verificado.

FORMATO — SOLO JSON VÁLIDO:
{
  "consulta": "[TEMA]",
  "fecha_corte": "[YYYY-MM-DD]",
  "subpreguntas": ["..."],
  "hallazgos": [
    { "afirmacion": "una afirmación atómica y verificable",
      "subpregunta": "a cuál responde",
      "confianza": "alta|media|baja",
      "tipo_fuente": "primaria|secundaria|agregador",
      "citas": [ { "url": "https://...", "titulo": "...",
                   "fecha_publicacion": "YYYY-MM-DD",
                   "fragmento": "cita textual EXACTA de máximo 30 palabras" } ] }
  ],
  "contradicciones": [
    { "tema": "...", "fuente_a": "...", "afirmacion_a": "...",
      "fuente_b": "...", "afirmacion_b": "..." } ],
  "vacios": ["qué NO pudiste verificar"],
  "cobertura": { "canales_consultados": ["..."], "canales_no_consultados": ["..."] },
  "confianza_global": "alta|media|baja"
}

REGLAS
1. Cada hallazgo lleva ≥1 cita. Sin cita => "vacios".
2. Cita solo URLs que hayas abierto. Prohibido inventar.
3. "fragmento" literal. Si no lo copias exacto, la cita es inválida.
4. Si dos fuentes se contradicen, NO elijas: repórtalas ambas.
5. No uses cifras de blogs agregadores sin ir a la fuente original.
6. Prohibido credenciales, tokens o datos de clientes.
```

---

## ⚪ GENÉRICO — Consulta rápida

```
Responde en español, máximo 120 palabras, formato JSON puro sin markdown.

{
  "pregunta": "[TU PREGUNTA]",
  "respuesta": "...",
  "confianza": "alta|media|baja",
  "citas": [ { "url": "https://...", "fecha": "YYYY-MM-DD",
               "fragmento": "cita textual EXACTA de máximo 30 palabras" } ],
  "vacios": ["qué no pudiste verificar"]
}

REGLAS: cita solo URLs que hayas abierto y leído ahora. Prohibido inventar URLs.
Cada afirmación necesita su cita literal. Si no sabes, di "no verificado" — no rellenes.
```

---

## ♊ CONSULTA EXTERNA DIRIGIDA A GEMINI (gemini.google.com)

> [!IMPORTANT]
> **Condición de Uso Estricta**:
> - **ACTIVAR SOLO** cuando el prompt de consulta externa vaya dirigido a **Gemini** (`gemini.google.com` / Gemini Chat / Gemini App).
> - **PROHIBIDO** incluir este bloque de contexto si la consulta va dirigida a ChatGPT, Claude, Grok o Perplexity (para ellos, usar las Rondas 0, 1, 2 o Genérico anteriores).

```
Actúa como mi Asistente Técnico y Arquitecto de Software.

CONTEXTO DE ENTORNO Y BASE DE VERDAD (GROUND TRUTH):
Mi entorno de trabajo y base de verdad técnica está estructurado en dos niveles interconectados:
1. Base de Verdad Profunda: Un ecosistema de 41 cuadernos en Google NotebookLM con más de 1,720 fuentes técnicas curadas (manuales oficiales, especificaciones de hardware, IoT, SRE Linux/Proxmox, RouterOS MikroTik y Desarrollo Web Luxury).
2. Base de Conocimiento Operativa: Bóveda en Obsidian (Memory Bank), estructurada con [[wikilinks]], MOCs de síntesis y decisiones de arquitectura (SSOT).
[Si estás en gemini.google.com con integración de Google Drive activa, puedes referenciar y buscar directamente los documentos exportados de NotebookLM].

CONSULTA TÉCNICA A RESOLVER:
[TEMA O PREGUNTA CONCRETA]

REGLAS DE RESPUESTA:
1. Respeta las decisiones de arquitectura de mis sistemas y no inventes configuraciones incompatibles.
2. Cita fuentes técnicas primarias (código fuente, RFCs, documentación oficial verificable).
3. Responde en español, formato estructurado en Markdown, conciso y accionable.
```

---

## 📊 Qué hace el agente con la respuesta

| Acción | Herramienta | Resultado |
| :-- | :-- | :-- |
| Verificar cada URL | Wayback + `curl` | Distingue URL alucinada de URL que cambió |
| Comprobar el fragmento | `verify_citations.py --deep` | Confirma que el texto existe literalmente |
| Detectar alucinación semántica | `extract_title()` | Cita una URL real que habla de otro tema |
| Contrastar con el enjambre | `merge_findings.py` | Marca coincidencias y contradicciones |
| Etiquetar | — | `[HECHO]` / `[DISPUTADO]` / `[RECHAZADA]` |
