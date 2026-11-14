# Protocolo de rondas (v2.2 — 4 rondas densas)

## R1 — Encuadre y plan adversarial
Objetivo: reformular el brief, fijar criterios de exito y producir un plan adversarial con huecos y severidad.
Pedir: plan por categorias, huecos con severidad ALTA/MEDIA/BAJA, evidencia necesaria por hueco y preguntas al operador.
Cierra: hay plan y huecos enumerados.

## R2 — Evidencia
Objetivo: verificar o refutar cada hueco con extractos reales (<= 150 lineas).
Pedir: veredicto por hueco con archivo:linea, contradicciones con la ronda anterior y evidencia que falta.
Cierra: cada hueco tiene CONFIRMADO / REFUTADO / PARCIAL, o se declara falta de evidencia.

## R3 — Correccion
Objetivo: corregir falsos positivos y depurar el plan.
Pedir: reevaluacion de los huecos corregidos, plan final de maximo 6 cambios con test y checklist de cierre.
Cierra: plan final y checklist.

## R4 — Cierre
Objetivo: informe consolidado.
Pedir: veredicto ejecutivo, tabla de hallazgos, top 3, plan, funciones nuevas, checklist y riesgos aceptados.
Cierra: `SINTESIS.md`.

## Presupuesto
- 1 envio por ronda; maximo 4 por defecto, 6 con permiso.
- <= 150 lineas de codigo por ronda.
- Respuesta esperada: 600-800 palabras.
- Intentos fallidos cuentan en `CONSULTAS.md`, pero no consumen ronda.

## Encabezado de ronda
Ronda N | Objetivo | Que se envia | Que se espera | Criterio de cierre

## Integridad de respuesta
- Contar nodos `model-response` antes de enviar y exigir +1.
- Inicio valido si se vio el boton de parada O hay nodo nuevo; fin solo con nodo nuevo y parada no visible.
- Tolerar pensamiento largo (hasta 240 s) sin declarar stream congelado.
- Esperar 2 s de estabilizacion y excluir el bloque de pensamiento.
- Extraer en Markdown, no en texto plano.
- Exigir >200 caracteres y descartar mensajes de error del sistema.
