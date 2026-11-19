# Research: Niebla de guerra y viaje automático «ir a»

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-18

Cada entrada registra la pregunta abierta, las alternativas que se consideraron, la decisión y lo
que la respalda. Las decisiones marcadas como preliminares se confirman con `--bench` y se trasladan
a `DECISIONES.md` §P2 5.3 con las mediciones finales.

## R1. Cómo indexar el estado de conocimiento de una sala — confirmada por el grupo

**Pregunta**: FR-050 exige que consultar si una sala está explorada, avistada o desconocida cueste
tiempo constante, y FR-051 que explorar k salas nuevas cueste proporcional a k y no al tamaño del
mapa conocido. ¿Sobre qué se indexa ese estado?

**Alternativas**:

1. Una tabla hash propia de id de sala a estado (`TablaHash`, ya existe de P1). Constante amortizado,
   pero paga el cálculo del hash y la resolución de colisiones en cada consulta, y las consultas son
   muy frecuentes: una por salida en cada vista y en cada paso de un viaje.
2. Un atributo nuevo en `Sala`. Constante y sin indirección, pero mezcla el conocimiento del jugador
   con el mapa descargado, que es justo la separación que FR-021 exige mantener. Además haría que
   dos partidas sobre la misma cripta cargada compartieran conocimiento.
3. Una lista indexada por `Sala.indice`, el índice compacto 0..n-1 que P1 ya asigna al cargar. Acceso
   constante por posición, sin hash, y el conocimiento vive en su propio objeto, separado de la
   cripta.

**Decisión**: alternativa 3. `Sala.indice` ya existe y `RegistroBusqueda` (001) demostró que el
patrón funciona. El estado de las n salas cabe en una lista de enteros pequeños, se consulta con una
indexación y se crea una sola vez al iniciar la partida.

**Consecuencia sobre FR-051**: crear la lista cuesta O(n) una vez al iniciar la partida, no en cada
exploración. Explorar k salas toca k posiciones más las vecinas de esas k para avistarlas, que son a
lo sumo 4k. El tamaño del mapa ya conocido no interviene.

**Lo que esto no resuelve**: la vista del mapa conocido necesita recorrer las salas exploradas, y
recorrer la lista de n posiciones sería proporcional a la cripta y no al mapa conocido. Ver R3.

## R2. Dónde guardar el estado recordado de cada puerta — confirmada por el grupo

**Pregunta**: FR-004, FR-010 y FR-011 piden recordar, por cada salida de cada sala explorada, si la
puerta se vio abierta, cerrada o nunca se vio. ¿Por puerta o por salida?

**Alternativas**:

1. Por objeto `Puerta`, con un atributo nuevo. Una puerta es compartida por sus dos lados (P1 la
   fusiona en `enlazar_puertas`), así que habría una sola anotación por conexión, lo que coincide
   con FR-008: observar desde cualquiera de los dos extremos es la misma observación. Pero vuelve a
   mezclar conocimiento del jugador con el mapa descargado, igual que R1 alternativa 2.
2. Por par (sala, dirección), en una lista de 4n posiciones indexada por `indice * 4 + direccion`.
   Separa el conocimiento del mapa y da acceso constante, al precio de guardar dos anotaciones por
   conexión, una por cada lado.
3. Por par (sala, dirección) pero escribiendo las dos entradas en cada observación, para que los dos
   lados nunca se contradigan.

**Decisión**: alternativa 3: almacenamiento por par (sala, dirección), y cada observación escribe
las **dos** entradas de la conexión.

**Corrección durante la implementación (§2.6).** La primera versión de esta entrada eligió la
alternativa 2 y afirmaba que no hacía falta escribir los dos lados, porque «lo que la ruta consulta
es siempre la entrada del lado desde el que se mira». Eso es falso, y la prueba de FR-017 lo
descubrió: el jugador está en la sala A, observa la puerta A–B y la recuerda abierta por el lado de
A; si más tarde una ruta de «ir a» pasa por B en dirección a A, la entrada del lado de B seguiría
«sin observar» y la ruta no usaría una puerta que el jugador vio con sus propios ojos. El enunciado
habla del estado recordado de **cada puerta**, no de cada lado, y FR-008 dice que observar desde
cualquiera de las dos salas es la misma observación. La especificación se corrigió primero y el
código después, en confirmaciones separadas.

