# Research: Línea de tiempo y puntos de control

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-18

## R1. Reconstruir hacia adelante re-simulando o hacia atrás invirtiendo cambios — decisión central

El enunciado (P2 §3.6 y §5.5) permite las dos y exige documentar la elección con evidencia.

**Alternativa A — hacia atrás, invirtiendo cambios.** Partir del estado actual y deshacer los
cambios de las acciones más recientes hasta llegar al instante pedido. P1 §4.6 ya tiene el mecanismo:
cada cambio registra una función que lo deshace, y el pergamino las ejecuta en orden inverso.

- A favor: el mecanismo existe y está probado; no necesita el estado del generador aleatorio.
- En contra, y es decisivo: esas funciones de deshacer son **cierres en memoria**, no datos. No se
  pueden escribir en el archivo de partida, así que FR-028 obligaría a inventar en paralelo una
  representación de los cambios como datos y a mantener las dos en paso. Además deshacer modifica el
  estado real para después volver a aplicarlo, lo que arriesga FR-007 y SC-008: una consulta que
  pasa por el estado vivo puede dejarlo distinto si algo falla en medio.

**Alternativa B — hacia adelante, re-simulando desde un punto de control.** Guardar una copia
completa del estado cada K acciones y, para consultar, restaurar el punto de control anterior al
instante pedido y volver a ejecutar las acciones del jugador que faltan.

- A favor: la información mínima que hay que almacenar entre puntos de control es **la secuencia de
  acciones del jugador**, que ya es un dato serializable y que el proyecto ya graba en
  `partida.log`. Esto satisface FR-023 sin estructuras nuevas y hace que FR-028 sea casi gratis.
- A favor: la consulta se resuelve sobre una partida **aparte**, construida para la consulta y
  descartada al terminar. El estado vivo nunca se toca, así que FR-007 y SC-008 se cumplen por
  construcción y no por cuidado.
- A favor: el proyecto ya tiene las dos piezas que esto necesita, probadas desde P1:
  `guardado.tomar_snapshot` / `restaurar_partida` para la copia completa, y la reproducción de
  acciones de `bitacora`. La capacidad reutiliza en vez de duplicar.
- En contra: exige guardar el estado del generador `random.Random` en cada punto de control
  (FR-025), porque sin él una re-simulación saca números distintos y el combate no coincide.
- En contra: una consulta cuesta re-ejecutar hasta K acciones, mientras que la alternativa A cuesta
  deshacer hasta K acciones. Son del mismo orden.

**Decisión**: alternativa B. Lo que la inclina no es el rendimiento, que es comparable, sino que
hace la persistencia (FR-028) y la no interferencia (FR-007) consecuencias del diseño en vez de cosas
que haya que cuidar. El costo que paga, guardar el estado del generador, es un requisito explícito
del enunciado y por tanto estaba previsto.

**Evidencia que se recoge**: `--bench` mide el tiempo de consulta para tres valores de K y lo compara
con no usar puntos de control (re-simular siempre desde el inicio) y con guardar una copia por
acción. Esos números van a `DECISIONES.md` §P2 5.5.

## R2. Qué se guarda en el archivo y qué no — confirmada por el grupo

**Pregunta**: FR-028 obliga a conservar la línea de tiempo completa al guardar. ¿Van los puntos de
control al archivo?

**Decisión**: no. Al archivo va la **secuencia de acciones del jugador con su instante**, que es la
historia; los puntos de control son una caché de consulta y se reconstruyen.

**Por qué**: con K = 50 y 5 000 acciones habría 100 copias completas del estado en el archivo. Eso
es exactamente el crecimiento «acciones por tamaño del estado» dividido por K que FR-024 quiere
evitar en memoria, y no hay ninguna razón para aceptarlo en disco cuando la historia cabe en una
lista de acciones.

**Consecuencia asumida**: la primera consulta de una partida recién cargada cuesta una re-simulación
completa para reconstruir los puntos de control. Está declarado en las clarificaciones de `spec.md` y
el límite de FR-030 se mide con los puntos de control ya construidos, que es la situación de una
partida en curso. Es un costo de una sola vez y solo para partidas cargadas.

