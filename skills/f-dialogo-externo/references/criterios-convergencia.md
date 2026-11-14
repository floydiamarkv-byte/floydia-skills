# Criterios de convergencia y parada (v2.2)

## Checklist de convergencia
1. Cero huecos ABIERTOS de severidad ALTA.
2. Cero contradicciones sin etiqueta.
3. Toda afirmacion externa verificada localmente o marcada DISPUTADA/RECHAZADA.
4. El entregable cumple el objetivo y criterios de R1.
5. El operador confirma el cierre.

## Reglas de parada
- Convergencia: checklist completa.
- Estancamiento: dos rondas sin hallazgos nuevos de severidad ALTA.
- Irresoluble: un hueco ALTA no se cierra en dos rondas -> DISPUTADO.
- Tope: 4 rondas por defecto; 6 con permiso explicito.
- Cupo: al llegar al tope de envios, cerrar con `SINTESIS.md`, `MANIFEST.sha256` y estado `DEGRADADA`.
- Aborto: el operador dice parar; se escribe `SINTESIS.md` y se sella el manifiesto con lo que haya.

## Severidad
ALTA: cambia la decision o rompe el entregable.
MEDIA: degrada calidad pero no bloquea.
BAJA: cosmetico o de estilo.

## Degradacion
- Sin nodo nuevo o texto inestable tras 240 s: fallo de stream, `handoff`; no reenviar.
- Respuesta vacia, <200 caracteres o mensaje de error del sistema: registrar y `handoff`.
- Relay o extension caidos: un `browse doctor`; si persiste, modo manual y declararlo.
- Cuenta equivocada (`/u/N/` distinto o perfil distinto): abortar de inmediato.