**Por qué no la alternativa 1**, que sería la representación natural de «una anotación por puerta»:
pondría el conocimiento del jugador como un atributo del objeto `Puerta`, que pertenece al mapa
descargado, y eso es justo la mezcla que FR-021 exige evitar; además dos partidas sobre la misma
cripta cargada compartirían conocimiento. Escribir dos entradas en cada observación cuesta una
asignación más y mantiene la separación.

**Verificación**: el escenario 2 de la User Story 2 comprueba que la puerta se observa desde
cualquiera de sus dos extremos, y la prueba de FR-017 comprueba que una vecina revelada por la
antorcha recuerda la puerta que comparte con el jugador y no las demás.

**Representación**: tres valores (sin observar, recordada abierta, recordada cerrada) caben en un
entero pequeño por posición. Se usa una lista de enteros, no una estructura con hash.

## R3. Cómo recorrer las salas exploradas sin recorrer la cripta — confirmada por el grupo

**Pregunta**: FR-024 pide mostrar las salas exploradas y las avistadas. Recorrer las n posiciones de
la lista de R1 es proporcional a la cripta, no al mapa conocido, y contradice el espíritu de FR-051.

**Alternativas**:

1. Recorrer las n posiciones y filtrar. Simple, pero paga el tamaño de la cripta en cada vista.
2. Mantener una lista de ids de salas exploradas en el orden en que se exploraron, además de la lista
   de estados. Agregar es O(1) al final, revertir es O(1) por sala quitando del final, y recorrer es
   proporcional al mapa conocido.
3. Una lista doblemente enlazada propia (`ListaDoble`, ya existe de P1). Permite quitar de cualquier
   posición en O(1), pero no hace falta: las reversiones siempre deshacen las exploraciones más
   recientes, que están al final.

**Decisión**: alternativa 2. La reversión de una acción deshace sus cambios en orden inverso
(P1 §4.6), así que las salas que una exploración agregó al final son exactamente las que su
reversión quita del final. Una lista simple basta y es la estructura más barata que cumple.

**Las avistadas** no se guardan en una lista aparte: se derivan recorriendo las salidas de las salas
exploradas, que es proporcional al mapa conocido y no a la cripta.

## R4. Si `ir a` comparte la búsqueda con el cazador (P2 §5.3) — decidida con argumento, confirmada con `--bench`

**Pregunta**: el enunciado pide justificar explícitamente si la ruta de `ir a` comparte
implementación con la búsqueda del cazador o si conviene separarlas. Ambas son búsquedas de costo
mínimo con el mismo desempate por menor id del primer paso (001 FR-014 y 003 FR-032).

**Alternativas**:

1. Una sola clase con un criterio de transitabilidad configurable (una función o un parámetro que
   decida si una salida se puede usar). Elimina la duplicación del algoritmo.
2. Dos buscadores separados, cada uno con su propio recorrido, compartiendo las estructuras
   auxiliares (`MonticuloMin` y `RegistroBusqueda`).
3. Dos buscadores completamente independientes, cada uno con sus propias estructuras auxiliares.

**Decisión**: alternativa 2. El algoritmo se repite, pero el filtro no es el mismo tipo de cosa en
los dos casos y meterlo en una sola clase tiene dos costos concretos:

- **Rendimiento del cazador**: el bucle interno del cazador se ejecuta decenas de veces por ciclo de
  eventos y su límite es 20 ms (001 FR-031). Añadirle una llamada indirecta por cada salida
  examinada es trabajo que se paga en el camino crítico de la capacidad con el límite más ajustado,
  para beneficio de un comando que se ejecuta una vez por orden del jugador y tiene 5 ms por paso.
