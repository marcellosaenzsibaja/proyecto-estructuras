# Feature Specification: Niebla de guerra y viaje automático «ir a»

**Feature Branch**: `003-niebla-guerra`

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "Niebla de guerra y viaje automático (P2 §3.3, §3.4, §5.3, §6.1, §6.3 y Apéndice B «Niebla de guerra e ir a»). El jugador deja de ver el mapa completo: cada sala está explorada (entró al menos una vez; la inicial desde el instante 0), avistada (no explorada pero destino de una salida de una sala explorada) o desconocida. De una sala explorada conoce nombre, salidas, costo de cada salida y el estado de sus puertas según la última observación; de una avistada solo que existe una sala detrás de esa salida; de una desconocida nada. El jugador observa una puerta cuando está en cualquiera de las dos salas que conecta, y el mapa recuerda el estado de esa última observación aunque después cambie. La antorcha de P1 §2.7 adquiere efecto: mientras esté encendida, al entrar a una sala también quedan exploradas todas sus vecinas a través de cualquier salida, abierta o cerrada, revelando nombre y salidas pero no contenido, y sin activar sus enemigos ni sus trampas. El programa sigue descargando el esqueleto completo y la precarga puede usarlo libremente porque es infraestructura, pero todo lo que la vista muestra y lo que usa «ir a» debe derivarse exclusivamente del conocimiento del jugador. El conocimiento es estado del juego: se guarda en el archivo de partida, se revierte con el pergamino de retroceso y forma parte de la línea de tiempo. La interfaz debe ofrecer un comando para ver el mapa conocido. El comando `ir a <sala>` lleva al jugador a una sala explorada mediante movimientos ordinarios: la ruta se calcula con el conocimiento del jugador, solo salas exploradas y solo salidas que el mapa recuerda abiertas, minimizando la suma de costos y desempatando como el cazador por la vecina de menor id; cada paso es una acción del jugador completa que consume tiempo y entre paso y paso ocurren normalmente los eventos del reloj; la ruta se recalcula antes de cada paso con el conocimiento vigente; el viaje se detiene cuando el jugador llega al destino, entra a una sala que contiene enemigos activos o dormidos, recibe daño o deja de existir una ruta conocida; no abre puertas aunque tenga la llave; en partida.log cada paso se registra como un movimiento individual y la orden se registra además como comentario; el pergamino revierte únicamente el último paso. Consultar el estado de una sala y el estado recordado de una puerta son operaciones frecuentes; explorar salas nuevas debe costar proporcionalmente a las salas reveladas y no al tamaño del mapa conocido; el diseño debe hacer barato registrar e invertir cambios. El cálculo de un paso de «ir a» debe tomar menos de 5 ms con el mapa conocido completo de la cripta de referencia, y `--bench` debe medir las consultas al mapa conocido y el cálculo de «ir a» con criptas sintéticas deterministas por semilla."

## Contexto y alcance

Esta capacidad amplía las reglas de la primera parte (P1 §2.3, §2.4, §2.7 y §2.11) y se apoya en el
terreno con costo de la capacidad 001. Todo lo que no se modifica aquí sigue igual: costos de las
acciones, activación de enemigos, combate, trampas, efectos, puntajes y reproducción.

**Dentro del alcance**: los tres estados de conocimiento de una sala; la memoria del estado de las
puertas; el efecto de la antorcha sobre la exploración; la separación entre el mapa descargado y el
conocimiento del jugador; el comando para ver el mapa conocido; el comando `ir a`; la reversión del
conocimiento con el pergamino; su persistencia; y las mediciones de `--bench` asociadas.

**Fuera del alcance** (tienen su propia especificación): terreno y cazador (001), verificación de
resolubilidad (002) y línea de tiempo con puntos de control (004). Esta especificación declara que
el conocimiento del jugador es estado del juego y por tanto reconstruible en la línea de tiempo,
pero la línea de tiempo misma, sus consultas y sus puntos de control pertenecen a la 004.

## Identificadores

Los requisitos de esta especificación se numeran `FR-NNN` dentro de ella, como en las capacidades
001 y 002. Cuando se citan desde fuera de este archivo (pruebas, `DECISIONES.md`, `tasks.md`) se
escriben calificados por la capacidad, `003-FR-012`, porque la numeración reinicia en cada
especificación y el mismo `FR-012` existe en las tres.

## Clarifications

### Session 2026-11-18

