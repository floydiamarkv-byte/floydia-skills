#!/usr/bin/env bash
# run_eval.sh — Suite de regresión de f-swarm-research
#
# Cada test reproduce un fallo REAL encontrado durante el desarrollo.
# Ejecutar tras CUALQUIER cambio en scripts/:
#     bash .agents/skills/f-investiga/scripts/run_eval.sh
#
# Cobertura de red: 2 tests. Sin red, los tests de red se saltan (SKIP),
# no se falsean como PASS.

set -uo pipefail
cd "$(dirname "$0")"

PASS=0; FAIL=0; SKIP=0
ok()   { echo "  PASS  $1"; PASS=$((PASS+1)); }
ko()   { echo "  FAIL  $1 -> $2"; FAIL=$((FAIL+1)); }
chk()  { if [ "$2" = "OK" ]; then ok "$1"; else ko "$1" "$2"; fi; }
t()    { if eval "$2" >/dev/null 2>&1; then ok "$1"; else ko "$1" "comando fallo"; fi; }
net()  { timeout 12 curl -s -o /dev/null -w '' https://hn.algolia.com 2>/dev/null; }

echo "########## SUITE f-swarm-research ##########"
echo "--- Sintaxis de scripts ---"
for f in doctor.py fanout_models.py verify_citations.py merge_findings.py rankings_ia.py senal_social.py busqueda_web.py; do
  t "$f importa" "python3 -c \"import ast;ast.parse(open('$f').read())\""
done

echo "--- E8: control de coste \$0.00 (sin red) ---"
R=$(timeout 60 python3 fanout_models.py --prompt t --models anthropic/claude-sonnet-5.5 2>/dev/null); E=$?
chk "E8 aborta con codigo 2"      "$([ "$E" = 2 ] && echo OK)"
chk "E8 reporta MODELO_NO_FREE"   "$(echo "$R" | grep -q MODELO_NO_FREE && echo OK)"
chk "E8 deduplica a 7 cuentas"    "$([ "$(echo "$R" | grep -c '_OPENROUTER' | tr -d ' ')" = 7 ] && echo OK)"
chk "E8 no infla con alias"       "$(echo "$R" | grep -q '"C9_OPENROUTER"' && echo FALLO || echo OK)"

echo "--- E11: las 7 fuentes keyless siguen vivas (sin web_search) ---"
KEYLESS=0
for u in "https://hn.algolia.com/api/v1/search?query=t&hitsPerPage=1" \
         "https://api.openalex.org/works?search=t&per-page=1" \
         "https://export.arxiv.org/api/query?search_query=all:t&max_results=1" \
         "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srsearch=t" \
         "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=t&limit=1" \
         "https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset" \
         "https://r.jina.ai/https://example.com"; do
  c=$(timeout 15 curl -s -o /dev/null -w "%{http_code}" -A "Mozilla/5.0" "$u" 2>/dev/null)
  [ "$c" = "200" ] && KEYLESS=$((KEYLESS+1))
done
chk "E11 7/7 fuentes keyless" "$([ "$KEYLESS" = 7 ] && echo OK)"

echo "--- E12: busqueda_web --stats no gasta cuota (solo lee config) ---"
chk "E12 stats de busqueda_web" "$(timeout 60 python3 busqueda_web.py x --stats 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('OK' if d.get('serper_key') and 'variables_buscadas' in d else 'FALLO')")"

echo "--- E7: epistemologia del consenso (sin red) ---"
D=$(mktemp -d)
cat > "$D/u1.json" <<'J'
[{"id":"a","claim":"Misma afirmacion compartida por todos los motores del enjambre","confidence":0.8,"sources":[{"url":"https://example.com/a"}]}]
J
cp "$D/u1.json" "$D/u2.json"; cp "$D/u1.json" "$D/u3.json"
chk "E7 trampa de premisas" "$(timeout 40 python3 merge_findings.py "$D"/u1.json "$D"/u2.json "$D"/u3.json 2>/dev/null | python3 -c "
import sys,json
v=json.load(sys.stdin)['consenso']['veredicto']
print('OK' if v=='UNANIMIDAD_SOBRE_PREMISA_NO_VERIFICADA' else 'FALLO '+v)")"