- **Conocimiento distinto**: el cazador mira el estado real de las puertas y no mira el estado de
  conocimiento de las salas; `ir a` mira exactamente lo contrario y nunca el estado real (FR-021,
  FR-023). Un parámetro que conmute entre las dos fuentes de verdad en la misma clase vuelve fácil
  escribir por accidente un cazador que respeta la niebla de guerra o un `ir a` que la atraviesa, que
  son los dos defectos más graves que esta capacidad puede introducir. Separarlos hace que ese error
  no se pueda escribir.

**Lo que sí se comparte**: `MonticuloMin` y `RegistroBusqueda`, que son las estructuras propias del
Principio I y donde está el trabajo real de implementación. El recorrido en sí son unas veinte líneas.

**Lo que se mide**: `--bench` reporta el costo de un paso de `ir a` y el del cazador en la misma
cripta sintética, para poder afirmar con datos que separarlos no degradó ninguno de los dos.

## R5. Reconstruir la ruta completa o solo el primer paso — confirmada por el grupo

**Pregunta**: FR-035 obliga a recalcular la ruta antes de cada paso. ¿Conviene calcular la ruta
completa una vez y rehacerla solo cuando el conocimiento cambie?

**Alternativas**:

1. Calcular la ruta completa al empezar el viaje y seguirla, recalculando solo si al observar las
   puertas de la sala de llegada cambió algo. Ahorra cálculos cuando nada cambia.
2. Calcular solo el primer paso antes de cada paso, siempre. Más cálculos, pero cada paso es por
   definición el primero de una ruta recalculada, que es literalmente lo que FR-035 pide.

**Decisión**: alternativa 2, reutilizando `primer_paso_desde` de la capacidad 001, que ya devuelve
la vecina correcta según el desempate. El viaje da unos pocos pasos y cada cálculo tiene 5 ms de
presupuesto; la alternativa 1 ahorra tiempo que no hace falta ahorrar e introduce exactamente la
clase de invalidación que la capacidad 001 ya demostró ser la parte más difícil de verificar
(001 §5.2). Aquí no hay límite de 20 ms que lo justifique.

**Consecuencia**: no hay estado de ruta que invalidar, así que no hay forma de que el viaje siga una
ruta obsoleta. El único estado del viaje es el destino y el motivo de detención.

## R6. Qué cuenta como «recibir daño» para detener el viaje — confirmada por el grupo

**Pregunta**: FR-038 detiene el viaje cuando el jugador recibe daño. El daño puede venir de una
trampa al entrar, del ataque de un enemigo durante los eventos del reloj entre dos pasos, o de un
pulso de veneno.

**Decisión**: cualquier reducción de la vida del jugador durante el viaje lo detiene, sin importar
la causa. P1 ya concentra todo el daño al jugador en un único punto (`_danar_jugador`), así que la
condición se observa comparando la vida del jugador antes y después de cada paso, y no hay que
enumerar causas ni tocar cada una.

**Por qué comparar y no observar el punto de daño**: comparar la vida antes y después del paso
captura también el daño que ocurre dentro de los eventos del reloj que se despachan al cerrar la
acción, que es donde atacan los enemigos. Un enganche en el punto de daño tendría que distinguir si
el viaje está en curso, lo que acopla el modelo de daño al comando.

**Lo que no detiene el viaje**: la curación, el veneno que termina sin dañar en ese paso y los
cambios de velocidad.

## R7. Dónde vive el bucle del viaje — confirmada por el grupo

**Pregunta**: el viaje ejecuta varias acciones del jugador seguidas. ¿Es una acción del modelo, un
bucle del controlador o algo intermedio?

**Alternativas**:

1. Una acción nueva del modelo (`Partida.ejecutar` con un tipo `IR_A`) que internamente dé todos los
   pasos. Contradice FR-034 y FR-045: cada paso debe ser una acción completa y el pergamino debe
   revertir solo el último.