## R3. Cómo encontrar el punto de control anterior a un instante — confirmada por el grupo

**Pregunta**: FR-026 pide que ubicar el punto de control más cercano no cueste proporcionalmente al
número de puntos de control, y §5.5 dice que es una búsqueda frecuente.

**Alternativas**:

1. Recorrer la lista de puntos de control de atrás hacia adelante. Proporcional al número de puntos,
   que en una partida de 5 000 acciones con K = 50 son 100: barato en la práctica, pero es
   exactamente lo que el requisito prohíbe.
2. Dividir el instante entre K para calcular el índice. No funciona: los instantes no son
   proporcionales al número de acciones, porque cada acción cuesta distinto según el terreno (001) y
   la velocidad del actor.
3. Búsqueda binaria sobre la lista de puntos de control, que está ordenada por instante porque se
   agregan en orden creciente.

**Decisión**: alternativa 3, con una función nueva `ultimo_menor_o_igual` en
`src/estructuras_datos/busqueda_binaria.py`. El módulo ya existe de la capacidad 002 y ya implementa
búsqueda exacta sin `bisect`; esta es la variante que devuelve la última posición cuyo valor no
supera el buscado, que es justo «el último punto de control en o antes de t».

**Por qué una función nueva y no reusar `buscar`**: `buscar` devuelve la posición exacta o la
ausencia. Aquí casi nunca hay coincidencia exacta y lo que se necesita es el predecesor. Son dos
contratos distintos sobre la misma técnica, y mezclarlos en una función con una bandera haría más
difícil de leer la que ya está probada.

## R4. Cómo recortar la línea al usar un pergamino — confirmada por el grupo

**Pregunta**: FR-015 exige que el recorte no recorra toda la historia.

**Decisión**: las entradas de la línea están en una lista en orden creciente de número de acción, y
los puntos de control también. Un retroceso quita entradas **del final**, y quita del final los
puntos de control cuyo instante quedó por encima del nuevo reloj. El costo depende de cuántas
entradas se quitan, no de cuántas quedan.

**Por qué no hace falta nada más**: el pergamino de P1 revierte una acción por uso y está limitado a
5, así que un recorte quita unas pocas entradas y a lo sumo un punto de control. La estructura más
simple que cumple el requisito es la correcta.

**Caso que importa**: un punto de control cuyo instante sigue siendo menor o igual que el nuevo reloj
**no** se descarta, porque describe un instante que sigue existiendo en la historia. Solo se
descartan los que quedaron en el futuro.

## R5. Qué cuenta como una entrada de la línea — confirmada por el grupo

**Pregunta**: FR-023 pide almacenar «solo la información necesaria para reconstruir los cambios».
Con la alternativa B de R1, eso es la acción del jugador. ¿Qué lleva exactamente?

**Decisión**: el número de acción, el instante en que el jugador la tomó, el tipo de acción y su
argumento. Nada más: el resto del estado se deduce re-simulando.

**El caso del cursor del inventario**: `sig` y `ant` mueven el cursor del inventario y **no** son
acciones del jugador (no consumen tiempo, P1 §10.2), pero sí cambian cuál es el objeto seleccionado,
y `usar`, `equipar` y `soltar` actúan sobre el seleccionado. Una re-simulación que ignore los
movimientos del cursor puede usar o soltar otro objeto y divergir.

**Consecuencia**: los movimientos de cursor se registran en la línea de tiempo y en `partida.log`
como registros que no son acciones del jugador: no incrementan el contador de acciones, no consumen
tiempo y no generan punto de control, pero se re-aplican en el mismo orden al re-simular. Esto
corrige una omisión de las capacidades anteriores, donde una bitácora con movimientos de cursor no
reproducía fielmente una partida que usara objetos no primeros de la lista.

**Alternativa descartada**: guardar en cada entrada el uid del objeto sobre el que la acción actuó,
para no depender del cursor. Haría la entrada más grande y dejaría la bitácora de P1 sin arreglar,
que es un defecto real y no solo un obstáculo para esta capacidad.

