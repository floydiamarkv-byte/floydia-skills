# Auditoría completa del harness — 20261107-100437

**Veredicto: VERDE** · 24 s · modo --fast · propuesta (sin aplicar)

| Etapa | Estado | ms |
|---|---|---|
| preflight | — | — |
| registro | ✔ | 1933 |
| contexto | ✔ | 1497 |
| lint | ✔ | 1616 |
| nombres | ✔ | 185 |
| allowlist | ✔ | 859 |
| suite_overlay | ✔ | 985 |
| suite_cotejo | ✔ | 1286 |
| switch | ✔ | 227 |
| dashboard | ✔ | 743 |
| enjambre | OK | — |
| revision_externa | OK | — |

Banco ciego v2: GO **8/8** · FREE **1/8** · p=0.0156

**Revisión externa** (nim_local/deepseek-v4.1-flash, 9729 ms):
- veredicto: AMARILLO
- acción: Conciliar los ok por cuenta y el inventario declarado antes de aprobar el harness como VERDE.
- riesgos: totals.requests=17 frente a suma de stats.ok=15 en las cuentas; faltan 2 ok sin categoría de error registrada.; C1 tiene dispatched=5 y ok=4; C7 tiene dispatched=4 y ok=3, sin http_429/timeouts/errors/degenerate que expliquen la diferencia.; clientes_declaran.opencode=11 y clientes_declaran.dsh=0 frente a ssot_servers=21; sin datos para juzgar si esa discrepancia es esperada.; hermes_enabled=20 y hermes_down=[] con hermes_disabled=["crawl4ai"]; sin datos sobre impacto operativo de esa desactivación.; Todos los comandos revisados tienen exit=0 y preflight.ok=true, pero persisten inconsistencias de conteo no explicadas.

Artefacto: `out/full_audit_20261107-100437.json` · log: `out/full_audit_20261107-100437.log`