- Q: ¿Cómo nombra el jugador la sala destino en `ir a <sala>`?
  → A: Por su id numérico, o por su nombre si ese nombre identifica a una sola sala explorada. Un
  nombre que coincida con dos o más salas exploradas se rechaza pidiendo el id, sin consumir tiempo.
- Q: Una sala explorada por la antorcha nunca fue visitada: ¿tiene contenido, enemigos y trampas?
  → A: Sí. La antorcha revela nombre y salidas, no contenido: sus enemigos siguen dormidos y sus
  trampas armadas. Cuando el jugador entra físicamente, se incorpora el contenido y se activan
  enemigos y trampas como en cualquier primera entrada (P1 §2.4). Por eso un `ir a` que atraviesa
  una sala explorada solo por antorcha puede detenerse en ella.
- Q: ¿Qué recuerda el mapa de las puertas de una sala explorada por la antorcha?
  → A: Solo las que comparte con la sala donde está el jugador, porque son las únicas que observa.
  Las demás salidas de esa vecina se conocen con su costo, pero su puerta queda sin observar, y una
  puerta sin observar no se considera abierta para `ir a`.
- Q: ¿Qué hace `ir a` si el destino es la sala actual, o si no existe ruta conocida antes del primer
  paso? → A: Se rechaza con un mensaje y no consume tiempo virtual, igual que un destino no
  explorado. Un viaje solo empieza si va a dar al menos un paso.
- Q: Al reproducir con `--replay`, ¿qué se ejecuta de un `ir a`?
  → A: Los movimientos individuales que quedaron grabados. La orden `ir a` se graba como comentario
  de depuración y la reproducción la ignora, de modo que una reproducción no recalcula rutas y no
  depende de que el conocimiento del jugador se reconstruya antes de cada paso.
- Q: ¿Cómo se comprueba que explorar salas nuevas no se vuelve más caro a medida que el mapa
  conocido crece? → A: Por conteo: una exploración solo toca las salas que revela y sus vecinas
  inmediatas, y ese número no cambia si el mapa ya conocido es 10 veces más grande; `--bench`
  reporta además los tiempos.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El jugador solo conoce lo que ha explorado (Priority: P1)

Como jugador, no veo la cripta completa: veo las salas donde he estado, con sus salidas y sus
costos, y sé que detrás de algunas salidas hay una sala más, sin saber cuál. Lo demás no existe
para mí hasta que lo descubro.

**Why this priority**: es la base de la capacidad. La vista, el mapa conocido y `ir a` dependen de
que exista un conocimiento del jugador distinto del mapa descargado.

**Independent Test**: cargar una cripta sintética, recorrer un camino conocido y comprobar, sala por
sala, el estado de cada una (explorada, avistada, desconocida) y lo que el mapa expone de cada
estado.

**Acceptance Scenarios**:

1. **Given** una partida recién iniciada, **When** se consulta el mapa conocido, **Then** la sala
   inicial está explorada y las salas destino de sus salidas están avistadas.
2. **Given** una sala avistada, **When** se consulta el mapa conocido, **Then** se sabe que existe
   una sala detrás de esa salida, y no se expone su nombre, ni sus salidas, ni sus costos.
3. **Given** una sala desconocida, **When** se consulta el mapa conocido, **Then** el mapa no
   expone nada de ella, ni siquiera que exista.
4. **Given** el jugador en la sala inicial, **When** se mueve a una sala avistada, **Then** esa sala
   queda explorada, y las salas destino de sus salidas que no estuvieran exploradas quedan
   avistadas.
5. **Given** una sala explorada, **When** el jugador la abandona y vuelve más tarde, **Then** sigue
   explorada y su nombre, salidas y costos siguen disponibles.
6. **Given** una sala explorada con una salida hacia otra sala explorada, **When** se consulta el
   mapa, **Then** esa vecina sigue explorada: ser destino de una salida no degrada su estado.

---

### User Story 2 - El mapa recuerda las puertas como se vieron (Priority: P1)

Como jugador, mi mapa anota el estado de cada puerta tal como la vi la última vez. Si una puerta se
cerró sola cuando yo ya estaba lejos, mi mapa sigue diciendo que está abierta hasta que vuelvo a
verla.

**Why this priority**: es la regla que hace del conocimiento algo distinto de una copia del estado
real, y la que obliga a `ir a` a recalcular la ruta y a poder equivocarse.

