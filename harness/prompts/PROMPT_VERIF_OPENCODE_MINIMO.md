Ejecuta SOLO estos 3 comandos, en orden, sin explorar el repositorio ni escribir scripts. Tienes 3 minutos.

1) python3 -c "import json,re;p='/home/tec/.config/opencode/opencode.jsonc';t=open(p).read();t='\n'.join(re.sub(r'^\s*//.*$','',l) for l in t.splitlines());d=json.loads(t);print('modelos',sum(len(v.get('models',{})) for v in d['provider'].values()));print('model',d['model']);print('small',d['small_model']);print('interrogacion',sum(1 for v in d['provider'].values() for m in v.get('models',{}).values() if '[?]' in m.get('name','')))"

2) python3 scratch/harness_v51/model_state_registry.py --lint; echo EXIT=$?

3) curl -s -m 20 -o /dev/null -w 'nim_http=%{http_code}\n' -X POST http://127.0.0.1:8088/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"deepseek-ai/deepseek-v4.1-flash","messages":[{"role":"user","content":"ok"}],"max_tokens":400}'

Devuelve SOLO este JSON, sin texto adicional:
{"agente":"opencode","modelos":{"catalogo":0,"default":"","small":"","con_signo_interrogacion":0},"pruebas":[{"nombre":"jsonc","exit":0,"salida":"","veredicto":"OK|FALLO"},{"nombre":"lint","exit":0,"salida":"","veredicto":"OK|FALLO"},{"nombre":"nim","exit":0,"salida":"","veredicto":"OK|FALLO"}],"veredicto":{"artefacto":"CERTIFICADO|NO CERTIFICADO","entorno":"CERTIFICADO|NO CERTIFICADO"},"hallazgos":[],"no_verificado":[]}