cat > "$D/f1.json" <<'J'
[{"id":"a","claim":"La descomposicion iterativa con sintesis jerarquica permite escalar la cobertura de fuentes","confidence":0.85,"sources":[{"url":"https://example.com/x"}]}]
J
cat > "$D/f2.json" <<'J'
[{"id":"b","claim":"La descomposicion iterativa con sintesis jerarquica es la unica via para escalar fuentes","confidence":0.6,"sources":[{"url":"https://example.com/x"}]}]
J
cat > "$D/f3.json" <<'J'
[{"id":"c","claim":"La descomposicion iterativa con sintesis jerarquica no es la unica via; chunking funciona igual","confidence":0.7,"sources":[{"url":"https://example.com/y"}]}]
J
chk "E7b mayoria + divergencia" "$(timeout 40 python3 merge_findings.py "$D"/f1.json "$D"/f2.json "$D"/f3.json 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)['consenso']
print('OK' if (d['veredicto'],d['divergencia'])==('MAYORIA_2',0.333) else f\"FALLO {d['veredicto']} {d['divergencia']}\")")"
rm -rf "$D"

if net; then
  echo "--- E4/E5: verificacion de citas (CON RED) ---"
  F=$(mktemp --suffix=.json)   # el sufijo importa: load_findings parsea por extension
  cat > "$F" <<'J'
[{"id":"real","claim":"control real","confidence":0.9,"sources":[{"url":"https://github.com/agentskills/agentskills"}]},
 {"id":"inventada","claim":"control inventada","confidence":0.5,"sources":[{"url":"https://no-existe-abc987654321.com/x"}]},
 {"id":"semantica","claim":"control semantica","confidence":0.8,
  "sources":[{"url":"https://arxiv.org/abs/2310.08562","quote":"Plan-and-Solve Prompting"}]}]
J
  # E9: una URL archivable pero 403 = BLOQUEADA, no ALUCINADA.
  # Regresion real: 4 citas de openai.com fueron marcadas NO_VERIFICABLE.
  B=$(mktemp --suffix=.json)
  cat > "$B" <<'J'
[{"id":"bloqueo","claim":"ToS de OpenAI accesible solo desde otra red","confidence":0.9,
  "sources":[{"url":"https://openai.com/policies/row-terms-of-use/"}]}]
J
  chk "E9 403+archivada = DISPUTADO (no NO_VERIFICABLE)" "$(timeout 120 python3 verify_citations.py "$B" 2>/dev/null | python3 -c "
import sys,json
e=json.load(sys.stdin)['hallazgos'][0]['estado']
print('OK' if e=='DISPUTADO' else 'FALLO '+e)")"
  rm -f "$B"

  # E10: HN Algolia devuelve HTTP 400 si usas `q=` en vez de `query=`.
  # Fallo silencioso (no es "sin resultados", es un 400). Verificado 2026-09-28.
  chk "E10 HN usa query= (no q=)" "$(timeout 60 python3 -c "
import urllib.request, urllib.parse, json
UA='Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0'
try:
    u='https://hn.algolia.com/api/v1/search?query=test&hitsPerPage=1'
    r=urllib.request.Request(u, headers={'User-Agent':UA})
    d=json.loads(urllib.request.urlopen(r,timeout=15).read().decode())
    print('OK' if 'nbHits' in d else 'FALLO')
except Exception: print('FALLO')")"

  chk "E4/E5 clasificacion correcta" "$(timeout 120 python3 verify_citations.py "$F" 2>/dev/null | python3 -c "
import sys,json
h={x['id']:x['estado'] for x in json.load(sys.stdin)['hallazgos']}
ok = h.get('real')=='HECHO' and h.get('inventada')=='NO_VERIFICABLE' and h.get('semantica')=='NO_VERIFICABLE'
print('OK' if ok else 'FALLO '+str(h))")"
  rm -f "$F"
else
  echo "  SKIP  tests de red (sin conectividad)"; SKIP=$((SKIP+1))
fi

echo
echo "########## $PASS PASS / $FAIL FAIL / $SKIP SKIP ##########"
[ "$FAIL" -eq 0 ] || exit 1