**Independent Test**: abrir una puerta, alejarse, provocar su cierre automático y comprobar que el
mapa la sigue recordando abierta; volver a la sala y comprobar que el mapa se corrige.

**Acceptance Scenarios**:

1. **Given** el jugador en una sala, **When** llega a ella, **Then** el mapa recuerda el estado
   real de todas las puertas de esa sala en ese instante.
2. **Given** una puerta entre las salas A y B, **When** el jugador está en B, **Then** también
   observa esa puerta: se observa desde cualquiera de sus dos extremos.
3. **Given** una puerta que el jugador recuerda abierta, **When** se cierra automáticamente estando
   el jugador en otra sala, **Then** el mapa la sigue recordando abierta.
4. **Given** la situación anterior, **When** el jugador entra a una de las dos salas que conecta,
   **Then** el mapa pasa a recordarla cerrada.
5. **Given** una puerta de una sala nunca visitada, **When** se consulta el mapa, **Then** su
   estado recordado es «sin observar», que no equivale a abierta.
6. **Given** el jugador que abre una puerta cerrada con su llave, **When** la abre, **Then** el
   mapa la recuerda abierta desde ese instante.

---

### User Story 3 - La antorcha ilumina los alrededores (Priority: P2)

Como jugador, si llevo una antorcha encendida, al entrar a una sala alcanzo a ver también las salas
contiguas: sé cómo se llaman y qué salidas tienen, pero no qué hay dentro, y no despierto nada.

**Why this priority**: da utilidad real a un objeto que en la primera parte no tenía efecto, y es la
fuente de las reversiones más grandes del mapa, que la 004 tendrá que reconstruir.

**Independent Test**: encender una antorcha, entrar a una sala con varias vecinas y comprobar que
todas quedan exploradas con nombre y salidas, que sus enemigos siguen dormidos, que sus trampas
siguen armadas y que el jugador no recibió daño.

**Acceptance Scenarios**:

1. **Given** una antorcha encendida, **When** el jugador entra a una sala, **Then** todas las salas
   destino de las salidas de esa sala quedan exploradas, por salidas abiertas y cerradas por igual
   (Apéndice B).
2. **Given** el escenario anterior, **When** se consulta una vecina recién explorada por la
   antorcha, **Then** se conocen su nombre, sus salidas y el costo de cada una, y no su contenido.
3. **Given** una vecina con enemigos dormidos y trampas armadas, **When** la antorcha la explora,
   **Then** sus enemigos siguen dormidos, sus trampas siguen armadas y el jugador no recibe daño
   (Apéndice B).
4. **Given** una vecina explorada por la antorcha, **When** el jugador entra físicamente a ella más
   tarde, **Then** se incorpora su contenido y se activan sus enemigos y sus trampas según P1 §2.4.
5. **Given** una antorcha apagada, **When** el jugador entra a una sala, **Then** sus vecinas quedan
   avistadas, no exploradas.
6. **Given** la antorcha que se apaga por fin de su duración, **When** se apaga, **Then** el mapa
   conocido no cambia por ese hecho: lo ya explorado sigue explorado.
7. **Given** una vecina explorada por la antorcha cuyas otras salidas llevan a salas desconocidas,
   **When** se consulta el mapa, **Then** esas salas quedan avistadas.

---

### User Story 4 - Viajar a una sala conocida sin repetir cada paso (Priority: P1)

Como jugador, cuando quiero volver a una sala donde ya estuve, doy una sola orden y el personaje
camina hasta allá por el camino más barato que yo conozco, deteniéndose si algo se interpone.

**Why this priority**: es el comando nuevo de la capacidad y el consumidor principal del mapa
conocido; su corrección depende de que el conocimiento sea la única fuente de la ruta.

**Independent Test**: en una cripta sintética con costos distintos, explorar un circuito, ordenar
`ir a` hacia el extremo y comprobar la secuencia exacta de salas visitadas, el reloj resultante y
el motivo de detención.

**Acceptance Scenarios**:

1. **Given** una sala explorada distinta de la actual con ruta conocida, **When** el jugador ordena
   `ir a` esa sala, **Then** llega a ella mediante movimientos ordinarios y el viaje termina por
   llegada al destino.
2. **Given** una sala avistada o desconocida, **When** el jugador ordena `ir a` esa sala, **Then**
   la orden se rechaza, no consume tiempo virtual y el reloj no avanza (Apéndice B).
