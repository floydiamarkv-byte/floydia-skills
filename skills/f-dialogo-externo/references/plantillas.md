# Plantillas (v2.1)

## ESTADO.md
Sesion: <slug> | Fecha: <YYYY-MM-DD> | Ronda: N/4 | Cupo: M/5
IA externa: <modelo> | Cuenta: <u/N> | Modo: <Argon Medium>
URL conversacion: <https://gemini.google.com/u/N/app/ID>
Objetivo: <una frase>
Huecos abiertos: H1..Hn (severidad)
Huecos cerrados: ...
Decisiones: ...
Siguiente accion: <emitir R(N+1) | cerrar>

## RONDA_N_PROMPT.md
Ronda: N | Objetivo: ...
Que se envia: <resumen o texto literal>
Que se espera: <formato exacto>
Criterio de cierre de esta ronda: ...

## RONDA_N_RESPUESTA.md
Fuente: EXTERNA/<modelo> | Cuenta: <u/N> | URL: <...> | Fecha: <YYYY-MM-DD HH:MM> | Estado: NO VERIFICADA
<respuesta literal>

## CONSULTAS.md
| Hora | Ronda | Enviados | Recibidos | Nodos antes/despues | Resultado |
|---|---|---|---|---|---|

## SINTESIS.md
Resultado: ...
Afirmaciones: [HECHO] / [DISPUTADO] / [RECHAZADA] con verificacion local
Huecos: cerrados / disputados
Rondas usadas: N | Cupo: M
Checklist de convergencia: X/5
