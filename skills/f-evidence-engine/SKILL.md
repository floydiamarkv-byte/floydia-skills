---
name: f-evidence-engine
description: "Motor determinista de certificación y verificación de evidencia del FloydIA Agent OS v1.0. Hace cumplir mecánicamente el principio 'Evidencia antes de Afirmar': prohíbe dar por resuelta cualquier tarea sin validar un artefacto técnico concreto (código de salida exit 0, hash SHA256 de archivo o JSON de aserciones de Playwright remoto). USAR antes de cerrar cualquier tarea, generar journals o emitir declaraciones de conformidad técnica. NO USAR para consultas informativas triviales ni tareas R0 de solo lectura."
version: 1.0.0
triggers:
  - /f-evidence-engine
  - /f-evidence
  - /evidence
  - certificar tarea
  - validar evidencia
  - evidencia antes de afirmar
---

# Skill: Evidence & Certification Engine (`f-evidence-engine` v1.0)
## Verification Plane & Deterministic Evidence Gate

> **Propósito**: Mecanizar el principio rector de gobernanza del ecosistema: **"Evidencia antes de Afirmar"**. Ningún agente de IA puede declarar un objetivo o hito como resuelto basándose únicamente en suposiciones, salidas inferidas o respuestas de texto plano. Debe aportarse un comprobante criptográfico o técnico verificable.

---

## 🎯 1. Tipos de Certificación Mecánica

```bash
# 1. Certificar que un archivo existe y obtener su hash SHA256 inmutable
python3 SCRIPTS/evidence_engine.py --claim file --target "dist.tar.gz"

# 2. Certificar que una suite de pruebas o comando finalizó con éxito (exit code 0)
python3 SCRIPTS/evidence_engine.py --claim command --target "npm test"

# 3. Certificar aserciones remotas de Playwright CT114
python3 SCRIPTS/evidence_engine.py --claim assertions --target "qa_summary.json"

# 4. Certificación por Enjambre Multiconsulta (Consenso 5 Motores a $0.00)
python3 SCRIPTS/evidence_engine.py --claim consensus --target "hipotesis_o_resultado.txt"
```

> **Regla de Consenso del Enjambre**: la composición de motores y reglas de consenso NO se definen aquí (SSOT): leer `memory-bank/prompts/ENJAMBRE_5_MOTORES_SSOT.md`. El recibo se valida únicamente con mayoría calificada (≥4/5 votos afirmativos sin alucinaciones) sobre los motores vivos definidos en ese SSOT.

---

## 🛡️ 2. El Contrato de Evidencia E5

Todo ticket, tarea o journal que aspire a declararse como `DONE` debe adjuntar el bloque de recibo emitido en `.session/evidence/`:

```json
{
  "timestamp": "2026-09-14T08:15:00",
  "claim_type": "command_exit_code",
  "target": "python3 SCRIPTS/skill_lint.py",
  "verified": true,
  "evidence": {
    "exit_code": 0,
    "stdout_snippet": "18 skills activas 100% PASS"
  },
  "evidence_receipt": ".session/evidence/evidence_a1b2c3d4.json"
}
```

---

## 🔄 3. Compatibilidad Multi-Agente

| Agente | Soporte | Notas |
|---|:---:|---|
| **Antigravity IDE** | ✅ Completo | Ejecución en el rol Revisor del arnés |
| **OpenCode CLI** | ✅ Completo | Certificación determinista vía CLI |
| **DeepSeek Harness** | ✅ Completo | Salida estricta con código de salida |
| **Hermes CLI** | ✅ Completo | Auditoría previa a la redacción del journal |