2. Un bucle en el controlador que traduzca la orden a movimientos y los ejecute uno por uno.
   Respeta que cada paso sea una acción, pero pone en el controlador el cálculo de la ruta, que es
   regla del juego, y lo deja fuera de las pruebas del modelo.
3. Un servicio del modelo que calcule el siguiente paso y evalúe las condiciones de parada, y un
   bucle delgado que pida pasos y los ejecute como acciones de movimiento ordinarias.

**Decisión**: alternativa 3. El cálculo de la ruta, el motivo de detención y las condiciones de
parada son reglas del juego y viven en el modelo, con pruebas propias que no necesitan vista ni
controlador. La ejecución de cada paso es la acción de mover que ya existe, sin ningún camino
alternativo que pudiera comportarse distinto de un movimiento manual.

**Consecuencia sobre la bitácora**: el bucle ejecuta acciones de mover, así que la bitácora las graba
como movimientos individuales sin ningún trabajo extra (FR-043). El comentario de la orden se graba
aparte, con un tipo que la lectura de bitácoras ignora (FR-044).

## R8. Cómo se revierte una exploración grande — confirmada por el grupo

**Pregunta**: FR-048 y el caso del Apéndice B «un pergamino revierte una entrada con antorcha
encendida» piden deshacer la exploración de varias salas a la vez. ¿Qué información mínima hay que
registrar?

**Decisión**: por cada sala que cambió de estado, su estado anterior; por cada puerta que cambió de
estado recordado, su valor anterior; y la cantidad de salas que se agregaron a la lista de
exploradas. P1 §4.6 ya ofrece el mecanismo: cada cambio registra su propia función de deshacer en el
intervalo de la acción en curso, y el pergamino las ejecuta en orden inverso. El mapa conocido se
engancha ahí y no necesita su propio historial.

**Costo**: proporcional a lo que cambió (FR-052). Una entrada con antorcha que no revela nada no
registra nada.

**Lo que no se registra**: el estado de las salas que no cambiaron. Marcar como avistada una sala ya
avistada o ya explorada no es un cambio y no deja rastro de reversión.

## R9. Formato de guardado — confirmada por el grupo

**Pregunta**: FR-046 obliga a persistir el mapa conocido, incluidas salas avistadas y salas
exploradas por antorcha cuyo contenido nunca se incorporó. El guardado de P1 solo recorre las salas
con contenido incorporado.

**Decisión**: el mapa conocido se guarda como una sección propia del encabezado del archivo, con una
entrada por sala conocida: su id, su estado y los estados recordados de sus cuatro puertas. No se
cuelga de la sección de salas, porque esa sección solo existe para las salas con contenido y el
conocimiento abarca más salas que esa.

**Versión del formato**: sube a 3. Los archivos de la primera parte (versión 1) y los de las
capacidades 001 y 002 (versión 2) se rechazan con el mensaje de incompatibilidad que ya existe
(FR-047), sin borrar archivos a mano.

**Lo que no se guarda**: nada del viaje. Un viaje no es estado persistente (R5), así que no hay
viajes a medio terminar que reanudar al cargar.

## R10. Conteo del trabajo de una exploración (SC-004)

**Pregunta**: ¿cómo se comprueba que explorar salas nuevas no se vuelve más caro a medida que el
mapa conocido crece, sin depender de los tiempos del equipo?

**Decisión**: el mapa conocido cuenta cuántas posiciones de sala y cuántas posiciones de puerta tocó
en la última exploración. La prueba revela k vecinas con antorcha en una cripta sintética pequeña y
en otra 10 veces más grande con la misma vecindad local, y compara los dos conteos, que deben ser
iguales. Los tiempos se reportan en `--bench` como evidencia complementaria, no como criterio.

**Precedente**: es el mismo método que la capacidad 001 usó para el rango del cazador (001 R9,
SC-004), y por la misma razón: un conteo es reproducible y un tiempo depende de la máquina.