3. **Given** dos rutas conocidas hacia el destino, una de 2 salidas con costo total 500 y otra de 4
   salidas con costo total 400, **When** el jugador ordena el viaje, **Then** sigue la de costo 400.
4. **Given** dos vecinas v1 y v2 (id de v1 < id de v2) que inician rutas conocidas de costo mínimo,
   **When** se calcula el primer paso, **Then** el jugador se mueve a v1.
5. **Given** un viaje de tres pasos, **When** se ejecuta, **Then** cada paso consume tiempo según
   el costo de su salida y entre paso y paso se despachan normalmente los eventos del reloj
   (venenos, turnos de enemigos, cierres automáticos).
6. **Given** una ruta cuyo siguiente tramo el mapa recuerda abierto pero está cerrado en realidad,
   **When** el jugador llega a la sala desde la que se observa esa puerta, **Then** el mapa se
   corrige, la ruta se recalcula evitándola y el viaje sigue por la nueva ruta si existe
   (Apéndice B).
7. **Given** la situación anterior sin ninguna ruta conocida alternativa, **When** se recalcula,
   **Then** el viaje se detiene sin consumir tiempo adicional y se informa el motivo (Apéndice B).
8. **Given** una ruta conocida que atraviesa una puerta que el mapa recuerda cerrada, **When** se
   calcula la ruta, **Then** esa puerta no se usa aunque el jugador tenga su llave: `ir a` no abre
   puertas.
9. **Given** el destino igual a la sala actual, **When** el jugador ordena el viaje, **Then** se
   rechaza y no consume tiempo.
10. **Given** un nombre de sala que coincide con dos salas exploradas, **When** el jugador lo usa
    como destino, **Then** se rechaza pidiendo el id y no consume tiempo.

---

### User Story 5 - El viaje se detiene cuando algo cambia (Priority: P1)

Como jugador, confío en que el viaje automático no me lleve a ciegas hacia el peligro: si aparece un
enemigo, si me hieren o si el camino deja de existir, el personaje se detiene y me devuelve el
control.

**Why this priority**: sin estas paradas, el comando convierte varias decisiones del jugador en una
sola y rompe el equilibrio del juego.

**Independent Test**: preparar criptas sintéticas donde cada condición de parada ocurre en un paso
intermedio conocido, y comprobar en qué sala se detuvo el viaje, cuánto tiempo consumió y qué motivo
se informó.

**Acceptance Scenarios**:

1. **Given** un viaje en curso, **When** el jugador entra a una sala que contiene enemigos activos,
   **Then** el viaje se detiene en esa sala.
2. **Given** un viaje en curso, **When** el jugador entra a una sala con enemigos dormidos, **Then**
   esos enemigos se activan según P1 §2.4 y el viaje se detiene en esa sala (Apéndice B).
3. **Given** un viaje en curso, **When** el jugador recibe daño por cualquier causa (trampa, ataque
   de un enemigo o veneno), **Then** el viaje se detiene.
4. **Given** un viaje en curso, **When** el jugador muere o gana durante un paso, **Then** el viaje
   se detiene y la partida termina.
5. **Given** un viaje detenido por cualquier motivo, **When** termina, **Then** la interfaz informa
   por qué se detuvo.
6. **Given** un viaje detenido por un enemigo, **When** el jugador vuelve a ordenar el mismo `ir a`,
   **Then** el viaje se recalcula desde cero con el conocimiento vigente.

---

### User Story 6 - El conocimiento es parte de la partida (Priority: P2)

Como jugador, mi mapa es tan parte de mi partida como mi vida o mi inventario: se guarda con ella,
y si uso un pergamino de retroceso vuelve a estar como estaba.

**Why this priority**: es lo que permite que la 004 reconstruya el mapa en cualquier instante, y lo
que obliga a que registrar e invertir cambios del mapa sea barato.

**Independent Test**: provocar una exploración grande con antorcha, usar un pergamino y comprobar
que todas las salas reveladas por esa entrada volvieron a su estado anterior; guardar, cargar y
comparar el mapa completo.

**Acceptance Scenarios**:

1. **Given** una entrada a una sala con antorcha encendida que exploró cinco vecinas, **When** el
   jugador usa un pergamino de retroceso, **Then** esas cinco salas vuelven a su estado anterior y
   la sala abandonada vuelve a ser la actual (Apéndice B).