## R6. Dónde se enganchan los registros — confirmada por el grupo

**Decisión**: en `Partida`, en el único punto donde una acción del jugador se cierra
(`_cerrar_accion`), que es por donde pasan todas. Allí se agrega la entrada a la línea y, si
corresponde por K, se toma el punto de control. El cursor se registra desde donde se mueve.

**Por qué ahí y no en el controlador**: la línea de tiempo es estado del juego (FR-028) y debe
existir igual en una partida jugada, en una reproducida con `--replay` y en una re-simulada para una
consulta. El controlador no participa en las dos últimas.

**Punto de control del instante 0**: se toma en `iniciar`, para que siempre exista un punto de
control anterior a cualquier instante consultable y la búsqueda de R3 nunca devuelva «ninguno».

**Lo que la re-simulación no debe hacer**: una partida construida para una consulta no graba
bitácora, no registra puntajes y no toma puntos de control propios, para que una consulta no cueste
memoria ni deje rastro (FR-007).

## R7. El resumen de la consulta — confirmada por el grupo

**Decisión**: el resumen se construye en un módulo propio (`resumen_historia.py`) que recibe una
partida reconstruida y devuelve los campos de FR-006 como datos, sin imprimir. La vista los formatea
para `historia`, y `--hasta` los imprime con el mismo formateo sin instanciar la vista.

**Por qué separar los datos del formato**: FR-017 exige que `--hasta` imprima «el mismo resumen» que
`historia`. Si el resumen se construyera dentro de la vista, `--hasta` tendría que instanciarla, que
es justo lo que el requisito prohíbe. Con el resumen como datos, las pruebas también comparan
estructuras y no texto.

## R8. Formato del archivo de partida — confirmada por el grupo

**Decisión**: `FORMATO_VERSION` sube de 2 a **3**, y la versión 3 lleva a la vez la sección del mapa
conocido de la capacidad 003 y la sección de la línea de tiempo de esta. Un archivo de versión 1
(primera parte) o 2 (capacidades 001 y 002) se rechaza con el mensaje de incompatibilidad que ya
existe (FR-029).

**Por qué un solo salto para las dos capacidades**: 003 y 004 se entregan juntas, y un archivo de
versión 2 se rechaza igual por cualquiera de las dos. Dos saltos (3 y luego 4) solo agregarían una
versión intermedia que nunca existió en ninguna entrega.

**Contenido de la sección de la línea de tiempo**: las entradas en orden, cada una con número de
acción, instante, tipo y argumento; y los registros de cursor intercalados en su posición. Nada de
puntos de control (R2).

## R9. Conteo de acciones re-aplicadas (SC-004)

**Decisión**: la línea de tiempo cuenta cuántas acciones re-aplicó la última consulta. La prueba
consulta muchos instantes y comprueba que ese conteo nunca supera K. Es un conteo reproducible, no un
tiempo, igual que en 001 R9 y 003 R10.

## R10. Efecto sobre el límite de 20 ms del ciclo de eventos — preliminar, se confirma con `--bench`

**Riesgo**: con la línea de tiempo activa, cada acción del jugador agrega una entrada y, una vez cada
K acciones, toma una copia completa del estado. Esa copia es el trabajo más caro que esta capacidad
mete en el camino de una acción, y el límite de 001 (20 ms por ciclo de eventos con decenas de
cazadores) sigue vigente (FR-031).

**Expectativa**: una copia completa cuesta del orden de lo que cuesta guardar la partida, que en las
mediciones de P1 fue de décimas de milisegundo para la cripta de referencia. Con K ≥ 10 el costo
amortizado por acción es una fracción de eso. Aun así, el pico de la acción que toma el punto de
control es lo que hay que medir, no el promedio.

**Cómo se confirma**: `--bench` repite el escenario `[ciclo_eventos]` de 001 con la línea de tiempo
activa y reporta el máximo, no solo la media (FR-033, SC-006). Si el pico se acercara al límite, la
salida obvia es subir el K por defecto, que es precisamente el parámetro que estas mediciones fijan.
