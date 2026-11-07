# Harness FloydIA v5.1 — auditoría y routing dual (GO/FREE)

Paquete reproducible del harness: registro de modelos con TTL, nomenclatura generada,
presupuesto de salida por tarea, banco de evaluación ciego y orquestador de ciclo completo.

## Una llamada

```bash
python3 scripts/harness_full_audit.py --run --fast     # vigilancia (~25 s)
python3 scripts/harness_full_audit.py --run            # ciclo completo (banco ciego incluido)
python3 scripts/harness_full_audit.py --run --apply    # escribe el SSOT (requiere orden humana)
```

## Qué contiene

| Ruta | Qué es |
|---|---|
| `scripts/harness_full_audit.py` | orquestador de 12 etapas: preflight → registro → lint → allowlist → Suite → banco → recall → conmutador → enjambre → revisión externa → dashboard |
| `scripts/harness_switch.py` | conmutador GO⇄FREE atómico (`os.replace`) con P50/P95/P99 |
| `scripts/peak_guard.py` | baja el modelo principal en ventana peak (01-04 y 06-10 UTC, L-V) |
| `scripts/memory_recall.py` | recuperación por párrafos puntuados (BM25-lite), sin dependencias |
| `scripts/apply_model_names.py` | aplica `[ESTADO][CTX][MODO]` desde el registro |
| `scripts/gen_c7_allowlist.py` | allowlist de modelos gratuitos desde el catálogo vivo |
| `scripts/suite_overlay_gen.py` | overlay que un panel consume en vez de poseer su propia lista |
| `bench/model_state_registry.py` | registro con TTL + lint de nombres |
| `bench/bench_publicable.py` | banco ciego: VCR, seed fija, frío/caliente, McNemar |
| `docs/` | informe, nomenclatura, política de memoria y mapa de 7 capas |

## Principios

1. **Evidencia o silencio**: cada cifra de los informes apunta a un artefacto.
2. **Una sola verdad numérica**: la bolsa se lee de un SSOT; las sumas de carteras no valen.
3. **Ningún nombre se teclea**: estado y contexto salen del registro; `?` cuando no está publicado.
4. **El presupuesto de salida es routing**: un razonador con `max_tokens` corto trunca (0/8 → 8/8 al subirlo).
5. **Un MCP deshabilitado no es un MCP caído**, y un revisor externo que inventa métricas no es evidencia.

MIT · sin credenciales, sin rutas absolutas, sin datos de cuentas.
