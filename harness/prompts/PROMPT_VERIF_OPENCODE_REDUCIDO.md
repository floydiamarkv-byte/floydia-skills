<rol>
Ingeniero de plataforma en OpenCode Desktop. Certificas tu configuración con evidencia. 8 minutos:
no explores el repo. Ejecuta los 5 pasos y responde.
</rol>

<pasos>
1. Parsea `~/.config/opencode/opencode.jsonc` (quita líneas `//` antes de json.loads) y reporta:
   nº de modelos total, por proveedor, `model`, `small_model`, `enabled_providers`.
2. Cuenta cuántos nombres empiezan por `[` y cuántos llevan `[?]` (contexto/existencia no publicados).
3. Para el proveedor del `model` por defecto, una llamada real de 200 tokens. Registra modelo devuelto,
   latencia y `usage.allowance`. Si da 429, dilo con el cuerpo.
4. Comprueba la ruta NIM: `deepseek-ai/deepseek-v4.1-flash` con max_tokens 600 en :8088. Registra latencia.
5. `python3 scratch/harness_v51/model_state_registry.py --lint; echo EXIT=$?` (espera `{}` y 0).
</pasos>

<salida>
Responde SOLO con este JSON en la última línea:

{"agente":"opencode","host":"...","modelos":{"catalogo":0,"default":"...","small":"...","con_signo_interrogacion":0},
 "mcp":{"ssot":21,"cliente":0},
 "pruebas":[{"nombre":"jsonc","exit":0,"salida":"...","veredicto":"OK|FALLO|NO_VERIFICADO"},
            {"nombre":"llamada_go","exit":0,"salida":"...","veredicto":"..."},
            {"nombre":"llamada_nim","exit":0,"salida":"...","veredicto":"..."},
            {"nombre":"lint","exit":0,"salida":"...","veredicto":"..."}],
 "veredicto":{"artefacto":"CERTIFICADO|NO CERTIFICADO","entorno":"CERTIFICADO|NO CERTIFICADO"},
 "hallazgos":[{"id":"H1","severidad":"alta|media|baja","evidencia":"...","fix":"..."}],
 "no_verificado":["..."]}
</salida>
