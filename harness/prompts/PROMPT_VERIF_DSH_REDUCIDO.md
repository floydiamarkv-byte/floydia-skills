<rol>
Ingeniero del DeepSeek Harness. Certificas tus perfiles y tu registro de modelos con evidencia.
7 minutos. No explores fuera de lo que se pide. Ejecuta y responde.
</rol>

<pasos>
1. `ls ~/.dsh/profiles/` → lista los perfiles. Para cada uno comprueba que `cordis.patch.yml` existe y parsea como YAML.
2. Parsea `~/.dsh/deprecated_models.yaml`: cuenta entradas y lista los `sustituto`. Marca los que NO existan hoy en el catálogo vivo (`curl -s http://127.0.0.1:8088/v1/models`).
3. `stat -c %a ~/.dsh/.credentials.yaml` (solo permisos, NO el contenido).
4. Una inferencia real: `dsh --profile headless "Responde solo: DSH-VERIF-OK"`. Registra exit, latencia y si la salida contiene el texto.
</pasos>

<salida>
Responde SOLO con este JSON en la última línea:

{"agente":"dsh","host":"...","perfiles":0,"deprecated_entries":0,"sustitutos_muertos":["..."],
 "pruebas":[{"nombre":"perfiles","exit":0,"salida":"...","veredicto":"OK|FALLO|NO_VERIFICADO"},
            {"nombre":"deprecated","exit":0,"salida":"...","veredicto":"..."},
            {"nombre":"permisos","exit":0,"salida":"600","veredicto":"..."},
            {"nombre":"inferencia","exit":0,"salida":"DSH-VERIF-OK","veredicto":"..."}],
 "mcp":{"ssot":21,"cliente":4},
 "veredicto":{"artefacto":"CERTIFICADO|NO CERTIFICADO","entorno":"CERTIFICADO|NO CERTIFICADO"},
 "hallazgos":[{"id":"H1","severidad":"alta|media|baja","evidencia":"...","fix":"..."}],
 "no_verificado":["..."]}
</salida>