2. **Given** un viaje de varios pasos ya terminado, **When** el jugador usa un pergamino, **Then**
   se revierte únicamente el último paso y el viaje no continúa (Apéndice B).
3. **Given** una puerta cuyo estado recordado cambió al observarla, **When** se revierte esa acción,
   **Then** el estado recordado vuelve a ser el anterior a la observación.
4. **Given** una partida con un mapa conocido parcial, **When** se guarda y se vuelve a cargar,
   **Then** el mapa conocido es idéntico: los mismos estados de sala y los mismos estados
   recordados de puertas.
5. **Given** un archivo de partida de la primera parte, **When** se intenta cargar, **Then** se
   reporta la incompatibilidad de formato y no se carga en silencio.
6. **Given** la misma cripta, la misma semilla y la misma secuencia de acciones, **When** se juega
   dos veces, **Then** el mapa conocido resultante es idéntico, también al reproducir con
   `--replay`.

---

### User Story 7 - Las operaciones del mapa son baratas (Priority: P2)

Como grupo de desarrollo, necesitamos que consultar y actualizar el mapa conocido no sea el cuello
de botella: se consulta en cada vista, en cada paso de un viaje y en cada entrada con antorcha.

**Why this priority**: es el problema de estructuras de datos de la capacidad (P2 §5.3) y lo que se
evalúa con mediciones.

**Independent Test**: ejecutar `--bench` con criptas sintéticas deterministas y comparar los
tiempos y los conteos declarados con los límites de P2 §6.1.

**Acceptance Scenarios**:

1. **Given** un mapa conocido de cualquier tamaño, **When** se consulta el estado de una sala o el
   estado recordado de una puerta, **Then** el costo de la consulta no depende de cuántas salas haya
   exploradas.
2. **Given** un mapa conocido ya grande, **When** una entrada con antorcha revela k salas nuevas,
   **Then** el trabajo de esa exploración depende de k y de sus vecinas inmediatas, no del tamaño
   del mapa ya conocido.
3. **Given** el mapa conocido completo de la cripta de referencia, **When** se calcula un paso de
   `ir a`, **Then** tarda menos de 5 ms en el equipo local, sin red ni renderizado.
4. **Given** `--bench`, **When** se ejecuta dos veces con la misma semilla, **Then** genera las
   mismas criptas sintéticas y no instancia la vista.

---

### Edge Cases

- Dos salidas distintas de una sala llevan a la misma vecina: el conocimiento es por sala, así que
  la vecina tiene un solo estado; para la ruta cuenta la salida que el mapa recuerda abierta de
  menor costo, y si empatan, la primera en el orden N, S, E, O.
- Una salida lleva a la propia sala: no cambia nada; una sala explorada no se avista a sí misma.
- El destino de `ir a` queda explorado pero aislado en el mapa conocido porque todas las puertas
  que llevan a él se recuerdan cerradas: no hay ruta conocida y la orden se rechaza.
- El jugador ordena `ir a` hacia una sala explorada solo por la antorcha: es un destino válido; el
  viaje puede detenerse al entrar si allí hay enemigos dormidos o trampas armadas.
- La antorcha se enciende estando el jugador en una sala: no explora las vecinas en ese instante;
  el efecto ocurre al entrar a una sala.
- La antorcha está encendida y el jugador entra a una sala cuyas vecinas ya estaban exploradas: no
  hay nada que revelar y la entrada no registra cambios del mapa.
- Un viaje con destino alcanzado en el primer paso: es un viaje de un paso, con su parada por
  llegada.
- El jugador recibe daño en el mismo instante en que llega al destino: el viaje terminó por llegada.
- Una puerta se abre en la realidad mientras el jugador está lejos: el mapa la sigue recordando
  cerrada y la ruta no la usa, aunque pasar por ahí fuera posible. El conocimiento puede ser peor
  que la realidad, no solo mejor.
- El jugador usa un pergamino que revierte la entrada que descubrió el destino del viaje: después
  de revertir, ese destino puede haber dejado de estar explorado.
- Se carga una partida guardada en medio de nada: el viaje no es estado persistente, no hay viajes
  a medio terminar que reanudar.
- Una sala explorada sin ninguna salida conocida abierta: aparece en el mapa conocido con sus
  salidas y sus estados recordados; simplemente no es alcanzable por `ir a`.

## Requirements *(mandatory)*

### Functional Requirements

**Estados de conocimiento de una sala**

- **FR-001**: Para el jugador, cada sala de la cripta DEBE estar en exactamente uno de tres
  estados: explorada, avistada o desconocida.
- **FR-002**: La sala inicial DEBE estar explorada desde el instante 0.
- **FR-003**: Entrar a una sala DEBE dejarla explorada, y una sala explorada NO DEBE volver a otro
  estado salvo por una reversión del estado del juego (pergamino o línea de tiempo).
- **FR-004**: De una sala explorada el jugador DEBE conocer su nombre, sus salidas, el costo de cada
  salida y el estado de cada una de sus puertas según la última observación.
- **FR-005**: Una sala no explorada que es destino de una salida de una sala explorada DEBE estar
  avistada. De una sala avistada el jugador solo DEBE conocer que existe una sala detrás de esa
  salida: NO DEBE conocer su nombre, ni sus salidas, ni sus costos, ni su contenido.
- **FR-006**: Una sala que no es explorada ni avistada DEBE estar desconocida, y el conocimiento del
  jugador NO DEBE exponer nada de ella.
- **FR-007**: Explorar una sala DEBE dejar avistadas las salas destino de sus salidas que no
  estuvieran ya exploradas, por salidas abiertas y cerradas por igual.

**Memoria del estado de las puertas**

- **FR-008**: El jugador DEBE observar una puerta cuando está en cualquiera de las dos salas que
  conecta.
- **FR-009**: Observar una puerta DEBE fijar su estado recordado al estado real de esa puerta en
  ese instante.
- **FR-010**: El mapa del jugador DEBE conservar el estado recordado de cada puerta tal como estaba
  en su última observación, aunque el estado real haya cambiado después.
- **FR-011**: Una puerta que el jugador nunca ha observado DEBE quedar como «sin observar». «Sin
  observar» NO DEBE tratarse como abierta por ninguna regla derivada del conocimiento.
- **FR-012**: Al entrar a una sala, las puertas de esa sala DEBEN observarse antes de cualquier
  decisión derivada del conocimiento, incluido el recálculo de la ruta de un viaje en curso.
- **FR-013**: Abrir una puerta con una llave DEBE dejarla recordada abierta, por ser una
  observación directa del jugador.

**Antorcha**

- **FR-014**: Mientras la antorcha del jugador esté encendida, entrar a una sala DEBE dejar
  exploradas todas las salas destino de las salidas de esa sala, a través de cualquier salida,
  abierta o cerrada.
- **FR-015**: Explorar una vecina por la antorcha DEBE revelar su nombre, sus salidas y el costo de
  cada una, y NO DEBE revelar su contenido.
- **FR-016**: Explorar una vecina por la antorcha NO DEBE activar sus enemigos ni sus trampas, ni
  causar daño al jugador, ni incorporar su contenido.
- **FR-017**: Explorar una vecina por la antorcha NO DEBE observar las puertas de esa vecina que no
  comparta con la sala donde está el jugador.
- **FR-018**: Entrar físicamente a una sala explorada antes por la antorcha DEBE incorporar su
  contenido y activar sus enemigos y sus trampas según P1 §2.4, como cualquier primera entrada.
- **FR-019**: Encender o apagar la antorcha NO DEBE cambiar por sí mismo el mapa conocido; su
  único efecto sobre el conocimiento ocurre al entrar a una sala.

**Separación entre el mapa descargado y el conocimiento**

- **FR-020**: El programa DEBE seguir descargando el esqueleto completo, y la estrategia de precarga
  de P1 §4.2 PUEDE usarlo libremente: es infraestructura, no conocimiento del jugador.
- **FR-021**: Todo lo que la vista muestre del mapa y todo lo que use `ir a` DEBE derivarse
  exclusivamente del conocimiento del jugador, nunca del esqueleto descargado ni del estado real de
  las puertas.
- **FR-022**: El conocimiento del jugador DEBE ser estado del juego: se guarda en el archivo de
  partida, se revierte con el pergamino de retroceso y forma parte de la línea de tiempo.
- **FR-023**: El conocimiento del jugador NO DEBE influir en las decisiones de los enemigos. En
  particular, el cazador sigue decidiendo con el esqueleto completo y el estado real de las puertas
  (001, FR-017).

**Vista del mapa conocido**

- **FR-024**: La interfaz DEBE ofrecer un comando para ver el mapa conocido, que muestre las salas
  exploradas con sus salidas y las salas avistadas.
- **FR-025**: La vista del mapa DEBE mostrar el estado recordado de cada puerta, no su estado real,
  y DEBE distinguir «sin observar» de «abierta» y de «cerrada».
- **FR-026**: Ver el mapa conocido NO DEBE consumir tiempo virtual, NO DEBE registrarse como acción
  en `partida.log` y NO DEBE alterar ningún estado del juego ni el historial de retroceso.

**Viaje automático «ir a»**

- **FR-027**: La interfaz DEBE ofrecer el comando `ir a <sala>`, que lleva al jugador a una sala
  explorada mediante una secuencia de movimientos ordinarios.
- **FR-028**: El destino DEBE poder indicarse por el id de la sala, o por su nombre si ese nombre
  identifica a una sola sala explorada.
- **FR-029**: Un destino que no esté explorado, un destino igual a la sala actual, un nombre
  ambiguo entre salas exploradas o un destino sin ruta conocida DEBEN rechazarse con un mensaje, sin
  consumir tiempo virtual y sin registrarse como acción.
- **FR-030**: La ruta DEBE calcularse únicamente sobre salas exploradas y únicamente a través de
  salidas que el mapa del jugador recuerde abiertas.
- **FR-031**: La ruta DEBE minimizar la suma de los costos de las salidas recorridas.
- **FR-032**: Desempate: entre las vecinas que inician una ruta conocida de costo mínimo, el primer
  paso DEBE ser hacia la de menor id, igual que el cazador (001, FR-014).
- **FR-033**: Si varias salidas recordadas abiertas llevan a la misma vecina, el costo que cuenta
  DEBE ser el menor de ellas, y el paso DEBE atravesar esa salida; si dos empatan en costo, la
  primera según el orden fijo N, S, E, O.
- **FR-034**: Cada paso del viaje DEBE ser una acción del jugador completa: consume tiempo según el
  costo de su salida (001, FR-003) y entre paso y paso DEBEN despacharse normalmente los eventos
  del reloj.
- **FR-035**: La ruta DEBE recalcularse antes de cada paso con el conocimiento vigente en ese
  instante.
- **FR-036**: El viaje DEBE detenerse cuando el jugador llega al destino.
- **FR-037**: El viaje DEBE detenerse cuando el jugador entra a una sala que contiene enemigos,
  activos o dormidos. Los enemigos dormidos de esa sala se activan según P1 §2.4 antes de la parada.
- **FR-038**: El viaje DEBE detenerse cuando el jugador recibe daño por cualquier causa.
- **FR-039**: El viaje DEBE detenerse cuando deja de existir una ruta conocida hacia el destino, sin
  consumir tiempo virtual adicional por ese hecho.
- **FR-040**: El viaje DEBE detenerse cuando la partida termina en victoria o derrota.
- **FR-041**: `ir a` NO DEBE abrir puertas, aunque el jugador tenga la llave correspondiente.
- **FR-042**: Al terminar, el viaje DEBE informar por qué se detuvo.
- **FR-043**: En `partida.log`, cada paso del viaje DEBE registrarse como un movimiento individual.
  La orden `ir a` DEBE registrarse además como comentario para fines de depuración.
- **FR-044**: El comentario de la orden `ir a` NO DEBE ejecutarse como acción al reproducir con
  `--replay`: la reproducción ejecuta los movimientos individuales grabados.
- **FR-045**: El pergamino de retroceso DEBE revertir únicamente el último paso del viaje, porque
  cada paso es una acción del jugador, y el viaje NO DEBE continuar después de la reversión.

**Persistencia, reversión y determinismo**

- **FR-046**: Guardar y cargar una partida DEBE conservar el mapa conocido completo: el estado de
  cada sala y el estado recordado de cada puerta, incluidas las salas avistadas y las exploradas sin
  contenido incorporado.
- **FR-047**: Un archivo de partida de un formato anterior DEBE detectarse como incompatible
  mediante la validación de versión del formato, y NO DEBE cargarse en silencio.
- **FR-048**: Toda modificación del mapa conocido DEBE poder revertirse como parte de la acción del
  jugador que la provocó, junto con el resto de los cambios de esa acción.
- **FR-049**: La misma cripta, la misma semilla y la misma secuencia de acciones DEBEN producir el
  mismo mapa conocido y las mismas rutas de `ir a`, también al reproducir con `--replay`.

**Rendimiento y medición**

- **FR-050**: Consultar el estado de una sala y el estado recordado de una puerta DEBEN costar
  tiempo constante, independiente de cuántas salas estén exploradas.
- **FR-051**: Explorar salas nuevas DEBE costar proporcionalmente a las salas reveladas y a sus
  vecinas inmediatas, no al tamaño del mapa ya conocido.
- **FR-052**: Registrar e invertir un cambio del mapa conocido DEBE costar proporcionalmente a lo
  que cambió, no al tamaño del mapa.
- **FR-053**: El cálculo de un paso de `ir a` DEBE tomar menos de 5 ms con el mapa conocido completo
  de la cripta de referencia, sin red ni renderizado.
- **FR-054**: Toda estructura auxiliar que el mapa conocido o el cálculo de la ruta necesiten DEBE
  cumplir el Principio I de la constitución: la implementa el grupo, y está PROHIBIDO usar `dict`,
  `set`, `heapq`, `bisect`, `collections`, bibliotecas de grafos o estructuras equivalentes de
  biblioteca como índice, caché o registro.
- **FR-055**: `--bench` DEBE medir las consultas al mapa conocido y el cálculo de un paso de `ir a`,
  y DEBE comparar el costo de explorar salas nuevas con un mapa conocido pequeño y con uno grande.
- **FR-056**: Las criptas sintéticas de `--bench` DEBEN ser deterministas por semilla, y `--bench`
  NO DEBE instanciar la vista.

### Key Entities *(include if feature involves data)*

- **Estado de conocimiento de una sala**: explorada, avistada o desconocida, desde el punto de vista
  del jugador. Es estado del juego.
- **Estado recordado de una puerta**: sin observar, recordada abierta o recordada cerrada. Es lo que
  el jugador anotó la última vez que vio esa puerta, no lo que ocurre ahora.
- **Mapa conocido**: el conjunto de estados de sala y de estados recordados de puertas, junto con el
  nombre, las salidas y los costos de las salas exploradas. Es lo único que la vista y `ir a` pueden
  mirar.
- **Observación**: el acto de fijar el estado recordado de las puertas de la sala donde el jugador
  está, al entrar a ella o al abrir una de sus puertas.
- **Viaje**: la ejecución de una orden `ir a`: una secuencia de pasos, cada uno una acción del
  jugador, con un destino y un motivo de detención. No es estado persistente de la partida.
- **Motivo de detención**: llegada al destino, enemigos en la sala, daño recibido, ruta conocida
  inexistente o fin de la partida.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Los 6 casos de «Niebla de guerra e ir a» del Apéndice B de P2 tienen una prueba
  automatizada que cita su requisito, y todas pasan.
- **SC-002**: En una partida sintética de al menos 1 000 acciones con antorchas, cierres automáticos
  y pergaminos, el mapa conocido coincide en todo instante con el que se obtiene recalculándolo
  desde el inicio a partir de la secuencia de acciones.
- **SC-003**: Con el mapa conocido completo de la cripta de referencia, ningún cálculo de un paso de
  `ir a` supera los 5 ms en el equipo local.
- **SC-004**: El número de salas que toca una exploración con antorcha que revela k vecinas es el
  mismo cuando el mapa ya conocido tiene 10 veces más salas exploradas. `--bench` reporta además los
  tiempos en ambos tamaños.
- **SC-005**: Para cada ruta que `ir a` calcula en al menos 10 000 cálculos sobre mapas conocidos
  sintéticos, el primer paso coincide con el de una referencia calculada desde cero sobre el
  subgrafo conocido.
- **SC-006**: Revertir con un pergamino una entrada con antorcha que exploró k salas deja el mapa
  conocido byte a byte igual al que había antes de esa entrada.
- **SC-007**: Guardar y cargar una partida con un mapa conocido parcial reproduce el mapa exacto, y
  un archivo del formato anterior se rechaza con un mensaje de incompatibilidad.
- **SC-008**: Dos reproducciones con `--replay` del mismo `partida.log` producen el mismo mapa
  conocido y la misma secuencia de salas visitadas.
- **SC-009**: Ningún módulo de la capacidad usa `dict`, `set`, `heapq`, `bisect`, `collections` ni
  bibliotecas de grafos, verificado por la prueba de restricciones.
- **SC-010**: Toda la batería de pruebas de las capacidades 001 y 002 sigue pasando.
